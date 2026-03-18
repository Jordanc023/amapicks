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


def formatear_tabla_discord(tabla: list, puntuacion: dict) -> str:
    """Genera tabla monospaced alineada para Discord."""
    if not tabla:
        return "```\n  La tabla de posiciones está vacía.\n  No se han registrado resultados aún.\n```"

    max_nombre = max(len(e.get('equipo', '???')) for e in tabla)
    max_nombre = max(max_nombre, 6)
    max_nombre = min(max_nombre, 18)

    header = f"{'#':>3} {'EQUIPO':<{max_nombre}} {'PJ':>3} {'PG':>3} {'PE':>3} {'PP':>3} {'GF':>3} {'GC':>3} {'DG':>4} {'PTS':>4}"
    separador = "─" * len(header)
    lineas = [separador, header, separador]

    for i, equipo in enumerate(tabla):
        pos = i + 1
        nombre = equipo.get('equipo', '???')[:max_nombre]
        pj = equipo.get('pj', 0)
        pg = equipo.get('pg', 0)
        pe = equipo.get('pe', 0)
        pp = equipo.get('pp', 0)
        gf = equipo.get('gf', 0)
        gc = equipo.get('gc', 0)
        dg = equipo.get('dif', 0)
        pts = equipo.get('pts', 0)
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        lineas.append(f"{pos:>3} {nombre:<{max_nombre}} {pj:>3} {pg:>3} {pe:>3} {pp:>3} {gf:>3} {gc:>3} {dg_str:>4} {pts:>4}")

    lineas.append(separador)
    v = puntuacion['pts_victoria']
    e = puntuacion['pts_empate']
    d = puntuacion['pts_derrota']
    lineas.append(f" V={v}pts | E={e}pts | D={d}pts")
    return "```\n" + "\n".join(lineas) + "\n```"


class ClasificacionCog(commands.Cog):
    """Cog de solo lectura: muestra la tabla de posiciones en Discord."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tabla", description="Ver la tabla de posiciones de la liga")
    async def tabla(self, ctx):
        """Muestra la tabla de posiciones actual con formato profesional."""
        await ctx.defer()

        guild_id = str(ctx.guild.id)
        tabla = await get_tabla_posiciones(guild_id)
        puntuacion = await get_puntuacion_config(guild_id)
        tabla_texto = formatear_tabla_discord(tabla, puntuacion)

        embed = discord.Embed(
            title="🏆 TABLA DE POSICIONES",
            description=tabla_texto,
            color=discord.Color.gold()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(
            text=f"Actualizado • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ClasificacionCog(bot))
