"""
directores.py - Cog para gestión de Directores Técnicos
Comandos: /dt, /renunciar, /mi_rol
"""
import asyncio
import discord
from discord.ui import View, Button, Modal, TextInput
from logger import get_module_logger
import traceback

logger = get_module_logger("directores")
from discord.ext import commands
from datetime import datetime

import config
from database import get_collection, log_action
from utils import es_admin, buscar_equipo


class FundarEquipoModal(Modal, title='📝 Fundar tu Club Formador'):
    nombre = TextInput(
        label='Nombre del Equipo',
        style=discord.TextStyle.short,
        placeholder='Ej. Los Pumas FC',
        required=True,
        max_length=50
    )

    color = TextInput(
        label='Color Hexadecimal',
        style=discord.TextStyle.short,
        placeholder='#3498db',
        default='#',
        required=True,
        min_length=7,
        max_length=7
    )

    logo_url = TextInput(
        label='URL del Escudo (PNG/JPG)',
        style=discord.TextStyle.short,
        placeholder='https://midominio.com/logo.png',
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            nombre_val = self.nombre.value.strip()
            color_val = self.color.value.strip()
            logo_val = self.logo_url.value.strip()

            if not color_val.startswith('#') or len(color_val) != 7:
                await interaction.followup.send("❌ El color debe ser un formato Hexadecimal válido (ej. #FF0000).", ephemeral=True)
                return
            
            if not logo_val.startswith('http'):
                await interaction.followup.send("❌ La URL del logo debe empezar con http:// o https://.", ephemeral=True)
                return

            equipos_col = get_collection('equipos')
            nombre_con_guion = f"-{nombre_val.upper()}" if not nombre_val.startswith('-') else nombre_val.upper()
            existe = await equipos_col.find_one({"nombre": nombre_con_guion})
            if existe:
                await interaction.followup.send(f"❌ Ya existe un equipo llamado {nombre_con_guion}. Elige otro nombre.", ephemeral=True)
                return

            pendientes_col = get_collection("clubes_pendientes_creacion")
            
            ya_mandado = await pendientes_col.find_one({"discord_id": str(interaction.user.id)})
            if ya_mandado:
                await interaction.followup.send("⚠️ Ya tienes una solicitud en proceso. Por favor espera a que se apruebe.", ephemeral=True)
                return

            await pendientes_col.insert_one({
                "discord_id": str(interaction.user.id),
                "dt_name": interaction.user.name,
                "nombre": nombre_val,
                "color": color_val,
                "logo_url": logo_val,
                "guild_id": str(interaction.guild_id),
                "fecha_solicitud": datetime.utcnow()
            })

            await interaction.followup.send(
                f"✅ **¡Solicitud enviada con éxito!**\n"
                f"El club **{nombre_val}** se está procesando. El sistema creará tus canales y rol en unos segundos. Ve revisando tu servidor.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error procesando modal FundarEquipoModal: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocurrió un error inesperado al procesar tu solicitud. Contacta a un administrador.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Error en FundarEquipoModal: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocurrió un error con el formulario.", ephemeral=True)


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
            canal_agentes = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_AGENTES_LIBRES)
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

    @commands.hybrid_command(name="mi_rol", description="Cambiar rol entre Manager y Jugador")
    async def mi_rol(self, ctx, modo: str = None):
        """Cambia tu rol: manager (solo dirige) o jugador (juega también)."""

        # 1. Verificar si es DT
        es_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not es_dt:
            await ctx.send("❌ Este comando es exclusivo para **Directores Técnicos**.")
            return

        # 2. Identificar equipo
        equipo_dt = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                break

        if not equipo_dt:
            await ctx.send("❌ Tienes el rol de DT pero no tienes equipo asignado.")
            return

        # 3. Validar argumento
        if not modo or modo.lower() not in ['manager', 'jugador']:
            embed = discord.Embed(
                title="⚙️ Configuración de Rol DT",
                description="Elige cómo quieres figurar en la plantilla:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="`/mi_rol manager`",
                value="👔 **Solo diriges.**\n• No ocupas cupo de plantilla.\n• Sigues pudiendo fichar/despedir.\n• No sales en la alineación.",
                inline=False
            )
            embed.add_field(
                name="`/mi_rol jugador`",
                value="👟 **Diriges y Juegas.**\n• Ocupas 1 cupo (1/8).\n• Sales en la alineación con ⭐.",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        modo = modo.lower()
        jugadores_col = get_collection('jugadores')

        if modo == 'manager':
            # CONVERTIR A MANAGER (async)
            result = await jugadores_col.delete_one({'discord_id': str(ctx.author.id)})

            if result.deleted_count > 0:
                await ctx.send(f"✅ **{ctx.author.display_name}**, ahora eres solo **Manager** de {equipo_dt}.\n(Has liberado un cupo en la plantilla).")
                await log_action(
                    guild_id=str(ctx.guild.id),
                    action_type=config.AuditAction.DT_ROL_CAMBIO,
                    actor_id=str(ctx.author.id),
                    actor_name=ctx.author.name,
                    details={'equipo': equipo_dt, 'nuevo_rol': 'manager'}
                )
            else:
                await ctx.send("⚠️ Ya estabas configurado como Manager (no estabas en la lista de jugadores).")

        elif modo == 'jugador':
            # CONVERTIR A JUGADOR (async)

            # Verificar si ya está
            existente = await jugadores_col.find_one({'discord_id': str(ctx.author.id)})
            if existente:
                await ctx.send("⚠️ Ya figuras como jugador en la plantilla.")
                return

            # Verificar cupos
            cantidad = await jugadores_col.count_documents({'equipo': equipo_dt})
            if cantidad > config.LIMITE_PLANTILLA:
                await ctx.send(f"❌ La plantilla de **{equipo_dt}** ya tiene demasiados jugadores ({cantidad}).\nNo puedes inscribirte como jugador.")
                return

            # Insertar (async)
            await jugadores_col.insert_one({
                'discord_id': str(ctx.author.id),
                'nombre': ctx.author.name,
                'equipo': equipo_dt,
                'es_dt': True
            })
            await ctx.send(f"✅ **{ctx.author.display_name}**, te has inscrito como **Jugador** de {equipo_dt}.\n(Ahora ocupas 1 cupo).")
            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=config.AuditAction.DT_ROL_CAMBIO,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                details={'equipo': equipo_dt, 'nuevo_rol': 'jugador'}
            )

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

            # 3. Enviar Embed con las nuevas instrucciones
            embed = discord.Embed(
                title="🎫 ¡LICENCIA DE FUNDADOR OTORGADA! 🎫",
                description=f"Felicidades {usuario.mention}, has sido acreditado como Director Técnico oficial por la Administración.\n\n"
                            f"**Tu siguiente paso es diseñar tu propio club formador:**\n"
                            f"🪄 Ejecuta el comando `/fundar_equipo` aquí mismo en el servidor para establecer tu insignia y colores.",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=usuario.display_avatar.url)
            
            await ctx.send(content=f"{usuario.mention}", embed=embed)
            logger.info(f"🎫 Licencia DT otorgada a {usuario.name} por {ctx.author.name}")

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos suficientes para asignar el rol de DT. (Verifica mis permisos)")
        except Exception as e:
            await ctx.send(f"❌ Error inesperado: {e}")
            logger.error(f"Error en licencia_dt: {e}", exc_info=True)

    @commands.hybrid_command(name="fundar_equipo", description="Crea tu propio equipo (Requiere Licencia de DT)")
    async def fundar_equipo(self, ctx: commands.Context):
        """Abre el formulario para fundar un nuevo equipo directo en Discord."""
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

        # Abrir ventana Modal
        modal = FundarEquipoModal()
        await ctx.interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(DirectoresCog(bot))
