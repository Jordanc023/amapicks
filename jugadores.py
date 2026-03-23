"""
jugadores.py - Cog para comandos de jugadores
Comandos: /aglibre, /mi_equipo, /h (historial), /plantilla, /sincronizar
"""
import discord
from logger import get_module_logger

logger = get_module_logger("jugadores")
from typing import List
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime

import config
from database import get_collection, mercado_esta_abierto, contar_jugadores_equipo
from utils import check_es_admin, buscar_equipo, es_admin


class BotonFicharAgenteView(View):
    """Botón adjunto al anuncio de Agente Libre para que los DTs envíen oferta rápido."""
    def __init__(self, jugador_id: int):
        super().__init__(timeout=None) # Persistente
        self.jugador_id = jugador_id

    @discord.ui.button(label="💼 Fichar Jugador", style=discord.ButtonStyle.primary, custom_id="btn_fichar_agente")
    async def boton_fichar(self, interaction: discord.Interaction, button: Button):
        # Verificar si el usuario que clickea es DT
        es_dt = any(rol.name == config.ROL_DE_DT for rol in interaction.user.roles)
        if not es_dt:
            return await interaction.response.send_message("❌ Solo los Directores Técnicos (DT) pueden usar este botón.", ephemeral=True)
            
        canal_ofertas = interaction.guild.get_channel(config.CANAL_FICHAJES_ID)
        if canal_ofertas:
            await interaction.response.send_message(f"✅ ¡Excelente! Ve al canal {canal_ofertas.mention} y usa el comando:\n `/fichar <@{self.jugador_id}>` para enviarle tu propuesta económica.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Usa el comando `/fichar <@{self.jugador_id}>` en el canal de ofertas para contratarlo.", ephemeral=True)


async def autocomplete_equipos(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocompletado para nombres de equipos."""
    equipos = interaction.client.roles_equipos
    current_lower = current.lower().replace('-', '').replace(' ', '')

    coincidencias = []
    for eq in equipos:
        eq_clean = eq.lower().replace('-', '').replace(' ', '')
        if current_lower in eq_clean or eq_clean.startswith(current_lower):
            coincidencias.append(eq)

    return [
        app_commands.Choice(name=eq, value=eq)
        for eq in coincidencias[:25]
    ]


class JugadoresCog(commands.Cog):
    """Cog para comandos de jugadores."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="mi_equipo", description="Ver tu equipo actual")
    async def mi_equipo(self, ctx):
        """Muestra el equipo actual del usuario."""
        jugadores_col = get_collection('jugadores')
        resultado = await jugadores_col.find_one({'discord_id': str(ctx.author.id)})

        if resultado:
            await ctx.send(f"⚽ {ctx.author.mention}, estás fichado en: **{resultado['equipo']}**")
        else:
            await ctx.send(f"❌ {ctx.author.mention}, figuras como **Agente Libre**.")

    @commands.hybrid_command(name="aglibre", description="Inscribirse como Agente Libre con tu posición")
    @app_commands.describe(posicion="Tu posición de juego: GK, DEF, MC, DC")
    @app_commands.choices(posicion=[
        app_commands.Choice(name="GK - Portero", value="GK"),
        app_commands.Choice(name="DEF - Defensa", value="DEF"),
        app_commands.Choice(name="MC - Mediocampista", value="MC"),
        app_commands.Choice(name="DC - Delantero", value="DC"),
    ])
    async def aglibre(self, ctx, posicion: app_commands.Choice[str]):
        """Te registra como Agente Libre con tu posición de juego."""
        pos = posicion.value

        # Verificar si tiene algún rol de equipo
        equipo_actual = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_actual = rol.name
                break

        es_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)

        if equipo_actual or es_dt:
            motivo = f"perteneces a **{equipo_actual}**" if equipo_actual else "eres **Director Técnico**"
            embed = discord.Embed(
                description=f"No puedes ser Agente Libre porque {motivo}.\nDebes renunciar o ser despedido primero.",
                color=discord.Color.from_rgb(45, 45, 45)
            )
            embed.set_author(name="❌ No disponible")
            await ctx.send(embed=embed)
            return

        # Verificar si ya tiene rol de agente libre
        tiene_rol_agente = any(rol.name == config.ROL_AGENTE_LIBRE for rol in ctx.author.roles)

        if tiene_rol_agente:
            agentes_col = get_collection('agentes_libres')
            await agentes_col.update_one(
                {'discord_id': str(ctx.author.id)},
                {'$set': {'posicion': pos}}
            )
            embed = discord.Embed(
                description=f"Ya eras Agente Libre. Tu posición ha sido actualizada a **{pos}**.",
                color=discord.Color.from_rgb(45, 45, 45)
            )
            embed.set_author(name="ℹ️ Posición Actualizada")
            await ctx.send(embed=embed)
            return

        try:
            # Agregar rol de Agente Libre
            rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
            if rol_agente:
                await ctx.author.add_roles(rol_agente)
            else:
                await ctx.send("❌ No se encontró el rol de Agente Libre. Contacta a un admin.")
                return

            # Confirmación
            embed = discord.Embed(
                description=f"Ahora eres **Agente Libre**.\n📍 Posición: **{pos}**\nLos DTs han sido notificados.",
                color=discord.Color.from_rgb(40, 40, 40)
            )
            embed.set_author(name="✅ REGISTRADO COMO AGENTE LIBRE", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

            # DM al usuario
            try:
                dm_embed = discord.Embed(
                    title="✅ REGISTRADO COMO AGENTE LIBRE",
                    description=f"Ahora eres **Agente Libre** en **{ctx.guild.name}**.\n\n"
                                f"📍 **Posición:** {pos}\n"
                                f"📢 Los DTs han sido notificados.\n\n"
                                f"💡 *Cuando un DT quiera ficharte, recibirás una oferta aquí.*",
                    color=discord.Color.from_rgb(46, 204, 113)
                )
                dm_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
                dm_embed.set_footer(text="¡Buena suerte encontrando equipo!")
                await ctx.author.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            # Notificar en canal de agentes libres (Mejorado con estilo y botón)
            canal_agentes = ctx.guild.get_channel(config.CANAL_AGENTES_LIBRES_ID)
            rol_dt = discord.utils.get(ctx.guild.roles, name=config.ROL_DE_DT)

            if canal_agentes:
                pos_colores = {
                    'GK': discord.Color.from_rgb(234, 179, 8),  # Amarillo
                    'DEF': discord.Color.from_rgb(59, 130, 246), # Azul
                    'MC': discord.Color.from_rgb(34, 197, 94),   # Verde
                    'DC': discord.Color.from_rgb(239, 68, 68)    # Rojo
                }
                color_embed = pos_colores.get(pos, discord.Color.light_grey())
                
                # Fetch DB para ver si tiene ex_equipo
                agentes_col = get_collection('agentes_libres')
                agente_previo = await agentes_col.find_one({'discord_id': str(ctx.author.id)})
                ex_equipo = agente_previo.get('ex_equipo') if agente_previo else None

                agente_embed = discord.Embed(
                    title="📋 CV Deportivo",
                    description=f"**{ctx.author.mention}** se ha declarado en estado de agencia libre y está escuchando ofertas de clubes.",
                    color=color_embed
                )
                agente_embed.set_author(name="🆕 NUEVO AGENTE LIBRE", icon_url=ctx.author.display_avatar.url)
                agente_embed.add_field(name="📍 Posición", value=f"**{pos}**", inline=True)
                if ex_equipo:
                    agente_embed.add_field(name="🔙 Último Club", value=f"*{ex_equipo}*", inline=True)
                    
                agente_embed.set_thumbnail(url=ctx.author.display_avatar.url)
                agente_embed.set_footer(text="Haz clic en el botón inferior para iniciar negociaciones")

                content = rol_dt.mention if rol_dt else ""
                view_fichar = BotonFicharAgenteView(ctx.author.id)
                await canal_agentes.send(content=content, embed=agente_embed, view=view_fichar)

            # Guardar en BD
            agentes_col = get_collection('agentes_libres')
            await agentes_col.update_one(
                {'discord_id': str(ctx.author.id)},
                {'$set': {
                    'discord_id': str(ctx.author.id),
                    'nombre': ctx.author.name,
                    'posicion': pos,
                    'ex_equipo': None,
                    'fecha': datetime.now().isoformat(),
                    'avatar_url': str(ctx.author.display_avatar.url)
                }},
                upsert=True
            )

            logger.info(f"🆕 Nuevo agente libre: {ctx.author.name} ({pos})")

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para asignar roles.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            logger.error(f"Error en aglibre: {e}", exc_info=True)

    @commands.hybrid_command(name="h", description="Ver historial de un jugador")
    async def historial_jugador(self, ctx, jugador: discord.Member):
        """Muestra el historial completo de un jugador con diseño visual premium."""
        await ctx.defer()

        jugadores_col = get_collection('jugadores')
        agentes_col = get_collection('agentes_libres')
        audit_col = get_collection('audit_logs')

        jugador_db = await jugadores_col.find_one({'discord_id': str(jugador.id)})
        agente_db = await agentes_col.find_one({'discord_id': str(jugador.id)})

        db_src = jugador_db or agente_db or {}
        equipo_actual = jugador_db.get('equipo') if jugador_db else None
        posicion = db_src.get('posicion', None)
        dorsal = db_src.get('dorsal', '??')
        goles = db_src.get('goles', 0)
        asistencias = db_src.get('asistencias', 0)
        mvps = db_src.get('mvps', 0)
        partidos = db_src.get('partidos_jugados', db_src.get('partidos', 0))
        precio = db_src.get('precio') or db_src.get('clausula') or db_src.get('valor_mercado') or 0

        # ── Color y Logo del Equipo (si tiene) ──
        equipos_col = get_collection('equipos')
        color_hex = "#1a1a1a"
        escudo_url = None
        equipo_display = "Agente Libre" if any(rol.name == config.ROL_AGENTE_LIBRE for rol in jugador.roles) else "Sin equipo"
        
        if equipo_actual:
            equipo_display = equipo_actual
            equipo_db_data = await equipos_col.find_one({'nombre': equipo_actual})
            if equipo_db_data:
                color_hex = equipo_db_data.get('color', color_hex)
                escudo_url = equipo_db_data.get('escudo_url', None)

        # ── Sección: Timeline del historial ──
        cursor = audit_col.find({
            'target_id': str(jugador.id),
            'action_type': {'$in': ['FICHAJE', 'DESPIDO', 'RENUNCIA']}
        }).sort('timestamp', -1).limit(6)
        historial_raw = await cursor.to_list(length=6)
        
        historial_list = []
        for evento in historial_raw:
            fecha_str = evento.get('timestamp').strftime('%d/%m/%y') if evento.get('timestamp') else '??/??'
            tipo = evento.get('action_type')
            eq_hist = evento.get('details', {}).get('equipo', '?')
            historial_list.append((fecha_str, tipo, eq_hist))

        await ctx.send("🎨 `Forjando Player Card en alta definición...`", delete_after=3)

        try:
            import utils_imagen
            imagen_bytes = await utils_imagen.generar_tarjeta_jugador(
                nombre_jugador=jugador.display_name,
                avatar_url=jugador.display_avatar.url if jugador.display_avatar else None,
                equipo_nombre=equipo_display,
                color_hex=color_hex,
                escudo_url=escudo_url,
                posicion=posicion,
                dorsal=dorsal,
                goles=goles,
                asistencias=asistencias,
                mvps=mvps,
                partidos=partidos,
                precio=precio,
                historial=historial_list
            )
            
            # ── Custom embed simple con foto adjunta ──
            file = discord.File(fp=imagen_bytes, filename="playercard.png")
            embed = discord.Embed(color=discord.Color.from_rgb(212, 175, 55)) # Dorado Global
            embed.set_image(url="attachment://playercard.png")
            fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
            embed.set_footer(text=f"Amapicks • {fecha_actual} • Solicitado por {ctx.author.display_name}")
            
            await ctx.send(file=file, embed=embed)
        except ImportError:
            await ctx.send("❌ El motor gráfico Pillow no está instalado en el servidor.")
        except Exception as e:
            logger.error(f"Error generando imagen de tarjeta de jugador: {e}", exc_info=True)
            await ctx.send(f"❌ Ocurrió un error al forjar la Player Card: {e}")

    @commands.hybrid_command(name="plantilla", description="Ver la plantilla de un equipo")
    @app_commands.autocomplete(nombre_equipo=autocomplete_equipos)
    async def plantilla(self, ctx, *, nombre_equipo: str = None):
        """Muestra la plantilla de jugadores de un equipo."""
        # Recarga de emergencia
        if not self.bot.roles_equipos:
            logger.warning("⚠️ Lista de equipos vacía. Recargando...")
            await self.bot.cargar_equipos()

        # Si no se especificó equipo, buscar el del usuario
        if nombre_equipo is None:
            equipo_usuario = None
            for rol in ctx.author.roles:
                if rol.name in self.bot.roles_equipos:
                    equipo_usuario = rol.name
                    break

            if equipo_usuario is None:
                equipos_text = "\n".join([f"• {eq}" for eq in self.bot.roles_equipos])
                embed = discord.Embed(
                    title="❌ Especifica un Equipo",
                    description="No perteneces a ningún equipo.\nUsa: `/plantilla Nombre del Equipo`",
                    color=discord.Color.orange()
                )
                embed.add_field(name="📋 Equipos disponibles", value=equipos_text, inline=False)
                await ctx.send(embed=embed)
                return

            nombre_equipo = equipo_usuario

        equipo_encontrado, coincidencias = buscar_equipo(nombre_equipo, self.bot.roles_equipos)

        if not equipo_encontrado:
            if coincidencias:
                lista = "\n".join([f"• `/plantilla {eq}`" for eq in coincidencias])
                embed = discord.Embed(
                    title="⚠️ Múltiples Coincidencias",
                    description=f"Encontré varios equipos que coinciden con **{nombre_equipo}**:",
                    color=discord.Color.orange()
                )
                embed.add_field(name="¿Cuál buscas?", value=lista, inline=False)
            else:
                equipos_text = "\n".join([f"• {eq}" for eq in self.bot.roles_equipos])
                embed = discord.Embed(
                    title="❌ Equipo No Encontrado",
                    description=f"No existe ningún equipo llamado **{nombre_equipo}**.",
                    color=discord.Color.red()
                )
                embed.add_field(name="📋 Equipos registrados", value=equipos_text, inline=False)
            await ctx.send(embed=embed)
            return

        jugadores_col = get_collection('jugadores')
        cursor = jugadores_col.find({'equipo': equipo_encontrado})
        jugadores_raw = await cursor.to_list(length=config.LIMITE_PLANTILLA + 5)

        # Necesitamos sacar escudo y color oficial desde MongoDB
        equipos_col = get_collection('equipos')
        equipo_db = await equipos_col.find_one({'nombre': equipo_encontrado})
        
        color_hex = "#3498db"
        escudo_url = None
        if equipo_db:
            color_hex = equipo_db.get('color', color_hex)
            escudo_url = equipo_db.get('escudo_url', None)

        rol_equipo = discord.utils.get(ctx.guild.roles, name=equipo_encontrado)

        # Identificar al DT
        dt_encontrado = None
        if rol_equipo:
            for miembro in rol_equipo.members:
                if any(r.name == config.ROL_DE_DT for r in miembro.roles):
                    dt_encontrado = miembro
                    break
        
        dt_nombre = dt_encontrado.display_name if dt_encontrado else "Vacante"

        lista_jugadores = []
        miembros_cache = {str(m.id): m for m in ctx.guild.members}

        if jugadores_raw:
            for j in jugadores_raw:
                discord_id = j['discord_id']
                miembro = miembros_cache.get(str(discord_id))
                nombre_mostrado = miembro.display_name if miembro else j['nombre']
                es_el_dt = (miembro == dt_encontrado) if miembro else False
                
                lista_jugadores.append((nombre_mostrado, es_el_dt))
        else:
            lista_jugadores = []

        await ctx.send("🎨 `Dibujando la tarjeta del equipo en alta resolución...`", delete_after=3)
        
        try:
            import utils_imagen
            imagen_bytes = await utils_imagen.generar_imagen_plantilla(
                nombre_equipo=equipo_encontrado,
                color_hex=color_hex,
                escudo_url=escudo_url,
                dt_nombre=dt_nombre,
                jugadores=lista_jugadores
            )
            
            estado_mercado = await mercado_esta_abierto()
            estado = "Mercado Abierto 🟢" if estado_mercado else "Mercado Cerrado 🔴"

            # Custom embed simple con foto adjunta
            file = discord.File(fp=imagen_bytes, filename="plantilla.png")
            embed = discord.Embed(color=discord.Color.from_rgb(30, 30, 30))
            embed.set_author(name=f"Plantilla OFICIAL: {equipo_encontrado.upper()}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_image(url="attachment://plantilla.png")
            embed.set_footer(text=f"Amapicks • {estado} • Solicitado por {ctx.author.display_name}")
            
            await ctx.send(file=file, embed=embed)
        except ImportError:
            await ctx.send("❌ El motor gráfico Pillow no está instalado en el servidor.\n**Admin:** Ejecute `pip install Pillow aiohttp` en la VPS.")
        except Exception as e:
            logger.error(f"Error generando imagen de plantilla: {e}", exc_info=True)
            await ctx.send(f"❌ Ocurrió un error al dibujar la plantilla: {e}")

    @commands.hybrid_command(name="sincronizar", description="Sincronizar base de datos con roles de Discord (Admin)")
    @check_es_admin()
    async def sincronizar(self, ctx):
        """Sincroniza manualmente la BD con los roles de Discord."""
        await ctx.defer()
        await ctx.send("🔄 **Escaneando servidor...** (Esto puede tardar unos segundos)")
        await self.bot.perform_sync(ctx.guild)

        embed = discord.Embed(
            title="✅ SINCRONIZACIÓN COMPLETA",
            color=discord.Color.green()
        )
        embed.add_field(name="🗑️ Limpieza", value="✅ Revisión automática completada", inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(JugadoresCog(bot))
