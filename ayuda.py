"""
ayuda.py - Cog para sistema de ayuda
Comandos: /helps, /ayuda, /comandos
"""
import discord
from discord.ext import commands

from utils import es_admin


class AyudaCog(commands.Cog):
    """Cog para mostrar comandos disponibles."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="helps", aliases=["ayuda", "comandos"])
    async def help_command(self, ctx):
        """Muestra la lista de comandos disponibles."""
        
        embed = discord.Embed(
            title="📚 Comandos de LigaHaxBot",
            description="Lista completa de comandos disponibles en el bot.",
            color=discord.Color.from_rgb(35, 35, 35)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Comandos Públicos / General
        general = """
        `/mi_equipo` - Ver tu equipo actual
        `/plantilla [Equipo]` - Ver jugadores y DT
        `/aglibre` - Registrarse como Agente Libre
        `!colores` - Ver colores disponibles (Prefix)
        """
        embed.add_field(name="⚽ General", value=general, inline=False)
        
        # Comandos para DTs
        dts = """
        `/fichar @Jugador` - Enviar oferta a jugador (Requiere Aceptar)
        `/despedir @Jugador` - Sacar jugador de la plantilla
        `/intercambio @MiJug @SuJug` - Iniciar trueque
        `/mi_rol [manager/jugador]` - manager (0 cupo) | jugador (1 cupo)
        `/renunciar` - Renunciar al cargo de DT
        """
        embed.add_field(name="👔 Directores Técnicos", value=dts, inline=False)
        
        # Comandos de Administración (Solo visible para admins)
        if es_admin(ctx.author):
            admin = """
            **Gestión**
            `/abrir_mercado [Equipo]` - Abrir globalmente o solo al equipo
            `/cerrar_mercado` - Bloquear fichajes
            `/crear "Nombre" Color` - Crear nuevo equipo
            `/dt @Usuario Equipo` - Asignar DT a un equipo
            
            **Mantenimiento**
            `/sincronizar` - Guardar roles manuales en BD
            `/info` - Ver Dashboard de Estadísticas
            `/bloquear_canal [block/unblock]` - Bloquear bot en canal
            `/backup` - Crear copia de seguridad
            `/reiniciar` - Reiniciar el bot
            `/resetear_bd` - ⚠️ Borrar toda la base de datos
            """
            embed.add_field(name="🛡️ Administración", value=admin, inline=False)
        
        embed.set_footer(text="Usa los comandos con responsabilidad. • Bot v3.0")
        
        if ctx.interaction:
            await ctx.reply(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AyudaCog(bot))
