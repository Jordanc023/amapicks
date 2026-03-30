"""
mercado.py - Cog para gestión del mercado de fichajes
Comandos: /abrir_mercado, /cerrar_mercado
"""
import discord
from logger import get_module_logger

logger = get_module_logger("mercado")
from discord.ext import commands
from datetime import datetime

from utils import check_es_admin, buscar_equipo, get_bot_config
from database import (
    get_collection, abrir_mercado, cerrar_mercado,
    mercado_esta_abierto, contar_jugadores_equipo
)

class MercadoCog(commands.Cog):
    """Cog para gestionar la apertura/cierre del mercado."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="abrir_mercado", description="Abrir el mercado de fichajes (Admin)")
    @check_es_admin()
    async def cmd_abrir_mercado(self, ctx):
        """Abre el mercado globalmente."""
        await ctx.defer()

        await abrir_mercado('true')

        cfg = await get_bot_config()
        rol_dt = discord.utils.get(ctx.guild.roles, name=cfg["rol_dt"])
        mencion = rol_dt.mention if rol_dt else ""

        # Estadísticas
        agentes_col = get_collection('agentes_libres')
        jugadores_col = get_collection('jugadores')

        agentes = await agentes_col.find({}).to_list(length=200)
        total_agentes = len(agentes)
        pos_counts = {'GK': 0, 'DEF': 0, 'MC': 0, 'DC': 0}
        for ag in agentes:
            pos = ag.get('posicion', '?')
            if pos in pos_counts:
                pos_counts[pos] += 1

        equipos_con_cupo = 0
        for equipo in self.bot.roles_equipos:
            count = await contar_jugadores_equipo(equipo)
            if count < cfg["limite_plantilla"]:
                equipos_con_cupo += 1

        total_fichajes = await jugadores_col.count_documents({})

        descripcion = f"El mercado de fichajes ha sido **HABILITADO**.\nLos {mencion} ya pueden realizar movimientos."

        embed = discord.Embed(
            description=descripcion,
            color=discord.Color.from_rgb(46, 204, 113)
        )
        embed.set_author(name="🟢 MERCADO ABIERTO", icon_url="https://i.imgur.com/8pA1d9D.png")

        stats_agentes = (
            f"🧤 GK: **{pos_counts['GK']}** • 🛡️ DEF: **{pos_counts['DEF']}**\n"
            f"⚙️ MC: **{pos_counts['MC']}** • ⚔️ DC: **{pos_counts['DC']}**"
        )
        embed.add_field(name=f"📋 Agentes Libres ({total_agentes})", value=stats_agentes, inline=False)
        embed.add_field(name="⚽ Equipos con Cupos",
                        value=f"**{equipos_con_cupo}** de **{len(self.bot.roles_equipos)}** equipos", inline=True)
        embed.add_field(name="📝 Fichajes Temporada", value=f"**{total_fichajes}** jugadores", inline=True)

        embed.set_footer(text=f"Autorizado por {ctx.author.display_name}")
        embed.timestamp = datetime.now()

        await ctx.send(content=mencion, embed=embed)
        logger.info(f"🟢 Mercado abierto (global) por {ctx.author.name}")

    @commands.hybrid_command(name="cerrar_mercado", description="Cerrar el mercado de fichajes (Admin)")
    @check_es_admin()
    async def cmd_cerrar_mercado(self, ctx):
        """Cierra el mercado de fichajes."""
        await ctx.defer()

        await cerrar_mercado()

        cfg = await get_bot_config()
        rol_dt = discord.utils.get(ctx.guild.roles, name=cfg["rol_dt"])
        mencion = rol_dt.mention if rol_dt else ""

        agentes_col = get_collection('agentes_libres')
        jugadores_col = get_collection('jugadores')

        total_agentes = await agentes_col.count_documents({})
        total_fichajes = await jugadores_col.count_documents({})
        total_equipos = len(self.bot.roles_equipos)

        embed = discord.Embed(
            description="El mercado de fichajes ha sido **CERRADO**.\nNo se permiten más movimientos por ahora.",
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.set_author(name="🔴 MERCADO CERRADO", icon_url="https://i.imgur.com/M612a4E.png")
        embed.add_field(
            name="📊 Resumen",
            value=f"👥 **{total_agentes}** agentes libres\n⚽ **{total_equipos}** equipos\n📝 **{total_fichajes}** fichajes totales",
            inline=False
        )
        embed.set_footer(text=f"Cerrado por {ctx.author.display_name}")
        embed.timestamp = datetime.now()

        await ctx.send(content=mencion, embed=embed)
        logger.info(f"🔴 Mercado cerrado por {ctx.author.name}")


async def setup(bot):
    await bot.add_cog(MercadoCog(bot))
