"""
equipos.py - Cog para gestión de equipos
Comandos: /crear, /colores
"""
import re
import discord
from logger import get_module_logger

logger = get_module_logger("equipos")
from discord.ext import commands
from datetime import datetime

from config import COLORES_EQUIPOS
from database import get_collection
from utils import es_admin


class EquiposCog(commands.Cog):
    """Cog para gestionar equipos (crear, colores, etc.)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="colores", description="Ver colores disponibles para crear equipos")
    async def ver_colores(self, ctx):
        """Muestra la lista de colores disponibles para equipos."""
        embed = discord.Embed(title="🎨 Colores Disponibles", color=discord.Color.gold())
        descripcion = "Usa estos nombres con `/crear Nombre Equipo Color`\n\n"

        for nombre, codigo in COLORES_EQUIPOS.items():
            descripcion += f"**{nombre.capitalize()}**: `{codigo}`\n"

        embed.description = descripcion
        embed.set_footer(text="También puedes usar códigos HEX como #FF0000")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="crear", description="Crear un nuevo equipo (Admin)")
    async def crear_equipo(self, ctx, *, entrada: str):
        """
        Crea un nuevo equipo.
        Uso: /crear Nombre del Equipo Color
        Ejemplo: /crear Manchester Rojo
        """
        await ctx.defer()

        # 1. Verificar permisos
        if not es_admin(ctx.author):
            await ctx.send("❌ No tienes permisos para crear equipos.")
            return

        # 2. Parseo inteligente (Separar nombre y color)
        partes = entrada.split()
        color_hex = "#3498db"
        nombre = entrada

        ultima_palabra = partes[-1].lower()

        if ultima_palabra in COLORES_EQUIPOS:
            color_hex = COLORES_EQUIPOS[ultima_palabra]
            nombre = " ".join(partes[:-1])
        elif len(ultima_palabra) in [6, 7]:
            match = re.search(r'^#?([A-Fa-f0-9]{6})$', ultima_palabra)
            if match:
                color_hex = "#" + match.group(1)
                nombre = " ".join(partes[:-1])

        if not nombre.strip():
            await ctx.send("⚠️ Debes escribir el nombre del equipo.\nEjemplo: `/crear Manchester Rojo`")
            return

        # 3. Verificar si ya existe
        equipos_col = get_collection('equipos')

        if nombre in self.bot.roles_equipos:
            await ctx.send(f"⚠️ El equipo **{nombre}** ya existe en la base de datos.")
            return

        # 4. Verificar si el rol ya existe en Discord
        rol_existente = discord.utils.get(ctx.guild.roles, name=nombre)
        if rol_existente:
            await ctx.send(f"⚠️ Ya existe un rol llamado **{nombre}** en el servidor. Lo registraré en la BD.")

            await equipos_col.update_one(
                {'nombre': nombre},
                {'$set': {'nombre': nombre, 'creado_por': ctx.author.name}},
                upsert=True
            )
            self.bot.roles_equipos.append(nombre)
            await ctx.send(f"✅ Equipo **{nombre}** registrado correctamente.")
            return

        try:
            # 5. Crear el Rol en Discord
            color_limpio = color_hex.lstrip('#')
            color_int = int(color_limpio, 16)
            color_discord = discord.Color(color_int)

            nuevo_rol = await ctx.guild.create_role(
                name=nombre,
                color=color_discord,
                hoist=True,
                mentionable=True,
                reason=f"Equipo creado por {ctx.author.name}"
            )

            # 6. Guardar en MongoDB (async)
            await equipos_col.insert_one({
                'nombre': nombre,
                'rol_id': str(nuevo_rol.id),
                'creado_por': ctx.author.name,
                'fecha': datetime.now()
            })

            self.bot.roles_equipos.append(nombre)

            embed = discord.Embed(
                description=f"El equipo **{nombre}** ha sido creado exitosamente.",
                color=color_discord
            )
            embed.set_author(
                name="✅ EQUIPO CREADO",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            embed.add_field(name="Rol", value=nuevo_rol.mention, inline=True)
            embed.add_field(name="Color", value=color_hex, inline=True)
            embed.set_footer(text=f"Admin: {ctx.author.display_name}")

            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para crear roles.")
        except Exception as e:
            await ctx.send(f"❌ Error al crear el equipo: {e}")
            logger.error(f"Error en crear_equipo: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(EquiposCog(bot))
