"""
clasificacion.py - Cog para Tabla de Posiciones (solo lectura en Discord)
Comando: /tabla
La gestión (resultado, walkover, puntuación) se hace desde el Panel Web Admin.
"""
import discord
from discord.ext import commands
from datetime import datetime

from logger import get_module_logger
from database import get_tabla_posiciones, get_puntuacion_config

logger = get_module_logger("clasificacion")

# Medallas para el top 3
MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def formatear_tabla_discord(tabla: list, puntuacion: dict) -> str:
    """Genera tabla monospaced alineada para Discord."""
    if not tabla:
        return "```\n  Sin equipos registrados en la liga activa.\n```"

    max_nombre = max(len(e.get('equipo', '???')) for e in tabla)
    max_nombre = max(max_nombre, 6)
    max_nombre = min(max_nombre, 16)

    header = f"{'':>4} {'EQUIPO':<{max_nombre}} {'PJ':>3} {'DG':>4} {'PTS':>4}"
    sep = "━" * len(header)
    lineas = [sep, header, sep]

    for i, equipo in enumerate(tabla):
        pos = i + 1
        icono = MEDALLAS.get(pos, f"{pos:>2}.")
        nombre = equipo.get('equipo', '???')[:max_nombre]
        pj  = equipo.get('pj', 0)
        dg  = equipo.get('dif', 0)
        pts = equipo.get('pts', 0)
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        lineas.append(f"{icono:<4} {nombre:<{max_nombre}} {pj:>3} {dg_str:>4} {pts:>4}")

    lineas.append(sep)
    v = puntuacion['pts_victoria']
    e = puntuacion['pts_empate']
    d = puntuacion['pts_derrota']
    lineas.append(f"  V={v}pts  E={e}pts  D={d}pts")
    return "```\n" + "\n".join(lineas) + "\n```"


class ClasificacionCog(commands.Cog):
    """Cog de solo lectura: muestra la tabla de posiciones en Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tabla", description="Ver la tabla de posiciones de la liga")
    async def tabla(self, ctx):
        await ctx.defer()

        guild_id = str(ctx.guild.id)
        tabla = await get_tabla_posiciones(guild_id)
        puntuacion = await get_puntuacion_config(guild_id)

        lider = tabla[0].get('equipo', '') if tabla else ''
        pts_lider = tabla[0].get('pts', 0) if tabla else 0

        embed = discord.Embed(
            title="🏆  TABLA DE POSICIONES",
            description=formatear_tabla_discord(tabla, puntuacion),
            color=0xFFD700,
        )

        if tabla:
            embed.add_field(
                name="👑 Líder actual",
                value=f"**{lider}** — {pts_lider} pts",
                inline=True,
            )
            embed.add_field(
                name="⚽ Equipos",
                value=str(len(tabla)),
                inline=True,
            )
            # Equipo con más goles a favor
            top_gf = max(tabla, key=lambda x: x.get('gf', 0))
            embed.add_field(
                name="🎯 Más goleador",
                value=f"**{top_gf['equipo']}** ({top_gf.get('gf', 0)} GF)",
                inline=True,
            )

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.set_footer(
            text=f"AMAPICKS • Actualizado {datetime.now().strftime('%d/%m/%Y  %H:%M')}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ClasificacionCog(bot))
