"""
clasificacion.py - Cog para Tabla de Posiciones (solo lectura en Discord)
Comando: /tabla
La gestión (resultado, walkover, puntuación) se hace desde el Panel Web Admin.
"""
import discord
from discord.ext import commands
from datetime import datetime

from logger import get_module_logger
from database import get_tabla_posiciones, get_puntuacion_config, get_collection

logger = get_module_logger("clasificacion")

# Medallas para el top 3
MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def formatear_tabla_resto(tabla: list, puntuacion: dict) -> str:
    """Genera tabla monospaced solo para posiciones 4 en adelante."""
    if len(tabla) <= 3:
        return ""
    
    resto = tabla[3:]  # Desde el 4to lugar
    
    max_nombre = max(len(e.get('equipo', '???')) for e in resto)
    max_nombre = max(max_nombre, 6)
    max_nombre = min(max_nombre, 16)

    header = f"{'POS':>4} {'EQUIPO':<{max_nombre}} {'PJ':>3} {'DG':>4} {'PTS':>4}"
    sep = "─" * len(header)
    lineas = [sep, header, sep]

    for i, equipo in enumerate(resto, start=4):
        nombre = equipo.get('equipo', '???')[:max_nombre]
        pj  = equipo.get('pj', 0)
        dg  = equipo.get('dif', 0)
        pts = equipo.get('pts', 0)
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        lineas.append(f"{i:>3}. {nombre:<{max_nombre}} {pj:>3} {dg_str:>4} {pts:>4}")

    lineas.append(sep)
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

        if not tabla:
            embed = discord.Embed(
                title="🏆  TABLA DE POSICIONES",
                description="```\n  Sin equipos registrados en la liga activa.\n```",
                color=0xFFD700,
            )
            await ctx.followup.send(embed=embed)
            return

        # Obtener color del líder desde BD
        lider = tabla[0]
        equipos_col = get_collection('equipos')
        equipo_lider_db = await equipos_col.find_one({'nombre': lider.get('equipo', '')})
        
        color_embed = 0xFFD700  # Dorado por defecto
        escudo_lider = None
        if equipo_lider_db:
            color_hex = equipo_lider_db.get('color', '#FFD700')
            try:
                color_embed = int(color_hex.lstrip('#'), 16)
            except ValueError:
                color_embed = 0xFFD700
            escudo_lider = equipo_lider_db.get('escudo_url')

        # Calcular stats extra
        top_victorias = max(tabla, key=lambda x: x.get('pg', 0))
        top_defensa = min(tabla, key=lambda x: x.get('gc', 999))
        
        # ===== EMBED PRINCIPAL: TOP 3 =====
        embed_top = discord.Embed(
            title="🏆 TABLA DE POSICIONES",
            color=color_embed,
            timestamp=datetime.now()
        )
        
        if ctx.guild.icon:
            embed_top.set_author(name=f"Liga {ctx.guild.name}", icon_url=ctx.guild.icon.url)
        
        if escudo_lider:
            embed_top.set_thumbnail(url=escudo_lider)

        # Mostrar Top 3 como fields grandes
        for i, equipo in enumerate(tabla[:3], 1):
            medalla = MEDALLAS.get(i, f"{i}.")
            nombre = equipo.get('equipo', '???')
            pj = equipo.get('pj', 0)
            pg = equipo.get('pg', 0)
            pe = equipo.get('pe', 0)
            pp = equipo.get('pp', 0)
            gf = equipo.get('gf', 0)
            gc = equipo.get('gc', 0)
            dg = equipo.get('dif', 0)
            pts = equipo.get('pts', 0)
            
            dg_str = f"+{dg}" if dg > 0 else str(dg)
            dg_emoji = "🟢" if dg > 0 else ("🔴" if dg < 0 else "⚪")
            
            value = (
                f"**{pts} pts** — {pj} PJ\n"
                f"```diff\n"
                f"+ {pg}G {pe}E {pp}P\n"
                f"  {gf}GF {gc}GC ({dg_str})\n"
                f"```"
            )
            
            embed_top.add_field(
                name=f"{medalla} {nombre}",
                value=value,
                inline=True
            )

        # Stats extra
        v = puntuacion['pts_victoria']
        e = puntuacion['pts_empate']
        d = puntuacion['pts_derrota']
        
        stats_text = (
            f"🔥 **Más victorias:** {top_victorias['equipo']} ({top_victorias.get('pg', 0)}G)\n"
            f"🛡️ **Mejor defensa:** {top_defensa['equipo']} ({top_defensa.get('gc', 0)}GC)\n"
            f"📋 **Sistema:** V={v}pts • E={e}pts • D={d}pts"
        )
        embed_top.add_field(name="📊 Estadísticas", value=stats_text, inline=False)

        # Si hay más de 3 equipos, agregar tabla del resto
        if len(tabla) > 3:
            resto_tabla = formatear_tabla_resto(tabla, puntuacion)
            embed_top.add_field(
                name=f"📈 Resto de la Clasificación ({len(tabla)-3} equipos)",
                value=resto_tabla,
                inline=False
            )

        embed_top.set_footer(
            text=f"AMAPICKS • {len(tabla)} equipos en competición",
            icon_url=ctx.author.display_avatar.url,
        )
        
        await ctx.followup.send(embed=embed_top)


async def setup(bot):
    await bot.add_cog(ClasificacionCog(bot))
