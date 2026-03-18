"""
estadisticas.py - Cog para dashboard de estadísticas
Comandos: /info, /estadisticas, /dashboard
"""
import discord
from discord.ext import commands

import config
from database import get_db, get_collection, mercado_esta_abierto
from utils import es_admin


class EstadisticasCog(commands.Cog):
    """Cog para mostrar estadísticas y dashboard de la liga."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="info", aliases=["estadisticas", "dashboard", "estado"], description="Ver dashboard de la liga (Admin)")
    async def info(self, ctx):
        """Muestra un dashboard completo con el estado de la liga (Solo Admins)."""

        if not es_admin(ctx.author):
            await ctx.send("❌ Solo administradores pueden ver el dashboard.")
            return

        async with ctx.typing():
            jugadores_col = get_collection('jugadores')
            agentes_col = get_collection('agentes_libres')

            # Conteos async
            total_jugadores = await jugadores_col.count_documents({})
            total_agentes_libres = await agentes_col.count_documents({})

            # Estado del mercado (async)
            estado_mercado = await mercado_esta_abierto()
            if estado_mercado is True:
                estado_mercado_texto = "🟢 Abierto Global"
            elif estado_mercado is False:
                estado_mercado_texto = "🔴 Cerrado"
            else:
                estado_mercado_texto = f"🟡 Abierto para {estado_mercado}"

            # Análisis de Equipos (async cursor)
            equipos_stats = {}
            cursor = jugadores_col.find({})
            jugadores_totales = await cursor.to_list(length=500)
            for j in jugadores_totales:
                eq = j.get('equipo', 'Desconocido')
                equipos_stats[eq] = equipos_stats.get(eq, 0) + 1

            todos_equipos = getattr(self.bot, 'roles_equipos', [])

            equipos_llenos = []
            equipos_vacios = []
            equipos_peligro = []

            for eq in todos_equipos:
                count = equipos_stats.get(eq, 0)
                if count >= config.LIMITE_PLANTILLA:
                    equipos_llenos.append(eq)
                elif count == 0:
                    equipos_vacios.append(eq)
                elif count < 5:
                    equipos_peligro.append(f"{eq} ({count})")

            # Análisis de DTs
            dts_count = 0
            equipos_sin_dt = []

            rol_dt_obj = discord.utils.get(ctx.guild.roles, name=config.ROL_DE_DT)

            if rol_dt_obj:
                dts_count = len(rol_dt_obj.members)

                for eq_name in todos_equipos:
                    rol_eq = discord.utils.get(ctx.guild.roles, name=eq_name)
                    if not rol_eq:
                        continue

                    tiene_dt = False
                    for member in rol_eq.members:
                        if rol_dt_obj in member.roles:
                            tiene_dt = True
                            break
                    if not tiene_dt:
                        equipos_sin_dt.append(eq_name)

            # EMBED
            embed = discord.Embed(
                title="📊 DASHBOARD DE LA LIGA",
                description=f"Estado del Mercado: **{estado_mercado_texto}**",
                color=discord.Color.blue()
            )

            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            poblacion = (
                f"**{total_jugadores}** Jugadores Fichados\n"
                f"**{total_agentes_libres}** Agentes Libres\n"
                f"**{dts_count}** Directores Técnicos"
            )
            embed.add_field(name="👥 Población", value=poblacion, inline=True)

            balance = (
                f"**{len(equipos_llenos)}** Equipos Llenos ({config.LIMITE_PLANTILLA}/{config.LIMITE_PLANTILLA})\n"
                f"**{len(equipos_vacios)}** Equipos Vacíos\n"
                f"**{len(todos_equipos)}** Equipos Totales"
            )
            embed.add_field(name="⚖️ Balance", value=balance, inline=True)

            alertas = ""
            if equipos_sin_dt:
                lista = ", ".join(equipos_sin_dt[:5])
                alertas += f"⚠️ **Sin DT:** {lista}\n"
            if equipos_peligro:
                lista = ", ".join(equipos_peligro[:5])
                alertas += f"⚠️ **Pocos Jugadores:** {lista}\n"

            if not alertas:
                alertas = "✅ Todo en orden."
            embed.add_field(name="🚨 Alertas", value=alertas, inline=False)

            if equipos_stats:
                sorted_equipos = sorted(equipos_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                top_text = "\n".join([f"• **{k}**: {v}/{config.LIMITE_PLANTILLA}" for k, v in sorted_equipos])
                embed.add_field(name="🏆 Top Fichajes", value=top_text, inline=False)

            embed.set_footer(text=f"Solicitado por {ctx.author.display_name} • Bot v3.0")

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EstadisticasCog(bot))
