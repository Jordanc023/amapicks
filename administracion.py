"""
administracion.py - Cog para administración avanzada del bot
Comandos: /auditoria, /nueva_temporada, /temporadas, /config, /restaurar, /backup_manual
           /iniciar_temporada
Incluye backup automático programado
"""
import asyncio
import discord
from logger import get_module_logger

logger = get_module_logger("administracion")
import json
import os
from datetime import datetime
from discord.ext import commands, tasks
from discord.ui import View, Button, Select

from config import (
    AuditAction, CANAL_AGENTES_LIBRES_ID, CANAL_BACKUPS_ID, CANAL_LOGS_ID,
    BACKUP_INTERVAL_HOURS, DEFAULT_SERVER_CONFIG
)
from database import (
    get_db, get_collection, log_action,
    get_server_config, update_server_config,
    get_current_season
)
from utils import es_admin, check_es_admin





class AdministracionCog(commands.Cog):
    """Cog para comandos de administración avanzada."""

    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start()

    def cog_unload(self):
        self.auto_backup.cancel()



    # ============================================
    # BACKUP AUTOMÁTICO
    # ============================================

    @tasks.loop(hours=BACKUP_INTERVAL_HOURS)
    async def auto_backup(self):
        """Tarea de backup automático (async)."""
        logger.info("💾 Iniciando backup automático...")

        for guild in self.bot.guilds:
            config = await get_server_config(str(guild.id))

            if not config.get('backup_automatico', True):
                continue

            canal_id = config.get('canal_backups_id', CANAL_BACKUPS_ID)
            canal = guild.get_channel(int(canal_id)) if canal_id else None

            if not canal:
                logger.warning(f"⚠️ No se encontró canal de backups en {guild.name}")
                continue

            try:
                await self._crear_y_enviar_backup(guild, canal, "Sistema (Automático)")
                logger.info(f"✅ Backup automático completado para {guild.name}")
            except Exception as e:
                logger.error(f"❌ Error en backup automático de {guild.name}: {e}", exc_info=True)

    @auto_backup.before_loop
    async def before_auto_backup(self):
        await self.bot.wait_until_ready()

    async def _crear_y_enviar_backup(self, guild, canal, autor_nombre):
        """Crea y envía un backup a un canal (async)."""
        fecha_hora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_nombre = f'backup_{guild.id}_{fecha_hora}.json'

        database = get_db()

        # Consultas async para obtener datos
        jugadores_cursor = database.jugadores.find({}, {'_id': 0})
        jugadores_data = await jugadores_cursor.to_list(length=1000)

        equipos_cursor = database.equipos.find({}, {'_id': 0})
        equipos_data = await equipos_cursor.to_list(length=100)

        config_cursor = database.configuracion.find({}, {'_id': 0})
        config_data = await config_cursor.to_list(length=100)

        agentes_cursor = database.agentes_libres.find({}, {'_id': 0})
        agentes_data = await agentes_cursor.to_list(length=500)

        server_config = await get_server_config(str(guild.id))
        temporada_actual = await get_current_season(str(guild.id))

        backup_data = {
            'guild_id': str(guild.id),
            'guild_name': guild.name,
            'fecha_backup': fecha_hora,
            'jugadores': jugadores_data,
            'equipos': equipos_data,
            'configuracion': config_data,
            'agentes_libres': agentes_data,
            'server_config': server_config,
            'temporada_actual': temporada_actual
        }

        # Limpiar _id
        if '_id' in backup_data['server_config']:
            del backup_data['server_config']['_id']
        if '_id' in backup_data['temporada_actual']:
            del backup_data['temporada_actual']['_id']

        with open(backup_nombre, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

        archivo = discord.File(backup_nombre, filename=backup_nombre)

        embed = discord.Embed(
            title="💾 Backup Automático",
            description=f"Backup creado exitosamente.\n**Archivo:** `{backup_nombre}`",
            color=discord.Color.blue()
        )
        embed.add_field(name="📅 Fecha", value=datetime.now().strftime('%d/%m/%Y %H:%M'), inline=True)
        embed.add_field(name="👥 Jugadores", value=str(len(backup_data['jugadores'])), inline=True)
        embed.add_field(name="⚽ Equipos", value=str(len(backup_data['equipos'])), inline=True)
        embed.set_footer(text=f"Generado por: {autor_nombre}")

        await canal.send(embed=embed, file=archivo)

        await log_action(
            guild_id=str(guild.id),
            action_type=AuditAction.BACKUP_CREADO,
            actor_id="0",
            actor_name=autor_nombre,
            details={'archivo': backup_nombre, 'jugadores': len(backup_data['jugadores'])}
        )

        if os.path.exists(backup_nombre):
            os.remove(backup_nombre)

    # ============================================
    # RESTAURAR BACKUP
    # ============================================

    @commands.hybrid_command(name="restaurar", description="Restaurar backup desde archivo JSON (Admin)")
    @check_es_admin()
    async def restaurar(self, ctx):
        """Restaura un backup desde un archivo JSON adjunto."""
        if not ctx.message.attachments:
            await ctx.send("❌ Debes adjuntar un archivo `.json` de backup.\n"
                          "Usa: Adjunta el archivo y escribe `/restaurar`")
            return

        attachment = ctx.message.attachments[0]

        if not attachment.filename.endswith('.json'):
            await ctx.send("❌ El archivo debe ser `.json`")
            return

        embed = discord.Embed(
            title="⚠️ CONFIRMAR RESTAURACIÓN",
            description=f"Estás a punto de restaurar:\n**{attachment.filename}**\n\n"
                        f"⚠️ Esto **SOBRESCRIBIRÁ** todos los datos actuales.\n\n"
                        f"Escribe `CONFIRMAR` en los próximos 30 segundos.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == 'CONFIRMAR'

        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("❌ Operación cancelada. No se escribió CONFIRMAR.")
            return

        try:
            contenido = await attachment.read()
            backup_data = json.loads(contenido.decode('utf-8'))
        except json.JSONDecodeError:
            await ctx.send("❌ El archivo no es un JSON válido.")
            return
        except Exception as e:
            await ctx.send(f"❌ Error al leer el archivo: {e}")
            return

        try:
            database = get_db()

            # Limpiar colecciones actuales (async)
            await database.jugadores.delete_many({})
            await database.equipos.delete_many({})
            await database.agentes_libres.delete_many({})

            # Insertar datos del backup (async)
            if backup_data.get('jugadores'):
                await database.jugadores.insert_many(backup_data['jugadores'])
            if backup_data.get('equipos'):
                await database.equipos.insert_many(backup_data['equipos'])
            if backup_data.get('agentes_libres'):
                await database.agentes_libres.insert_many(backup_data['agentes_libres'])

            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=AuditAction.BACKUP_RESTAURADO,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                details={
                    'archivo': attachment.filename,
                    'jugadores_restaurados': len(backup_data.get('jugadores', [])),
                    'equipos_restaurados': len(backup_data.get('equipos', []))
                }
            )

            # Recargar equipos en memoria (async)
            if hasattr(self.bot, 'cargar_equipos'):
                await self.bot.cargar_equipos()

            embed = discord.Embed(
                title="✅ BACKUP RESTAURADO",
                description=f"Se han restaurado los datos desde `{attachment.filename}`",
                color=discord.Color.green()
            )
            embed.add_field(name="👥 Jugadores", value=str(len(backup_data.get('jugadores', []))), inline=True)
            embed.add_field(name="⚽ Equipos", value=str(len(backup_data.get('equipos', []))), inline=True)
            embed.set_footer(text=f"Restaurado por {ctx.author.display_name}")

            await ctx.send(embed=embed)
            logger.info(f"✅ Backup restaurado por {ctx.author.name}: {attachment.filename}")

        except Exception as e:
            await ctx.send(f"❌ Error al restaurar: {e}")
            logger.error(f"Error en restauración: {e}", exc_info=True)

    @commands.hybrid_command(name="backup_manual", description="Crear un backup manual ahora (Admin)")
    @check_es_admin()
    async def backup_manual(self, ctx):
        """Crea un backup manual inmediato."""
        config = await get_server_config(str(ctx.guild.id))
        canal_id = config.get('canal_backups_id', CANAL_BACKUPS_ID)
        canal = ctx.guild.get_channel(int(canal_id)) if canal_id else None

        if not canal:
            canal = ctx.channel

        await ctx.send("💾 Creando backup manual...")

        try:
            await self._crear_y_enviar_backup(ctx.guild, canal, ctx.author.display_name)
            await ctx.send(f"✅ Backup enviado a {canal.mention}")
        except Exception as e:
            await ctx.send(f"❌ Error al crear backup: {e}")
            logger.error(f"Error en backup_manual: {e}", exc_info=True)

    @commands.hybrid_command(name="sync_old", description="Sincronizar comandos de barra en el servidor actual (legacy)")
    @check_es_admin()
    async def sync_old(self, ctx):
        """Sincroniza los comandos de barra con el servidor actual."""
        await ctx.send("🔄 Sincronizando comandos de barra...")
        try:
            # Sincronizar solo al servidor actual para rapidez
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"✅ Se han sincronizado {len(synced)} comandos en este servidor.")
            logger.info(f"✅ Sincronización manual en {ctx.guild.name}: {len(synced)} comandos.")
        except Exception as e:
            await ctx.send(f"❌ Error al sincronizar: {e}")
            logger.error(f"Error en sync: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(AdministracionCog(bot))
