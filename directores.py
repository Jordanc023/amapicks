"""
directores.py - Cog para gestión de Directores Técnicos
Comandos: /dt, /renunciar, /mi_rol
"""
import asyncio
import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from logger import get_module_logger
import traceback

logger = get_module_logger("directores")
from discord.ext import commands
from datetime import datetime

import config
from database import get_collection, log_action
from utils import es_admin, buscar_equipo


class FundarNombreModal(Modal, title='📝 Elegir Nombre'):
    nombre = TextInput(
        label='Nombre del Equipo',
        style=discord.TextStyle.short,
        placeholder='Ej. Los Pumas FC',
        required=True,
        max_length=50
    )

    def __init__(self, view: "FundarEquipoView"):
        super().__init__()
        self.view_parent = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.view_parent.nombre = self.nombre.value.strip()
            await self.view_parent.update_message(interaction)
        except Exception as e:
            logger.error(f"Error en FundarNombreModal: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error interno: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error interno: {e}", ephemeral=True)


class FundarColorSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Rojo Carmesí", description="Color Rojo intenso (#E74C3C)", emoji="🔴", value="#E74C3C"),
            discord.SelectOption(label="Azul Celeste", description="Color Azul brillante (#3498DB)", emoji="🔵", value="#3498DB"),
            discord.SelectOption(label="Verde Esmeralda", description="Color Verde oscuro (#2ECC71)", emoji="🟢", value="#2ECC71"),
            discord.SelectOption(label="Amarillo Oro", description="Color Amarillo vibrante (#F1C40F)", emoji="🟡", value="#F1C40F"),
            discord.SelectOption(label="Naranja Fuego", description="Color Naranja vivo (#E67E22)", emoji="🟠", value="#E67E22"),
            discord.SelectOption(label="Morado Rey", description="Color Morado oscuro (#9B59B6)", emoji="🟣", value="#9B59B6"),
            discord.SelectOption(label="Negro Noche", description="Color Negro profundo (#2C3E50)", emoji="⚫", value="#2C3E50"),
            discord.SelectOption(label="Blanco Puro", description="Color Blanco nieve (#FFFFFF)", emoji="⚪", value="#FFFFFF"),
        ]
        super().__init__(placeholder="🎨 Elige un color principal", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            view: FundarEquipoView = self.view
            view.color = self.values[0]
            # Mantener la seleccion visual
            for option in self.options:
                option.default = (option.value == view.color)
            await view.update_message(interaction)
        except Exception as e:
            logger.error(f"Error en FundarColorSelect: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error interno: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error interno: {e}", ephemeral=True)


class FundarEscudoModal(Modal, title='🖼️ Enlace del Escudo'):
    logo_url = TextInput(
        label='URL del Escudo (PNG/JPG)',
        style=discord.TextStyle.short,
        placeholder='https://midominio.com/logo.png',
        required=True,
        max_length=500
    )

    def __init__(self, view: "FundarEquipoView"):
        super().__init__()
        self.view_parent = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            logo_val = self.logo_url.value.strip()
            if not logo_val.startswith('http'):
                await interaction.response.send_message("❌ La URL debe empezar con http:// o https://.", ephemeral=True)
                return
            
            self.view_parent.logo_url = logo_val
            await self.view_parent.update_message(interaction)
        except Exception as e:
            logger.error(f"Error en FundarEscudoModal: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error interno: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error interno: {e}", ephemeral=True)


class FundarEquipoView(View):
    def __init__(self, user: discord.Member, logo_inicial: str = None):
        super().__init__(timeout=600.0) # 10 mins timeout
        self.user = user
        self.nombre = None
        self.color = None
        self.logo_url = logo_inicial
        
        self.add_item(FundarColorSelect())
        self.actualizar_botones()

    def actualizar_botones(self):
        # Habilitar o Deshabilitar el botón final
        listo = bool(self.nombre and self.color and self.logo_url)
        for child in self.children:
            if isinstance(child, Button) and child.custom_id == "btn_confirmar":
                child.disabled = not listo

    def build_embed(self) -> discord.Embed:
        # Resolvemos el color de manera segura
        try:
            color_val = discord.Color(int(self.color.replace("#", ""), 16)) if self.color else discord.Color.blurple()
        except:
            color_val = discord.Color.blurple()

        embed = discord.Embed(
            title="🛠️ Panel de Creación de Club",
            description="Completa los siguientes datos para fundar tu equipo.\nUsa los botones debajo para rellenar la información.",
            color=color_val
        )
        if self.user.display_avatar:
            embed.set_thumbnail(url=self.user.display_avatar.url)
        
        embed.add_field(name="📝 Nombre", value=f"✅ `{self.nombre}`" if self.nombre else "❌ Pendiente", inline=True)
        embed.add_field(name="🎨 Color", value=f"✅ `{self.color}`" if self.color else "❌ Pendiente", inline=True)
        embed.add_field(name="🖼️ Escudo", value="✅ Cargado" if self.logo_url else "❌ Pendiente", inline=True)
        
        if self.logo_url:
            embed.set_image(url=self.logo_url)
            
        return embed

    async def update_message(self, interaction: discord.Interaction):
        try:
            self.actualizar_botones()
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=self.build_embed(), view=self)
            else:
                await interaction.message.edit(embed=self.build_embed(), view=self)
        except Exception as e:
            logger.error(f"Error en update_message: {e}", exc_info=True)
            import traceback
            error_str = f"❌ Ocurrió un error al cargar la vista de Fundación:\n```py\n{traceback.format_exc()[:1500]}\n```"
            if not interaction.response.is_done():
                await interaction.response.send_message(error_str, ephemeral=True)
            else:
                await interaction.followup.send(error_str, ephemeral=True)

    @discord.ui.button(label="📝 Nombre", style=discord.ButtonStyle.secondary, custom_id="btn_nombre", row=1)
    async def btn_nombre(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(FundarNombreModal(self))

    @discord.ui.button(label="🖼️ Escudo (Link)", style=discord.ButtonStyle.secondary, custom_id="btn_escudo", row=1)
    async def btn_escudo(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(FundarEscudoModal(self))

    @discord.ui.button(label="✅ CONFIRMAR FUNDACIÓN", style=discord.ButtonStyle.success, custom_id="btn_confirmar", disabled=True, row=2)
    async def btn_confirmar(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try:
            equipos_col = get_collection('equipos')
            nombre_con_guion = f"-{self.nombre.upper()}" if not self.nombre.startswith('-') else self.nombre.upper()
            existe = await equipos_col.find_one({"nombre": nombre_con_guion})
            if existe:
                await interaction.followup.send(f"❌ Ya existe un equipo llamado {nombre_con_guion}. Elige otro nombre usando el botón 📝 Nombre.", ephemeral=True)
                return

            pendientes_col = get_collection("clubes_pendientes_creacion")
            ya_mandado = await pendientes_col.find_one({"discord_id": str(self.user.id)})
            if ya_mandado:
                await interaction.followup.send("⚠️ Ya tienes una solicitud en proceso. Por favor espera a que se apruebe.", ephemeral=True)
                return

            await pendientes_col.insert_one({
                "discord_id": str(self.user.id),
                "dt_name": self.user.name,
                "nombre": self.nombre,
                "color": self.color,
                "logo_url": self.logo_url,
                "guild_id": str(interaction.guild_id),
                "fecha_solicitud": datetime.utcnow()
            })

            # Deshabilitar todo
            for child in self.children:
                child.disabled = True
            
            embed_exito = self.build_embed()
            embed_exito.title = "🎉 ¡Solicitud de Fundación Enviada!"
            embed_exito.description = "El bot está procesando tu solicitud para crear los canales y el rol."
            await interaction.message.edit(embed=embed_exito, view=self)
            
            await interaction.followup.send(
                f"✅ **¡Solicitud enviada con éxito!**\n"
                f"El club **{self.nombre}** se está procesando. El sistema creará tus canales y rol en unos segundos. Ve revisando tu servidor.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error confirmando FundarEquipoView: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocurrió un error inesperado al procesar tu solicitud. Contacta a un administrador.", ephemeral=True)


class DirectoresCog(commands.Cog):
    """Cog para gestionar Directores Técnicos."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="renunciar", description="Renunciar a tu cargo de DT y Equipo")
    async def renunciar(self, ctx):
        """Permite a un DT renunciar a su equipo y quedar libre."""

        # 1. Verificar si es DT
        es_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not es_dt:
            await ctx.send("❌ Este comando es exclusivo para **Directores Técnicos**.")
            return

        # 2. Identificar equipo del DT
        equipo_dt = None
        rol_equipo_obj = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                rol_equipo_obj = rol
                break

        if not equipo_dt:
            rol_dt = discord.utils.get(ctx.guild.roles, name=config.ROL_DE_DT)
            if rol_dt:
                await ctx.author.remove_roles(rol_dt)
            await ctx.send("⚠️ No tenías equipo asignado, pero te he quitado el rol de DT.")
            return

        # 3. Pedir confirmación
        confirm_embed = discord.Embed(
            title="⚠️ CONFIRMACIÓN DE RENUNCIA",
            description=f"¿Estás seguro de que quieres **RENUNCIAR** a **{equipo_dt}**?\n\n"
                        "• Perderás tus permisos de DT.\n"
                        "• Quedarás como Agente Libre.\n"
                        "• El equipo quedará vacante.",
            color=discord.Color.red()
        )

        msg_confirm = await ctx.send(embed=confirm_embed)
        await msg_confirm.add_reaction("✅")
        await msg_confirm.add_reaction("✖️")

        def check(reaction, user):
            return (user == ctx.author and
                    str(reaction.emoji) in ["✅", "✖️"] and
                    reaction.message.id == msg_confirm.id)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            if str(reaction.emoji) == "✖️":
                await ctx.send("Operación cancelada.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Tiempo agotado. Operación cancelada.")
            return

        # 4. PROCEDER CON LA RENUNCIA
        try:
            jugadores_col = get_collection('jugadores')
            agentes_col = get_collection('agentes_libres')

            # Eliminar de BD (async)
            await jugadores_col.delete_one({'discord_id': str(ctx.author.id)})

            # Quitar Roles (Equipo + DT)
            rol_dt = discord.utils.get(ctx.guild.roles, name=config.ROL_DE_DT)
            roles_a_quitar = []
            if rol_equipo_obj:
                roles_a_quitar.append(rol_equipo_obj)
            if rol_dt:
                roles_a_quitar.append(rol_dt)

            if roles_a_quitar:
                await ctx.author.remove_roles(*roles_a_quitar)

            # Convertir en Agente Libre
            rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
            if rol_agente:
                await ctx.author.add_roles(rol_agente)

            # Guardar en BD Agentes Libres (async)
            await agentes_col.update_one(
                {'discord_id': str(ctx.author.id)},
                {'$set': {
                    'discord_id': str(ctx.author.id),
                    'nombre': ctx.author.name,
                    'ex_equipo': equipo_dt,
                    'fecha': datetime.now().isoformat()
                }},
                upsert=True
            )

            # Notificaciones
            embed = discord.Embed(
                description=f"**{ctx.author.display_name}** ha renunciado a **{equipo_dt}**.",
                color=discord.Color.dark_grey()
            )
            embed.set_author(name="👋 RENUNCIA OFICIAL", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

            # Log de auditoría (async)
            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=config.AuditAction.DT_RENUNCIA,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                details={'equipo': equipo_dt}
            )

            # Canal de Agentes Libres
            canal_agentes = self.bot.get_channel(config.CANAL_AGENTES_LIBRES_ID)
            if canal_agentes:
                aviso = discord.Embed(
                    description=f"**{ctx.author.display_name}** (Ex-DT {equipo_dt}) busca nuevo proyecto.",
                    color=discord.Color.gold()
                )
                aviso.set_author(name="👔 DT LIBRE", icon_url=ctx.author.display_avatar.url)
                await canal_agentes.send(embed=aviso)

        except Exception as e:
            await ctx.send(f"❌ Error al procesar renuncia: {e}")
            logger.error(f"Error en renunciar: {e}", exc_info=True)

    @commands.hybrid_command(name="dt", description="Asignar un Director Técnico a un equipo (Admin)")
    async def inscribir_dt(self, ctx, usuario: discord.Member, *, equipo: str):
        """
        Inscribe a un usuario como Director Técnico de un equipo.
        Uso: /dt @Usuario NombreEquipo
        Ejemplo: /dt @Jordan Liverpool
        """
        await ctx.defer()

        # 1. Verificar permisos de Admin
        if not es_admin(ctx.author):
            await ctx.send("❌ Solo los administradores pueden asignar DTs.")
            return

        # 2. Buscar equipo
        nombre_equipo_raw = equipo.strip()

        if not nombre_equipo_raw:
            await ctx.send("⚠️ Debes especificar el nombre del equipo.")
            return

        equipo_encontrado, coincidencias = buscar_equipo(nombre_equipo_raw, self.bot.roles_equipos)

        if not equipo_encontrado:
            if coincidencias:
                lista = "\n".join([f"• {c}" for c in coincidencias[:5]])
                await ctx.send(f"⚠️ **{nombre_equipo_raw}** es ambiguo. ¿Te referías a alguno de estos?\n{lista}")
            else:
                await ctx.send(f"❌ No encontré ningún equipo llamado **{nombre_equipo_raw}**.\nUsa `/plantilla` para ver los equipos disponibles.")
            return

        # 3. Lógica de inscripción
        try:
            rol_equipo_obj = discord.utils.get(ctx.guild.roles, name=equipo_encontrado)
            rol_dt_obj = discord.utils.get(ctx.guild.roles, name=config.ROL_DE_DT)

            if not rol_equipo_obj:
                await ctx.send(f"❌ Error crítico: El equipo existe en BD pero no encuentro el rol **{equipo_encontrado}** en Discord.")
                return

            if not rol_dt_obj:
                await ctx.send(f"❌ Error crítico: No encuentro el rol de DT **{config.ROL_DE_DT}** en Discord.")
                return

            # Asignar roles
            await usuario.add_roles(rol_equipo_obj, rol_dt_obj)

            # Guardar/Actualizar en MongoDB (async)
            jugadores_col = get_collection('jugadores')
            await jugadores_col.update_one(
                {'discord_id': str(usuario.id)},
                {'$set': {
                    'discord_id': str(usuario.id),
                    'nombre': usuario.name,
                    'equipo': equipo_encontrado,
                    'es_dt': True
                }},
                upsert=True
            )

            # Quitar de Agentes Libres si estaba ahí (async)
            agentes_col = get_collection('agentes_libres')
            await agentes_col.delete_one({'discord_id': str(usuario.id)})

            rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
            if rol_agente and rol_agente in usuario.roles:
                await usuario.remove_roles(rol_agente)

            # Embed de confirmación
            embed = discord.Embed(
                description=f"**{usuario.display_name}** ahora es DT de **{equipo_encontrado}**",
                color=discord.Color.gold()
            )
            embed.set_author(name="👔 NUEVO DIRECTOR TÉCNICO", icon_url=usuario.display_avatar.url)
            embed.add_field(name="Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="Equipo", value=equipo_encontrado, inline=True)

            if hasattr(rol_equipo_obj, 'icon') and rol_equipo_obj.icon:
                embed.set_thumbnail(url=rol_equipo_obj.icon.url)
            else:
                embed.set_thumbnail(url=usuario.display_avatar.url)

            await ctx.send(embed=embed)
            logger.info(f"👔 Nuevo DT: {usuario.name} -> {equipo_encontrado} (por {ctx.author.name})")

            # Log de auditoría (async)
            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=config.AuditAction.DT_ASIGNADO,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                target_id=str(usuario.id),
                target_name=usuario.name,
                details={'equipo': equipo_encontrado}
            )

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para asignar roles. Sube mi rol por encima de los equipos y DTs.")
        except Exception as e:
            await ctx.send(f"❌ Error inesperado: {e}")
            logger.error(f"Error en inscribir_dt: {e}", exc_info=True)

    @commands.hybrid_command(name="banco", description="Revisar el estado de cuenta y fondos de tu equipo (DT).")
    async def ver_banco(self, ctx):
        """Muestra el presupuesto, fondos retenidos y valor de plantilla del equipo del DT."""
        await ctx.defer(ephemeral=True)
        
        # 1. Validar que sea DT
        if not discord.utils.get(ctx.author.roles, name=config.ROL_DE_DT):
            await ctx.send("❌ Este comando es exclusivo para **Directores Técnicos**.", ephemeral=True)
            return
            
        # 2. Encontrar el rol de su equipo
        equipo_nombre = None
        for rol in ctx.author.roles:
            if str(rol.name) in self.bot.roles_equipos or (rol.name.startswith('-') and rol.name != config.ROL_DE_DT):
                equipo_nombre = rol.name
                break
                
        if not equipo_nombre:
            await ctx.send("⚠️ Eres DT pero no pareces tener el rol de tu equipo asignado.", ephemeral=True)
            return

        equipos_col = get_collection("equipos")
        jugadores_col = get_collection("jugadores")
        ofertas_col = get_collection("ofertas_pendientes")

        equipo_doc = await equipos_col.find_one({"nombre": equipo_nombre})
        if not equipo_doc:
            await ctx.send("⚠️ Error: Tu equipo no está registrado en la base de datos.", ephemeral=True)
            return

        # 3. Calcular Métrica 1: Presupuesto Bruto
        presupuesto_total = equipo_doc.get("presupuesto", 0)

        # 4. Calcular Métrica 2: Fondos Retenidos (Escrow)
        fondos_retenidos = 0
        ofertas_pendientes = ofertas_col.find({"equipo": equipo_nombre})
        async for oferta in ofertas_pendientes:
            fondos_retenidos += oferta.get("monto_ofrecido", 0)

        # 5. Calcular Métrica 3: Valor de Plantilla
        valor_plantilla = 0
        jugadores_equipo = jugadores_col.find({"equipo": equipo_nombre})
        async for jugador in jugadores_equipo:
            valor_plantilla += jugador.get("precio", 0)

        # 6. Presupuesto Disponible
        presupuesto_disponible = presupuesto_total - fondos_retenidos

        # Construir Embed bancario
        embed = discord.Embed(
            title=f"🏦 Banco del {equipo_nombre} 🏦",
            description="Estado de cuenta financiero del club.",
            color=discord.Color.from_rgb(0, 153, 51) # Color verde billete
        )
        embed.add_field(
            name="💰 Presupuesto Total", 
            value=f"**${presupuesto_total:,}**", 
            inline=False
        )
        
        if fondos_retenidos > 0:
            embed.add_field(
                name="🔒 Fondos Retenidos (Ofertas Pendientes)", 
                value=f"**-${fondos_retenidos:,}**", 
                inline=False
            )
            
        embed.add_field(
            name="✅ Presupuesto Disponible para Fichar", 
            value=f"```diff\n+ ${presupuesto_disponible:,}\n```", 
            inline=False
        )
        
        embed.add_field(
            name="📈 Valorización de la Plantilla", 
            value=f"${valor_plantilla:,}", 
            inline=False
        )
        
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png")
        embed.set_footer(text=f"Consultado por el DT {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None)
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="licencia_dt", description="Otorga permiso a un usuario para fundar un club en la Web (Admin)")
    async def licencia_dt(self, ctx, usuario: discord.Member):
        """
        Da la licencia de DT al usuario y le permite usar /fundar_equipo.
        """
        await ctx.defer()
        
        if not es_admin(ctx.author):
            await ctx.send("❌ Solo los administradores pueden otorgar licencias de DT.")
            return

        rol_licencia_obj = ctx.guild.get_role(getattr(config, 'ROL_LICENCIA_ID', 1474670232181411994))
        if not rol_licencia_obj:
            await ctx.send(f"❌ Error: No encuentro el rol de Licencia de Fundador (ID: 1474670232181411994) en el servidor.")
            return

        try:
            # 1. Asignar rol de Licencia en Discord
            if rol_licencia_obj not in usuario.roles:
                await usuario.add_roles(rol_licencia_obj)
            
            # 2. Registrar en MongoDB como DT Libre (sin equipo)
            jugadores_col = get_collection('jugadores')
            await jugadores_col.update_one(
                {'discord_id': str(usuario.id)},
                {'$set': {
                    'discord_id': str(usuario.id),
                    'nombre': usuario.name,
                    'es_dt': True,
                    'equipo': None,
                    'guild_id': str(ctx.guild.id)
                }},
                upsert=True
            )

            # Quitar de Agentes Libres visualmente (Opcional, pero para evitar duplicados)
            agentes_col = get_collection('agentes_libres')
            await agentes_col.delete_one({'discord_id': str(usuario.id)})

            import datetime
            fecha = datetime.datetime.now().strftime('%d/%m/%Y')
            
            # 3. Enviar Embed con las nuevas instrucciones
            embed = discord.Embed(
                description=(
                    "╭─────────── 🏟️ ───────────╮\n"
                    "⠀⠀**LICENCIA DE MÁNAGER PRO**\n"
                    "╰─────────── ⚽ ───────────╯\n\n"
                    f"👤 **MÍSTER:** {usuario.mention}\n"
                    "📄 **RANGO:** Fundador / DT\n"
                    "✨ **PERMISO:** ✅ **CONFIRMADO**\n\n"
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
                    "📋 **PRÓXIMO PASO:**\n"
                    "Ejecuta el comando `/fundar_equipo` aquí en el servidor para registrar y diseñar la identidad visual de tu nuevo club."
                ),
                color=0xFFD700  # Dorado profesional
            )
            if ctx.guild.icon:
                embed.set_author(name="ADMINISTRACIÓN - ACREDITACIÓN OFICIAL", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name="ADMINISTRACIÓN - ACREDITACIÓN OFICIAL")
            
            embed.set_footer(text=f"Licencia ID: {str(usuario.id)[:6]}-{datetime.datetime.now().strftime('%M%S')} • Emitida: {fecha}")
            embed.set_thumbnail(url=usuario.display_avatar.url)
            
            await ctx.send(content=f"{usuario.mention}", embed=embed)
            logger.info(f"🎫 Licencia DT otorgada a {usuario.name} por {ctx.author.name}")

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos suficientes para asignar el rol de DT. (Verifica mis permisos)")
        except Exception as e:
            await ctx.send(f"❌ Error inesperado: {e}")
            logger.error(f"Error en licencia_dt: {e}", exc_info=True)

    @commands.hybrid_command(name="fundar_equipo", description="Crea tu propio equipo (Requiere Licencia de DT)")
    async def fundar_equipo(self, ctx: commands.Context, escudo: discord.Attachment = None):
        """Abre el panel interactivo para fundar un nuevo equipo directo en Discord."""
        if ctx.interaction is None:
            await ctx.send("❌ Este comando solo puede usarse como slash command (`/fundar_equipo`).", delete_after=10)
            return

        # Verificar permisos
        jugadores_col = get_collection('jugadores')
        jugador = await jugadores_col.find_one({"discord_id": str(ctx.author.id)})
        
        # Deben tener es_dt = True y no tener equipo
        if not jugador or not jugador.get("es_dt", False):
            await ctx.send("❌ No tienes una **Licencia de DT**. Pide a los administradores que te otorguen una usando `/licencia_dt`.", ephemeral=True)
            return
            
        if jugador.get("equipo"):
            await ctx.send(f"❌ Ya eres el DT del equipo **{jugador.get('equipo')}**. Debes renunciar primero si quieres fundar uno nuevo.", ephemeral=True)
            return

        logo_url = escudo.url if escudo else None

        # Abrir ventana Dashboard interactiva
        view = FundarEquipoView(user=ctx.author, logo_inicial=logo_url)
        embed = view.build_embed()
        
        mensaje_tip = ""
        if not logo_url:
            mensaje_tip = ("💡 *Tip: Si tienes el logo en tu PC/celular, puedes usar el comando nuevamente adjuntando "
                           "la imagen en el parámetro 'escudo' para que se cargue automáticamente. Así te evitas poner enlaces.*")

        await ctx.send(content=mensaje_tip, embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="subdt", description="Asigna un Sub-Director Técnico a tu equipo (cuenta en la plantilla).")
    @app_commands.describe(usuario="El jugador que será el SubDT")
    async def asignar_subdt(self, ctx, usuario: discord.Member):
        """Asigna un SubDT al equipo. El SubDT cuenta como parte de la plantilla."""
        await ctx.defer()
        
        # 1. Validar que quien ejecuta sea DT
        if not discord.utils.get(ctx.author.roles, name=config.ROL_DE_DT):
            await ctx.send("❌ Solo el **Director Técnico** puede asignar un SubDT.", ephemeral=True)
            return
        
        # 2. Encontrar el equipo del DT
        equipo_nombre = None
        for rol in ctx.author.roles:
            if str(rol.name) in self.bot.roles_equipos or (rol.name.startswith('-') and rol.name != config.ROL_DE_DT):
                equipo_nombre = rol.name
                break
        
        if not equipo_nombre:
            await ctx.send("⚠️ No se encontró tu equipo.", ephemeral=True)
            return
        
        # 3. Verificar que el usuario sea jugador del mismo equipo
        jugadores_col = get_collection('jugadores')
        jugador_doc = await jugadores_col.find_one({
            'discord_id': str(usuario.id),
            'equipo': equipo_nombre
        })
        
        if not jugador_doc:
            await ctx.send(f"❌ **{usuario.display_name}** no es un jugador de tu equipo.", ephemeral=True)
            return
        
        # 4. Verificar que no sea el DT actual
        if jugador_doc.get('es_dt', False):
            await ctx.send("❌ No puedes asignar al DT como SubDT.", ephemeral=True)
            return
        
        # 5. Asignar rol de SubDT
        await jugadores_col.update_one(
            {'discord_id': str(usuario.id)},
            {'$set': {'es_subdt': True}}
        )
        
        # 6. Quitar SubDT anterior si existe
        await jugadores_col.update_many(
            {
                'discord_id': {'$ne': str(usuario.id)},
                'equipo': equipo_nombre,
                'es_subdt': True
            },
            {'$unset': {'es_subdt': ''}}
        )
        
        # Embed de confirmación
        embed = discord.Embed(
            description=f"**{usuario.display_name}** ahora es **Sub-Director Técnico** de **{equipo_nombre}**",
            color=discord.Color.blue()
        )
        embed.set_author(name="🎖️ NUEVO SUB-DIRECTOR TÉCNICO", icon_url=usuario.display_avatar.url)
        embed.add_field(name="Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="Equipo", value=equipo_nombre, inline=True)
        embed.set_footer(text="El SubDT cuenta como parte de la plantilla")
        
        await ctx.send(embed=embed)
        logger.info(f"🎖️ Nuevo SubDT: {usuario.name} -> {equipo_nombre}")
    
    @commands.hybrid_command(name="capitan", description="Asigna un Capitán a tu equipo (cuenta en la plantilla).")
    @app_commands.describe(usuario="El jugador que será el Capitán")
    async def asignar_capitan(self, ctx, usuario: discord.Member):
        """Asigna un Capitán al equipo. El Capitán cuenta como parte de la plantilla."""
        await ctx.defer()
        
        # 1. Validar que quien ejecuta sea DT
        if not discord.utils.get(ctx.author.roles, name=config.ROL_DE_DT):
            await ctx.send("❌ Solo el **Director Técnico** puede asignar un Capitán.", ephemeral=True)
            return
        
        # 2. Encontrar el equipo del DT
        equipo_nombre = None
        for rol in ctx.author.roles:
            if str(rol.name) in self.bot.roles_equipos or (rol.name.startswith('-') and rol.name != config.ROL_DE_DT):
                equipo_nombre = rol.name
                break
        
        if not equipo_nombre:
            await ctx.send("⚠️ No se encontró tu equipo.", ephemeral=True)
            return
        
        # 3. Verificar que el usuario sea jugador del mismo equipo
        jugadores_col = get_collection('jugadores')
        jugador_doc = await jugadores_col.find_one({
            'discord_id': str(usuario.id),
            'equipo': equipo_nombre
        })
        
        if not jugador_doc:
            await ctx.send(f"❌ **{usuario.display_name}** no es un jugador de tu equipo.", ephemeral=True)
            return
        
        # 4. Verificar que no sea el DT actual
        if jugador_doc.get('es_dt', False):
            await ctx.send("❌ No puedes asignar al DT como Capitán.", ephemeral=True)
            return
        
        # 5. Asignar rol de Capitán
        await jugadores_col.update_one(
            {'discord_id': str(usuario.id)},
            {'$set': {'es_capitan': True}}
        )
        
        # 6. Quitar Capitán anterior si existe
        await jugadores_col.update_many(
            {
                'discord_id': {'$ne': str(usuario.id)},
                'equipo': equipo_nombre,
                'es_capitan': True
            },
            {'$unset': {'es_capitan': ''}}
        )
        
        # Embed de confirmación
        embed = discord.Embed(
            description=f"**{usuario.display_name}** ahora es **Capitán** de **{equipo_nombre}**",
            color=discord.Color.gold()
        )
        embed.set_author(name="⭐ NUEVO CAPITÁN", icon_url=usuario.display_avatar.url)
        embed.add_field(name="Usuario", value=usuario.mention, inline=True)
        embed.add_field(name="Equipo", value=equipo_nombre, inline=True)
        embed.set_footer(text="El Capitán cuenta como parte de la plantilla")
        
        await ctx.send(embed=embed)
        logger.info(f"⭐ Nuevo Capitán: {usuario.name} -> {equipo_nombre}")

async def setup(bot):
    await bot.add_cog(DirectoresCog(bot))
