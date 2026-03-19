import discord
import os
import sys
from datetime import datetime
from discord.ext import commands, tasks

# Importar configuración centralizada
from config import (
    TOKEN, ROL_DE_DT, ROLES_ADMIN,
    AUTO_SYNC_INTERVAL_HOURS, CANAL_OFERTAS_ID
)
from database import get_collection, init_db
from logger import log, get_module_logger
from utils import es_admin

logger = get_module_logger("main")


class LigaBot(commands.Bot):
    """Bot principal para gestionar la Liga de Haxball."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.roles_equipos = []
        self.uptime_start = datetime.now()

    async def setup_hook(self):
        """Hook de configuración antes de conectar."""
        logger.info("🔄 Iniciando carga de extensiones...")

        # Cargar extensiones (Cogs)
        extensiones = [
            'equipos', 'directores', 'ayuda', 'fichajes',
            'estadisticas', 'administracion',
            'partidos', 'mercado', 'jugadores', 'clasificacion'
        ]
        for ext in extensiones:
            try:
                await self.load_extension(ext)
                logger.info(f"✅ Extensión '{ext}' cargada.")
            except Exception as e:
                logger.error(f"❌ Error al cargar extensión {ext}: {e}", exc_info=True)

        # Sincronizar Slash Commands
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Sincronizados {len(synced)} comandos de barra.")
        except Exception as e:
            logger.error(f"❌ Error al sincronizar árbol de comandos: {e}", exc_info=True)

    async def cargar_equipos(self):
        """
        Carga la lista de equipos detectando roles que empiecen con '-'.
        Sincroniza con MongoDB (async).
        """
        try:
            self.roles_equipos = []
            equipos_col = get_collection('equipos')

            for guild in self.guilds:
                for rol in guild.roles:
                    if rol.name.startswith('-'):
                        nombre_equipo = rol.name
                        if nombre_equipo not in self.roles_equipos:
                            self.roles_equipos.append(nombre_equipo)

            # Sincronizar con MongoDB
            for equipo in self.roles_equipos:
                await equipos_col.update_one(
                    {'nombre': equipo},
                    {'$set': {'nombre': equipo, 'detectado': datetime.now()}},
                    upsert=True
                )

            logger.info(f"📊 {len(self.roles_equipos)} equipos detectados (con prefijo '-').")
            if self.roles_equipos:
                preview = ', '.join(self.roles_equipos[:5])
                suffix = '...' if len(self.roles_equipos) > 5 else ''
                logger.debug(f"   Equipos: {preview}{suffix}")

        except Exception as e:
            logger.error(f"❌ Error al cargar equipos: {e}", exc_info=True)
            self.roles_equipos = []

    async def on_command_error(self, ctx, error):
        """Manejador global de errores de comandos."""
        if isinstance(error, commands.CommandNotFound):
            return
        if hasattr(ctx.command, 'on_error'):
            return

        logger.warning(f"⚠️ Error en comando '{ctx.command}': {error}")

        try:
            embed = discord.Embed(
                description=f"❌ **Error:** {error}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
        except discord.HTTPException:
            pass

    async def on_ready(self):
        """Evento cuando el bot está listo."""
        await init_db()
        logger.info(f'✅ {self.user} está en línea.')
        logger.info('📂 Base de datos lista.')

        # Cargar equipos desde Discord → MongoDB
        await self.cargar_equipos()

        # Sincronización inicial
        logger.info('🔄 Sincronizando base de datos al iniciar...')
        for guild in self.guilds:
            await self.perform_sync(guild)
        logger.info('✅ Sincronización inicial completada.')

        # Restaurar ofertas pendientes al reiniciar
        await self._restaurar_ofertas_pendientes()

        # Iniciar tarea periódica
        if not self.auto_sync_task.is_running():
            self.auto_sync_task.start()
        logger.info('🔄 Sincronización automática activada.')

        # Iniciar Heartbeat
        if not self.heartbeat_task.is_running():
            self.heartbeat_task.start()
        logger.info('💓 Heartbeat del bot activado para el Panel Web.')

        # Iniciar tarea de anuncios
        if not self.announcements_task.is_running():
            self.announcements_task.start()
        logger.info('📢 Tarea de Anuncios Globales activada (intervalo 15s).')

        # Iniciar tarea del Fundador de Clubes Híbrido
        if hasattr(self, 'fundador_task') and not self.fundador_task.is_running():
            self.fundador_task.start()
        logger.info('🏗️ Listener de Fundación de Clubes (Web) activado (intervalo 10s).')

    async def _restaurar_ofertas_pendientes(self):
        """
        Restaura ofertas pendientes de MongoDB al reiniciar el bot.
        Como las views de Discord no sobreviven al reinicio, se limpian
        las ofertas huérfanas y se notifica que expiraron.
        """
        try:
            ofertas_col = get_collection('ofertas_pendientes')
            ofertas = await ofertas_col.find({}).to_list(length=100)

            if not ofertas:
                logger.debug("📋 No hay ofertas pendientes que restaurar.")
                return

            expiradas = 0
            for oferta in ofertas:
                try:
                    dt_id = oferta.get('dt_id')
                    jugador_id = oferta.get('jugador_id')
                    equipo = oferta.get('equipo', 'Desconocido')

                    # Notificar al DT que la oferta expiró por reinicio
                    for guild in self.guilds:
                        dt_member = guild.get_member(int(dt_id)) if dt_id else None
                        if dt_member:
                            try:
                                embed = discord.Embed(
                                    title="⚠️ Oferta Expirada (Reinicio)",
                                    description=(
                                        f"Tu oferta de fichaje para <@{jugador_id}> "
                                        f"al equipo **{equipo}** fue cancelada porque "
                                        f"el bot se reinició.\n\n"
                                        f"Usa `/fichar` para enviar una nueva oferta."
                                    ),
                                    color=discord.Color.orange()
                                )
                                await dt_member.send(embed=embed)
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                            break

                    # Eliminar la oferta huérfana
                    await ofertas_col.delete_one({'_id': oferta['_id']})
                    expiradas += 1

                except Exception as e:
                    logger.warning(f"Error limpiando oferta individual: {e}")

            if expiradas > 0:
                logger.info(f"🧹 {expiradas} ofertas huérfanas limpiadas tras reinicio.")

        except Exception as e:
            logger.error(f"Error restaurando ofertas pendientes: {e}", exc_info=True)

    async def perform_sync(self, guild):
        """Sincroniza la BD con los roles del servidor (async optimizado)."""
        jugadores_col = get_collection('jugadores')

        # PASO 1: Limpieza — Obtener todos los registros
        eliminados_sv = 0
        eliminados_rol = 0

        cursor = jugadores_col.find({})
        jugadores_db = await cursor.to_list(length=500)

        # Pre-cargar todos los miembros del caché (no API calls)
        miembros_cache = {str(m.id): m for m in guild.members}

        for registro in jugadores_db:
            uid = registro['discord_id']
            equipo_db = registro.get('equipo')

            miembro = miembros_cache.get(uid)

            if not miembro:
                await jugadores_col.delete_one({'_id': registro['_id']})
                eliminados_sv += 1
                continue

            tiene_rol_equipo = any(r.name == equipo_db for r in miembro.roles)
            if not tiene_rol_equipo:
                await jugadores_col.delete_one({'_id': registro['_id']})
                eliminados_rol += 1

        # PASO 2: Captación — Registrar miembros con rol de equipo
        agregados = 0

        for miembro in guild.members:
            if miembro.bot:
                continue

            equipo_encontrado = None
            es_dt_rol = any(r.name == ROL_DE_DT for r in miembro.roles)

            for rol in miembro.roles:
                if rol.name in self.roles_equipos:
                    equipo_encontrado = rol.name
                    break

            if equipo_encontrado:
                try:
                    op_result = await jugadores_col.update_one(
                        {'discord_id': str(miembro.id)},
                        {
                            '$set': {
                                'discord_id': str(miembro.id),
                                'nombre': miembro.name,
                                'equipo': equipo_encontrado,
                                'avatar_url': str(miembro.display_avatar.url)
                            },
                            '$setOnInsert': {'es_dt': es_dt_rol}
                        },
                        upsert=True
                    )
                    if op_result.upserted_id:
                        agregados += 1
                except Exception as e:
                    logger.warning(f"Error sync {miembro.name}: {e}")

        logger.info(f"✅ Sync: -SV:{eliminados_sv} -Rol:{eliminados_rol} +Nuevos:{agregados}")

    @tasks.loop(hours=AUTO_SYNC_INTERVAL_HOURS)
    async def auto_sync_task(self):
        """Tarea periódica de sincronización."""
        logger.info("🔄 Sincronización automática...")
        for guild in self.guilds:
            await self.perform_sync(guild)
        logger.info("✅ Sincronización automática finalizada.")

    @auto_sync_task.before_loop
    async def before_auto_sync(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def heartbeat_task(self):
        """Envía una señal de vida, métricas a MongoDB y lee comandos remotos de la web."""
        try:
            status_col = get_collection('config_col')
            
            # 1. Enviar Heartbeat
            await status_col.update_one(
                {'_id': 'bot_status'},
                {'$set': {
                    'is_online': True,
                    'last_update': datetime.now(),
                    'uptime_start': self.uptime_start,
                    'latency_ms': round(self.latency * 1000)
                }},
                upsert=True
            )
            
            # 1.5 Refrescar Configuración Global en Memoria
            try:
                from utils import get_bot_config
                import config
                cfg = await get_bot_config()
                config.LIMITE_PLANTILLA = cfg.get("limite_plantilla", config.LIMITE_PLANTILLA)
                config.CANAL_FICHAJES = cfg.get("canal_fichajes", config.CANAL_FICHAJES)
                config.CANAL_AGENTES_LIBRES = cfg.get("canal_agentes", config.CANAL_AGENTES_LIBRES)
                config.ROL_DE_DT = cfg.get("rol_dt", config.ROL_DE_DT)
                config.ROL_AGENTE_LIBRE = cfg.get("rol_agente", config.ROL_AGENTE_LIBRE)
                config.CANAL_OFERTAS_ID = cfg.get("canal_ofertas_id", config.CANAL_OFERTAS_ID)
                config.DEFAULT_PUNTUACION = {
                    'pts_victoria': cfg.get("pts_victoria", 3),
                    'pts_empate': cfg.get("pts_empate", 1),
                    'pts_derrota': cfg.get("pts_derrota", 0),
                }
                config.WALKOVER_GOLES_FAVOR = cfg.get("walkover_gf", 3)
                config.WALKOVER_GOLES_CONTRA = cfg.get("walkover_gc", 0)
            except Exception as e_cfg:
                logger.error(f"Error actualizando la configuración viva en memoria: {e_cfg}")
            
            # 2. Leer comandos remotos pendientes
            command_doc = await status_col.find_one({'_id': 'bot_commands'})
            if command_doc and command_doc.get('force_sync'):
                logger.info("⚡ Comando remoto recibido: Forzando Sincronización de Slash Commands...")
                try:
                    synced = await self.tree.sync()
                    logger.info(f"✅ Sincronizados {len(synced)} comandos de barra remotamente.")
                except Exception as sync_e:
                    logger.error(f"❌ Error al sincronizar remotamente: {sync_e}")
                finally:
                    # Limpiar la bandera en la BD para no repetir el proceso
                    await status_col.update_one(
                        {'_id': 'bot_commands'},
                        {'$set': {'force_sync': False}}
                    )
        except Exception as e:
            logger.error(f"Error en heartbeat/comandos remotos: {e}")

    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.wait_until_ready()

    @tasks.loop(seconds=15)
    async def announcements_task(self):
        """Revisa la tabla de anuncios pendientes y los publica en el canal destino de cada servidor."""
        try:
            anuncios_col = get_collection("anuncios_pendientes")
            # Buscar anuncios no procesados
            anuncios = await anuncios_col.find({"procesado": {"$ne": True}}).to_list(length=10)
            
            if not anuncios:
                return
                
            for anuncio in anuncios:
                try:
                    titulo = anuncio.get("titulo", "Anuncio Oficial")
                    mensaje = anuncio.get("mensaje", "")
                    imagen_url = anuncio.get("imagen_url")
                    color_hex = anuncio.get("color", "#e74c3c").replace('#', '')
                    canal_nombre = anuncio.get("canal_destino", "anuncios").lower()
                    
                    color_int = int(color_hex, 16) if color_hex else discord.Color.red().value
                    
                    embed = discord.Embed(
                        title=f"🔔 {titulo}",
                        description=mensaje,
                        color=color_int,
                        timestamp=datetime.utcnow()
                    )
                    
                    if imagen_url:
                        embed.set_image(url=imagen_url)
                        
                    embed.set_footer(text="Administración de Liga", icon_url=self.user.display_avatar.url if self.user else None)
                    
                    # Enviar a todos los servidores en el canal que coincida (o contenga) el nombre
                    for guild in self.guilds:
                        canal_destino = None
                        # Convertimos a minúsculas y limpiamos emojis comunes al buscar si es necesario
                        for channel in guild.text_channels:
                            if canal_nombre in channel.name.lower():
                                canal_destino = channel
                                break
                                
                        if not canal_destino:
                            # Fallback: intentar enviarlo al primer canal general
                            for channel in guild.text_channels:
                                if "general" in channel.name.lower():
                                    canal_destino = channel
                                    break
                                    
                        if canal_destino:
                            try:
                                await canal_destino.send(embed=embed)
                                logger.info(f"📣 Anuncio '{titulo}' enviado a {guild.name} -> {canal_destino.name}")
                            except discord.Forbidden:
                                logger.warning(f"⚠️ No hay permisos para enviar el anuncio en {guild.name} -> {canal_destino.name}")
                                
                    # Marcar como procesado independientemente de si se envió con éxito o no a discord
                    await anuncios_col.update_one(
                        {"_id": anuncio["_id"]},
                        {"$set": {"procesado": True, "procesado_en": datetime.utcnow()}}
                    )
                    
                except Exception as ex_item:
                    logger.error(f"Error procesando el anuncio {anuncio.get('_id')}: {ex_item}")
                    
        except Exception as e:
            logger.error(f"Error en announcements_task: {e}")

    @announcements_task.before_loop
    async def before_announcements(self):
        await self.wait_until_ready()

    # ============================================
    # FUNDADOR DE CLUBES (HYBRID WEB-DISCORD)
    # ============================================
    @tasks.loop(seconds=10)
    async def fundador_task(self):
        """Revisa la BD iterando solicitudes de creación de clubes desde la Web."""
        try:
            pendientes_col = get_collection("clubes_pendientes_creacion")
            equipos_col = get_collection("equipos")
            jugadores_col = get_collection("jugadores")
            
            # Buscamos de 1 en 1 para evitar rate limits de Discord
            club_pendiente = await pendientes_col.find_one()
            if not club_pendiente:
                return

            guild_id = club_pendiente.get("guild_id")
            discord_id = club_pendiente.get("discord_id")
            nombre_crudo = club_pendiente.get("nombre", "Equipo").upper()
            nombre_equipo = nombre_crudo if nombre_crudo.startswith('-') else f"-{nombre_crudo}"
            color_hex = club_pendiente.get("color", "#3498db")
            logo_url = club_pendiente.get("logo_url", "")
            
            # Buscar el Guild (Servidor)
            guild = self.get_guild(int(guild_id)) if guild_id else (self.guilds[0] if self.guilds else None)
            if not guild:
                logger.error(f"❌ No se encontró servidor para crear el club {nombre_equipo}")
                await pendientes_col.delete_one({"_id": club_pendiente["_id"]})
                return
            
            logger.info(f"🌐 Servidor objetivo determinado: {guild.name} (ID: {guild.id})")

            # Verificar si el Rol ya existe (evitar duplicados de web rapidos)
            rol_equipo = discord.utils.get(guild.roles, name=nombre_equipo)
            
            if not rol_equipo:
                # 1. Crear el Rol en Discord
                color_limpio = color_hex.lstrip('#')
                color_int = int(color_limpio, 16) if color_limpio else 0x3498db
                color_discord = discord.Color(color_int)
                
                try:
                    rol_equipo = await guild.create_role(
                        name=nombre_equipo,
                        color=color_discord,
                        hoist=True,
                        mentionable=True,
                        reason=f"Fundación de Club Vía Web por <@{discord_id}>"
                    )
                except Exception as e:
                    logger.error(f"❌ Error API Discord creando rol {nombre_equipo}: {e}")
                    return # Intentará nuevamente el ciclo siguiente
            
            if nombre_equipo not in self.roles_equipos:
                self.roles_equipos.append(nombre_equipo)

            # 2. Asignar el Rol al DT (Dueño/Fundador)
            logger.info(f"⏳ Intentando localizar al DT (ID: {discord_id}) para darle su rol '{nombre_equipo}'...")
            miembro_dt = guild.get_member(int(discord_id))
            
            if not miembro_dt:
                import asyncio
                logger.warning(f"⚠️ DT {discord_id} no hallado en caché local. Iniciando fetch con backoff...")
                retries = 3
                for attempt in range(retries):
                    try:
                        miembro_dt = await guild.fetch_member(int(discord_id))
                        break
                    except discord.NotFound:
                        logger.error(f"❌ FETCH FALLIDO: El DT {discord_id} no está en {guild.name}.")
                        break
                    except discord.HTTPException as e:
                        if e.status == 429:
                            if attempt < retries - 1:
                                sleep_time = (2 ** attempt) + 1
                                logger.warning(f"⚠️ Rate limit detectado. Esperando {sleep_time}s antes de reintentar...")
                                await asyncio.sleep(sleep_time)
                            else:
                                logger.error(f"❌ Error de Rate Limit excedido haciendo fetch de {discord_id}: {e}")
                        else:
                            logger.error(f"❌ Error HTTP inesperado haciendo fetch de {discord_id}: {e}")
                            break
                    except Exception as ex_fetch:
                        logger.error(f"❌ Error inesperado haciendo fetch de {discord_id}: {ex_fetch}")
                        break

            if miembro_dt:
                logger.info(f"👤 DT {miembro_dt.name} encontrado. Procediendo a dar permisos...")
                try:
                    if rol_equipo not in miembro_dt.roles:
                        await miembro_dt.add_roles(rol_equipo)
                        logger.info(f"✅ Rol '{nombre_equipo}' asignado a {miembro_dt.name}")
                    else:
                        logger.info(f"ℹ️ El usuario {miembro_dt.name} ya tenía el rol '{nombre_equipo}'.")
                    
                    # 3. GESTIÓN DE LICENCIA Y ROL OFICIAL DE DT
                    from config import ROL_LICENCIA_ID, ROL_DT_OFICIAL_ID
                    
                    rol_licencia = guild.get_role(ROL_LICENCIA_ID)
                    if rol_licencia and rol_licencia in miembro_dt.roles:
                        await miembro_dt.remove_roles(rol_licencia)
                        logger.info(f"🎟️ Licencia fundacional (ID: {ROL_LICENCIA_ID}) retirada con éxito a {miembro_dt.name}.")
                        
                    rol_dt_oficial = guild.get_role(ROL_DT_OFICIAL_ID)
                    if rol_dt_oficial and rol_dt_oficial not in miembro_dt.roles:
                        await miembro_dt.add_roles(rol_dt_oficial)
                        logger.info(f"👔 Rol de DT Oficial (ID: {ROL_DT_OFICIAL_ID}) asignado con éxito a {miembro_dt.name}.")
                except discord.Forbidden:
                    logger.error(f"❌ PERMISOS DENEGADOS: El bot no tiene jerarquía para darle el rol '{nombre_equipo}' a {miembro_dt.name}. Asegúrese que el Rol del Bot esté arriba del todo.")
                except Exception as e:
                    logger.error(f"❌ Error desconocido asignando/quitando roles a {miembro_dt.name}: {e}")
            else:
                logger.error(f"🛑 ADVERTENCIA CRÍTICA: Se creará el club '{nombre_equipo}' en la BD, pero nadie quedó como dueño porque el DT no fue encontrado en el servidor.")

            # 3. Guardar el nuevo Club en la Colección Equipos Oficiales
            await equipos_col.update_one(
                {'nombre': nombre_equipo},
                {'$set': {
                    'nombre': nombre_equipo,
                    'rol_id': str(rol_equipo.id) if rol_equipo else None,
                    'creado_por': miembro_dt.name if miembro_dt else "Web Admin",
                    'creado_por_id': str(discord_id),
                    'escudo_url': logo_url,
                    'fecha': datetime.now(),
                    'presupuesto': 550000000, # Fondo inicial por defecto
                    'color': color_hex
                }},
                upsert=True
            )

            # 4. Actualizar ficha del DT en BD
            await jugadores_col.update_one(
                {'discord_id': str(discord_id)},
                {'$set': {'equipo': nombre_equipo}}
            )

            # 5. Borrar petición pendiente
            await pendientes_col.delete_one({"_id": club_pendiente["_id"]})
            logger.info(f"🏗️ Club '{nombre_equipo}' fundado y registrado correctamente (Automático).")

            # 6. Anunciar Nacimiento de Club
            canal_anuncios = discord.utils.get(guild.text_channels, name="anuncios")
            if not canal_anuncios:
                for channel in guild.text_channels:
                    if "general" in channel.name.lower():
                        canal_anuncios = channel
                        break
            
            if canal_anuncios:
                embed = discord.Embed(
                    title="🎉 ¡UN NUEVO CLUB NACE EN LA LIGA! 🎉",
                    description=f"Demos la bienvenida al **{nombre_equipo}**.\n\n"
                                f"Su Director Técnico y Fundador <@{discord_id}> acaba de abrir "
                                f"las instalaciones y está listo para fichar jugadores.",
                    color=rol_equipo.color if rol_equipo else discord.Color.gold()
                )
                if logo_url:
                    embed.set_thumbnail(url=logo_url)
                embed.set_footer(text="Aprobado por el Ministerio de AMAPICKS", icon_url=self.user.display_avatar.url)
                
                await canal_anuncios.send(embed=embed)

        except Exception as e:
            logger.error(f"Error crítico iterando fundador_task: {e}", exc_info=True)

    @fundador_task.before_loop
    async def before_fundador(self):
        await self.wait_until_ready()


bot = LigaBot()


# ============================================
# EVENTOS
# ============================================

@bot.event
async def on_message(message):
    """Procesa mensajes entrantes con filtros tempranos optimizados."""
    # Filtro temprano: ignorar bots y DMs
    if message.author.bot:
        return
    if not message.guild:
        return

    # Proteger canal de ofertas: solo comandos permitidos
    if message.channel.id == CANAL_OFERTAS_ID:
        if not es_admin(message.author):
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} Este canal es **solo para comandos**. "
                    f"Usa `/fichar`, `/despedir`, `/agentes`, etc.",
                    delete_after=5
                )
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

    await bot.process_commands(message)


# ============================================
# INICIAR BOT
# ============================================

if __name__ == "__main__":
    bot.run(TOKEN)