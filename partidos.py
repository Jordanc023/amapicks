"""
partidos.py - Cog para sistema de partidos y tabla de posiciones
Comandos: /partido, /partidos, /resultado, /tabla, /cancelar_partido
Incluye recordatorios automáticos 1 hora antes
"""
import discord
from logger import get_module_logger

logger = get_module_logger("partidos")
import re
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ui import View, Button

from config import ROL_DE_DT, AuditAction
from database import (
    get_collection, log_action,
    crear_partido, get_partidos_pendientes, get_partidos_proximos,
    marcar_partido_notificado, get_partido_by_id, registrar_resultado,
    get_tabla_posiciones, cancelar_partido, validar_resultado_dt
)
from utils import es_admin, check_es_admin, buscar_equipo





class PartidosCog(commands.Cog):
    """Cog para gestionar partidos y tabla de posiciones."""

    def __init__(self, bot):
        self.bot = bot
        self.recordatorios.start()

    def cog_unload(self):
        self.recordatorios.cancel()



    # ============================================
    # RECORDATORIOS AUTOMÁTICOS
    # ============================================

    @tasks.loop(minutes=5)
    async def recordatorios(self):
        """Revisa partidos próximos y notifica a los DTs (async)."""
        for guild in self.bot.guilds:
            partidos = await get_partidos_proximos(str(guild.id), minutos=65)

            for partido in partidos:
                try:
                    rol_local = discord.utils.get(guild.roles, name=partido['equipo_local'])
                    rol_visitante = discord.utils.get(guild.roles, name=partido['equipo_visitante'])

                    if not rol_local or not rol_visitante:
                        continue

                    canal = discord.utils.get(guild.text_channels, name='fichajes')
                    if not canal:
                        canal = guild.system_channel
                    if not canal:
                        continue

                    fecha = partido['fecha_hora'].strftime("%H:%M") if isinstance(partido['fecha_hora'], datetime) else partido['fecha_hora']

                    embed = discord.Embed(
                        title="⏰ RECORDATORIO DE PARTIDO",
                        description=f"**{partido['equipo_local']}** vs **{partido['equipo_visitante']}**\n\n"
                                   f"¡El partido comienza en **1 hora**!",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="🕐 Hora", value=fecha, inline=True)

                    menciones = ""
                    if rol_local:
                        menciones += rol_local.mention + " "
                    if rol_visitante:
                        menciones += rol_visitante.mention

                    await canal.send(content=menciones, embed=embed)

                    await marcar_partido_notificado(partido['_id'])
                    logger.info(f"🔔 Recordatorio enviado: {partido['equipo_local']} vs {partido['equipo_visitante']}")

                except Exception as e:
                    logger.error(f"Error en recordatorio: {e}", exc_info=True)

    @recordatorios.before_loop
    async def before_recordatorios(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(PartidosCog(bot))
