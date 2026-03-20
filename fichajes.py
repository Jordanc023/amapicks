"""
fichajes.py - Cog para sistema de fichajes
Comandos: /fichar, /despedir, /agentes
Ofertas persistentes en MongoDB (no se pierden al reiniciar)
"""
import discord
from logger import get_module_logger

logger = get_module_logger("fichajes")
import asyncio
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime

import config
from database import (
    get_collection, mercado_abierto_para, contar_jugadores_equipo, log_action,
    crear_oferta_pendiente, eliminar_oferta_pendiente,
    tiene_oferta_pendiente, tiene_oferta_de_otro_dt
)

async def validateOffer(player_id: str, amount: int) -> dict:
    """
    Valida que una oferta esté dentro de los rangos permitidos.
    
    - Límite inferior: 75% del valor de mercado (cláusula)
    - Límite superior: 200% del valor de mercado (cláusula)
    
    Retorna: {
        'valid': bool,
        'market_value': int,
        'min_allowed': int,
        'max_allowed': int,
        'message': str (solo si no es válida)
    }
    """
    jugadores_col = get_collection('jugadores')
    
    # Obtener valor de mercado (cláusula) del jugador
    jugador = await jugadores_col.find_one({'discord_id': str(player_id)})
    
    if not jugador:
        return {
            'valid': False,
            'market_value': 0,
            'min_allowed': 0,
            'max_allowed': 0,
            'message': "❌ Jugador no encontrado en la base de datos."
        }
    
    # Usar cláusula como market_value, o precio si no existe cláusula
    market_value = jugador.get('clausula', jugador.get('precio', 0))
    
    if market_value <= 0:
        return {
            'valid': False,
            'market_value': 0,
            'min_allowed': 0,
            'max_allowed': 0,
            'message': "❌ El jugador no tiene un valor de mercado definido. Contacta a un administrador."
        }
    
    # Calcular límites
    min_allowed = int(market_value * 0.75)  # 75% mínimo
    max_allowed = int(market_value * 2.00)  # 200% máximo
    
    # Validar límite inferior
    if amount < min_allowed:
        return {
            'valid': False,
            'market_value': market_value,
            'min_allowed': min_allowed,
            'max_allowed': max_allowed,
            'message': f"❌ **Oferta rechazada.** El mínimo permitido es `${min_allowed:,}` (75% del valor de mercado)."
        }
    
    # Validar límite superior
    if amount > max_allowed:
        return {
            'valid': False,
            'market_value': market_value,
            'min_allowed': min_allowed,
            'max_allowed': max_allowed,
            'message': f"❌ **Monto inválido.** El máximo permitido es `${max_allowed:,}` (200% del valor de mercado)."
        }
    
    # Oferta válida
    return {
        'valid': True,
        'market_value': market_value,
        'min_allowed': min_allowed,
        'max_allowed': max_allowed,
        'message': None
    }


class ConfirmacionTraspasoView(View):
    """Vista interactiva enviada por DM a un DT para que acepte o rechace la venta de su jugador."""

    def __init__(self, bot, dt_comprador_id, dt_vendedor_id, jugador, equipo_comprador, equipo_vendedor, monto):
        super().__init__(timeout=86400) # 24 horas de expiración para DMs
        self.bot = bot
        self.dt_comprador_id = dt_comprador_id
        self.dt_vendedor_id = dt_vendedor_id
        self.jugador = jugador
        self.equipo_comprador = equipo_comprador
        self.equipo_vendedor = equipo_vendedor
        self.monto = monto
        self.respondido = False

    @discord.ui.button(label="✅ Vender Jugador", style=discord.ButtonStyle.green)
    async def aceptar_venta(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.dt_vendedor_id:
            await interaction.response.send_message("❌ No eres el dueño de este equipo.", ephemeral=True)
            return

        if self.respondido:
            await interaction.response.send_message("⚠️ Esta oferta ya fue gestionada.", ephemeral=True)
            return

        await interaction.response.defer()
        self.respondido = True
        
        # Desactivar botones
        for child in self.children:
            child.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = "✅ TRASPASO ACEPTADO"
        embed.set_footer(text="Procesando transferencia...")
        await interaction.message.edit(embed=embed, view=self)

        await ejecutar_traspaso_clubes(
            self.bot, interaction, self.dt_comprador_id, self.dt_vendedor_id,
            self.jugador, self.equipo_comprador, self.equipo_vendedor, self.monto
        )

    @discord.ui.button(label="❌ Rechazar Oferta", style=discord.ButtonStyle.red)
    async def rechazar_venta(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != self.dt_vendedor_id:
            await interaction.response.send_message("❌ No eres el dueño de este equipo.", ephemeral=True)
            return

        if self.respondido:
            return

        await interaction.response.defer()
        self.respondido = True
        
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = "❌ TRASPASO RECHAZADO"
        embed.set_footer(text="Has declinado la oferta.")
        await interaction.message.edit(embed=embed, view=self)

        # Notificar al comprador
        try:
            comprador = await self.bot.fetch_user(int(self.dt_comprador_id))
            if comprador:
                await comprador.send(f"❌ El **{self.equipo_vendedor}** ha **RECHAZADO** tu oferta de `${self.monto:,}` por **{self.jugador.name}**.")
        except Exception as e:
            logger.error(f"No se pudo notificar rechazo al DT comprador: {e}")

class ConfirmacionClausulazoView(View):
    """Vista interactiva enviada por DM al *Jugador* para aceptar o rechazar un Clausulazo."""

    def __init__(self, bot, dt_comprador_id, jugador, equipo_comprador, equipo_vendedor, monto):
        super().__init__(timeout=86400) # 24 horas de expiración para DMs
        self.bot = bot
        self.dt_comprador_id = dt_comprador_id
        self.jugador = jugador
        self.equipo_comprador = equipo_comprador
        self.equipo_vendedor = equipo_vendedor
        self.monto = monto
        self.respondido = False

    @discord.ui.button(label="✅ Traición (Aceptar Clausulazo)", style=discord.ButtonStyle.green)
    async def aceptar_clausula(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.jugador:
            await interaction.response.send_message("❌ Esta oferta no es para ti.", ephemeral=True)
            return

        if self.respondido:
            await interaction.response.send_message("⚠️ Esta decisión ya fue tomada.", ephemeral=True)
            return

        await interaction.response.defer()
        self.respondido = True
        
        # Desactivar botones
        for child in self.children:
            child.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = "💼 CONTRATO FIRMADO"
        embed.description = f"Has decidido abandonar tu equipo y fichar por **{self.equipo_comprador}**."
        embed.set_footer(text="Procesando pago de cláusula...")
        await interaction.message.edit(embed=embed, view=self)

        # Aquí llamamos a la misma función de traspaso, pero el vendedor no importa porque no puede decir no
        # Para engañar un poco a la función existente (que le manda DM al vendedor), le pasamos un "DUMMY ID" para que falle silenciosamente
        await ejecutar_traspaso_clubes(
            self.bot, interaction, self.dt_comprador_id, "clara_traicion", # "clara_traicion" como id_vendedor
            self.jugador, self.equipo_comprador, self.equipo_vendedor, self.monto
        )

    @discord.ui.button(label="❌ Amor por la Camiseta (Rechazar)", style=discord.ButtonStyle.red)
    async def rechazar_clausula(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.jugador:
            await interaction.response.send_message("❌ Esta oferta no es para ti.", ephemeral=True)
            return

        if self.respondido:
            return

        await interaction.response.defer()
        self.respondido = True
        
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = "🛡️ LEALTAD DEMOSTRADA"
        embed.description = f"Le has dicho **NO** a los millones del **{self.equipo_comprador}**. Te quedas en casa."
        embed.set_footer(text="Operación cancelada.")
        await interaction.message.edit(embed=embed, view=self)

        # Notificar al comprador
        try:
            comprador = await self.bot.fetch_user(int(self.dt_comprador_id))
            if comprador:
                await comprador.send(f"❌ ¡Traición fallida! **{self.jugador.name}** ha **RECHAZADO** tu clausulazo de `${self.monto:,}` prefiriendo quedarse en su club.")
        except Exception as e:
            pass

        # Anunciar el rechazo en el Canal Fichajes
        guild = interaction.message.guild
        if not guild:
            for g in self.bot.guilds:
                if g.get_member(self.jugador.id):
                    guild = g
                    break
        if guild:
            canal_noticias = discord.utils.get(guild.text_channels, name=config.CANAL_FICHAJES)
            if canal_noticias:
                anuncio_rechazo = discord.Embed(
                    title="🛡️ ¡AMOR POR LA CAMISETA!",
                    description=(
                        f"A pesar de que el **{self.equipo_comprador}** puso `${self.monto:,}` sobre la mesa pagando su cláusula, "
                        f"el jugador **{self.jugador.mention}** ha rechazado abandonar el **{self.equipo_vendedor}**.\n\n"
                        f"*El dinero ha sido devuelto.*"
                    ),
                    color=discord.Color.from_rgb(0, 112, 255) # Azul lealtad
                )
                anuncio_rechazo.set_thumbnail(url=self.jugador.display_avatar.url)
                await canal_noticias.send(embed=anuncio_rechazo)


async def ejecutar_traspaso_clubes(bot, interaction, dt_comprador_id, dt_vendedor_id,
                                    jugador, equipo_comprador, equipo_vendedor, monto):
    """
    Ejecuta un traspaso entre clubes (oferta club-a-club o clausulazo).
    Mueve al jugador del equipo vendedor al comprador, transfiere fondos y notifica.
    """
    jugadores_col = get_collection('jugadores')
    equipos_col = get_collection('equipos')

    # Buscar guild del jugador
    guild = None
    for g in bot.guilds:
        if g.get_member(jugador.id):
            guild = g
            break

    if not guild:
        logger.error(f"No se encontró guild para el jugador {jugador.name}")
        return

    miembro = guild.get_member(jugador.id)
    if not miembro:
        logger.error(f"No se encontró miembro {jugador.id} en guild {guild.name}")
        return

    try:
        # 1. Actualizar BD: mover jugador al equipo comprador
        await jugadores_col.update_one(
            {'discord_id': str(jugador.id)},
            {'$set': {
                'equipo': equipo_comprador,
                'fecha_fichaje': datetime.now().isoformat(),
                'traspaso_desde': equipo_vendedor,
                'monto_traspaso': monto
            }}
        )

        # 2. Transferir fondos entre equipos
        # Restar del comprador
        await equipos_col.update_one(
            {'nombre': equipo_comprador},
            {'$inc': {'presupuesto': -monto}}
        )
        # Sumar al vendedor (solo si no es clausulazo sin DT)
        if dt_vendedor_id != "clara_traicion":
            await equipos_col.update_one(
                {'nombre': equipo_vendedor},
                {'$inc': {'presupuesto': monto}}
            )

        # 3. Cambiar roles en Discord
        rol_vendedor = discord.utils.get(guild.roles, name=equipo_vendedor)
        rol_comprador = discord.utils.get(guild.roles, name=equipo_comprador)

        if rol_vendedor and rol_vendedor in miembro.roles:
            await miembro.remove_roles(rol_vendedor)
        if rol_comprador:
            await miembro.add_roles(rol_comprador)

        # 4. Anuncio público en canal de fichajes
        canal_noticias = discord.utils.get(guild.text_channels, name=config.CANAL_FICHAJES)
        if canal_noticias:
            es_clausulazo = (dt_vendedor_id == "clara_traicion")
            titulo = "💣 ¡CLAUSULAZO COMPLETADO!" if es_clausulazo else "🤝 TRASPASO OFICIAL"
            color = discord.Color.from_rgb(255, 69, 0) if es_clausulazo else discord.Color.brand_green()

            embed_anuncio = discord.Embed(
                title=titulo,
                description=(
                    f"**{jugador.mention}** deja el **{equipo_vendedor}** y ficha por el **{equipo_comprador}**.\n\n"
                    f"💰 **Monto de la operación:** `${monto:,}`"
                ),
                color=color
            )
            embed_anuncio.set_thumbnail(url=jugador.display_avatar.url)
            embed_anuncio.set_footer(text=f"Traspaso completado • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            await canal_noticias.send(embed=embed_anuncio)

        # 5. Log de auditoría
        await log_action(
            guild_id=str(guild.id),
            action_type=config.AuditAction.FICHAJE,
            actor_id=dt_comprador_id,
            actor_name=equipo_comprador,
            target_id=str(jugador.id),
            target_name=jugador.name,
            details={
                'tipo': 'clausulazo' if dt_vendedor_id == "clara_traicion" else 'traspaso_club',
                'equipo_origen': equipo_vendedor,
                'equipo_destino': equipo_comprador,
                'monto': monto
            }
        )

        # 6. Notificar al DT comprador
        try:
            comprador = await bot.fetch_user(int(dt_comprador_id))
            if comprador:
                await comprador.send(
                    f"✅ ¡Traspaso completado! **{jugador.name}** ahora juega en **{equipo_comprador}**. "
                    f"Se descontaron `${monto:,}` de tu presupuesto."
                )
        except Exception:
            pass

        # 7. Canal de logs
        canal_log = discord.utils.get(guild.text_channels, name=config.CANAL_LOGS)
        if canal_log:
            log_embed = discord.Embed(
                title="📝 TRASPASO ENTRE CLUBES",
                description=f"**{jugador.name}**: {equipo_vendedor} → {equipo_comprador} por `${monto:,}`",
                color=discord.Color.green()
            )
            await canal_log.send(embed=log_embed)

        logger.info(f"✅ Traspaso completado: {jugador.name} ({equipo_vendedor} -> {equipo_comprador}) por ${monto}")

    except Exception as e:
        logger.error(f"❌ Error en ejecutar_traspaso_clubes: {e}", exc_info=True)
        # Intentar notificar al comprador del error
        try:
            comprador = await bot.fetch_user(int(dt_comprador_id))
            if comprador:
                await comprador.send(f"❌ Error procesando el traspaso de **{jugador.name}**: {e}")
        except Exception:
            pass


class ConfirmacionFichajeView(View):
    """Vista con botones para confirmar/rechazar un fichaje (enviada por DM)."""

    def __init__(self, ctx, jugador, equipo_dt, rol_equipo, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.jugador = jugador
        self.equipo_dt = equipo_dt
        self.rol_equipo = rol_equipo
        self.bot = bot
        self.value = None
        self.respondido = False

    @discord.ui.button(label="✅ Aceptar Fichaje", style=discord.ButtonStyle.green)
    async def aceptar(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.jugador:
            await interaction.response.send_message("❌ Solo tú puedes aceptar esta oferta.", ephemeral=True)
            return

        await interaction.response.defer()
        self.value = True
        self.respondido = True
        self.stop()

        # Limpiar oferta pendiente de MongoDB
        await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

        # Obtener el canal de noticias de fichajes
        canal_noticias = discord.utils.get(self.ctx.guild.text_channels, name=config.CANAL_FICHAJES)
        
        # Enviar gran anuncio al canal de fichajes
        if canal_noticias:
            embed_noticia = discord.Embed(
                title="🤝 CONTRATO FIRMADO: ¡NUEVO FICHAJE!",
                description=(
                    f"**{self.jugador.mention}** ha estampado su firma y es oficialmente nuevo jugador de **{self.equipo_dt}**.\n\n"
                    f"🎉 *¡La directiva y la afición le dan la bienvenida al club!*"
                ),
                color=discord.Color.brand_green()
            )
            embed_noticia.set_thumbnail(url=self.jugador.display_avatar.url)
            embed_noticia.set_footer(text=f"Fichaje Completado • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            await canal_noticias.send(embed=embed_noticia)

        # Editar mensaje ORIGINAL en el canal de ofertas para "limpiar"
        embed_oferta_cerrada = discord.Embed(
            description=f"✅ Oferta Aceptada. El jugador se fue a **{self.equipo_dt}**.",
            color=discord.Color.from_rgb(100, 100, 100) # Gris
        )
        await interaction.message.edit(embed=embed_oferta_cerrada, view=None)

        # Ejecutar lógica de fichaje
        await ejecutar_fichaje(self.ctx, self.jugador, self.equipo_dt, self.rol_equipo)

    @discord.ui.button(label="❌ Rechazar Oferta", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.jugador:
            await interaction.response.send_message("❌ Solo tú puedes rechazar esta oferta.", ephemeral=True)
            return

        await interaction.response.defer()
        self.value = False
        self.respondido = True
        self.stop()

        # Limpiar oferta pendiente de MongoDB
        await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

        # Obtener el canal de noticias de fichajes
        canal_noticias = discord.utils.get(self.ctx.guild.text_channels, name=config.CANAL_FICHAJES)

        # Enviar anuncio de rechazo al canal de fichajes
        if canal_noticias:
            embed_noticia = discord.Embed(
                title="❌ OFERTA RECHAZADA",
                description=(
                    f"Las negociaciones se han roto.\n"
                    f"**{self.jugador.mention}** ha rechazado formalmente la oferta de **{self.equipo_dt}**."
                ),
                color=discord.Color.brand_red()
            )
            embed_noticia.set_footer(text="El jugador declinó la oferta")
            await canal_noticias.send(embed=embed_noticia)

        # Editar mensaje ORIGINAL en el canal de ofertas
        embed_oferta_cerrada = discord.Embed(
            description=f"❌ Oferta Rechazada por el jugador.",
            color=discord.Color.from_rgb(100, 100, 100) # Gris
        )
        await interaction.message.edit(embed=embed_oferta_cerrada, view=None)



        # Notificar al DT
        try:
            await self.ctx.channel.send(f"🚫 {self.ctx.author.mention}, **{self.jugador.display_name}** ha rechazado tu oferta.")
        except (discord.Forbidden, discord.HTTPException):
            pass


async def ejecutar_fichaje(ctx, miembro, equipo_dt, rol_equipo):
    """Ejecuta el fichaje después de la confirmación (async)."""
    jugadores_col = get_collection('jugadores')
    agentes_col = get_collection('agentes_libres')

    # Verificar plantillas por seguridad (race condition)
    cantidad_jugadores = await jugadores_col.count_documents({'equipo': equipo_dt})
    if cantidad_jugadores >= config.LIMITE_PLANTILLA:
        await ctx.send(f"❌ Error crítico: La plantilla de {equipo_dt} se llenó antes de aceptar.")
        return

    try:
        # Guardar en base de datos (update_one + upsert para evitar DuplicateKeyError en race conditions)
        await jugadores_col.update_one(
            {'discord_id': str(miembro.id)},
            {'$set': {
                'discord_id': str(miembro.id),
                'nombre': miembro.name,
                'equipo': equipo_dt,
                'fecha_fichaje': datetime.now().isoformat(),
                'avatar_url': str(miembro.display_avatar.url)
            }},
            upsert=True
        )

        # Asignar rol en Discord
        await miembro.add_roles(rol_equipo)

        # Mensaje de confirmación (Se enviará al canal de noticias, no al de ofertas)
        canal_noticias = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_FICHAJES)

        embed = discord.Embed(
            title="📸 PRESENTACIÓN OFICIAL",
            description=f"**{miembro.display_name}** posa con la camiseta de **{equipo_dt}** tras firmar su nuevo contrato.",
            color=discord.Color.gold()
        )
        embed.set_author(name="✅ TRASPASO CONFIRMADO", icon_url=miembro.display_avatar.url)
        embed.add_field(name="👤 Jugador", value=miembro.mention, inline=True)
        embed.add_field(name="🛡️ Equipo", value=f"**{equipo_dt}**", inline=True)
        embed.add_field(name="📊 Plantilla", value=f"`{cantidad_jugadores + 1}/{config.LIMITE_PLANTILLA}`", inline=True)
        embed.set_thumbnail(url=miembro.display_avatar.url)
        embed.set_footer(text=f"Operación gestionada por el DT: {ctx.author.display_name}")

        if canal_noticias:
            await canal_noticias.send(embed=embed)
        else:
            await ctx.send(embed=embed) # Fallback

        logger.info(f"✅ Fichaje: {miembro.name} -> {equipo_dt}")

        # Log de auditoría (async)
        await log_action(
            guild_id=str(ctx.guild.id),
            action_type=config.AuditAction.FICHAJE,
            actor_id=str(ctx.author.id),
            actor_name=ctx.author.name,
            target_id=str(miembro.id),
            target_name=miembro.name,
            details={'equipo': equipo_dt, 'plantilla': cantidad_jugadores + 1}
        )

        # LOGS
        canal_log = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_LOGS)
        if canal_log:
            log_embed = discord.Embed(
                title="📝 NUEVO FICHAJE",
                description=f"El equipo **{equipo_dt}** ha fichado a **{miembro.display_name}**",
                color=discord.Color.green()
            )
            log_embed.add_field(name="DT", value=ctx.author.display_name)
            log_embed.set_footer(text=f"ID Jugador: {miembro.id}")
            await canal_log.send(embed=log_embed)

        # Limpieza Agente Libre (async)
        await agentes_col.delete_one({'discord_id': str(miembro.id)})
        rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
        if rol_agente and rol_agente in miembro.roles:
            await miembro.remove_roles(rol_agente)

    except Exception as e:
        await ctx.send(f"❌ Error al procesar fichaje: {e}")
        logger.error(f"Error en ejecutar_fichaje: {e}", exc_info=True)


class FichajesCog(commands.Cog):
    """Cog para gestionar fichajes y despidos."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="fichar", description="Ofertar fichaje a uno o más jugadores")
    async def fichar(self, ctx, jugadores: commands.Greedy[discord.Member]):
        """
        Envía ofertas de fichaje a uno o más jugadores.
        Uso: /fichar @jugador1 @jugador2 @jugador3
        Solo funciona en el canal de ofertas.
        """
        # Defer para evitar timeout en interacciones
        await ctx.defer()

        # Verificar que se usa en el canal correcto
        if ctx.channel.id != config.CANAL_OFERTAS_ID:
            canal_ofertas = self.bot.get_channel(config.CANAL_OFERTAS_ID)
            if canal_ofertas:
                await ctx.send(f"❌ Este comando solo funciona en {canal_ofertas.mention}", delete_after=10)
            else:
                await ctx.send("❌ Este comando solo funciona en el canal de ofertas.", delete_after=10)
            return

        # Verificar que hay al menos un jugador mencionado
        if not jugadores:
            await ctx.send("❌ Uso: `/fichar @jugador1 @jugador2 ...`")
            return

        # Identificar equipo del DT
        equipo_dt = None
        rol_equipo = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                rol_equipo = rol
                break

        # Verificar mercado (async)
        if not await mercado_abierto_para(equipo_dt):
            await ctx.send(embed=discord.Embed(
                title="🔴 Mercado Cerrado",
                description="El mercado está cerrado o no está abierto para tu equipo.",
                color=discord.Color.red()
            ))
            return

        # Validaciones de DT
        tiene_rol_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not tiene_rol_dt:
            await ctx.send("❌ Solo los **DT** pueden fichar.")
            return
        if not equipo_dt:
            await ctx.send("❌ Tienes rol DT pero no equipo.")
            return

        # Validar Cupos (async)
        cantidad_actual = await contar_jugadores_equipo(equipo_dt)
        cupos_disponibles = config.LIMITE_PLANTILLA - cantidad_actual

        if cupos_disponibles <= 0:
            await ctx.send(f"❌ **{equipo_dt}** ya tiene **{cantidad_actual}/{config.LIMITE_PLANTILLA}** jugadores. No hay cupos.")
            return

        equipos_col = get_collection("equipos")
        jugadores_col = get_collection("jugadores")
        ofertas_col = get_collection("ofertas_pendientes")

        equipo_doc = await equipos_col.find_one({"nombre": equipo_dt})
        if not equipo_doc:
            await ctx.send("❌ Error: Equipo no encontrado en BD.", delete_after=10)
            return

        presupuesto_total = equipo_doc.get("presupuesto", 0)
        
        fondos_retenidos = 0
        async for oferta in ofertas_col.find({"equipo": equipo_dt}):
            fondos_retenidos += oferta.get("monto_ofrecido", 0)
            
        presupuesto_disponible = presupuesto_total - fondos_retenidos

        # Procesar cada jugador
        enviados = []
        fallidos = []
        omitidos = []

        for miembro in jugadores:
            # Validaciones por jugador
            if miembro.id == ctx.author.id:
                omitidos.append((miembro, "No puedes ficharte a ti mismo"))
                continue
            if miembro.bot:
                omitidos.append((miembro, "No puedes fichar a un bot"))
                continue

            # Verificar si ya está fichado (async)
            jugador_existente = await jugadores_col.find_one({'discord_id': str(miembro.id)})
            if jugador_existente:
                omitidos.append((miembro, f"Ya juega en {jugador_existente['equipo']}"))
                continue

            # Verificar oferta pendiente del MISMO DT (MongoDB)
            if await tiene_oferta_pendiente(str(ctx.author.id), str(miembro.id)):
                omitidos.append((miembro, "Ya le enviaste una oferta pendiente"))
                continue
                
            # Verificar Precio vs Presupuesto
            agentes_col = get_collection('agentes_libres')
            jugador_db = await agentes_col.find_one({"discord_id": str(miembro.id)})
            
            # Si no está en agentes, quizás es clausulazo (pero por ahora /fichar es para agentes)
            # Tomamos el precio_pagado
            precio_jugador = jugador_db.get("clausula", 0) if jugador_db else 0
            
            if presupuesto_disponible < precio_jugador:
                omitidos.append((miembro, f"No tienes fondos (${presupuesto_disponible:,} disponibles, cuesta ${precio_jugador:,})"))
                continue

            # Descontar el presupuesto disponible simulado para el siguiente de la lista
            presupuesto_disponible -= precio_jugador

            # Verificar si OTRO DT ya tiene oferta pendiente
            oferta_de_otro = await tiene_oferta_de_otro_dt(str(miembro.id), str(ctx.author.id))
            if oferta_de_otro:
                omitidos.append((miembro, f"Ya tiene oferta de {oferta_de_otro}"))
                continue

            # Verificar cupos restantes
            if len(enviados) >= cupos_disponibles:
                omitidos.append((miembro, "Sin cupos disponibles"))
                continue

            # Crear vista para este jugador
            view = ConfirmacionFichajeView(ctx, miembro, equipo_dt, rol_equipo, self.bot)

            # Crear embed Público para el Canal
            canal_embed = discord.Embed(
                title="📝 PROPUESTA DE CONTRATO (OFERTA FORMAL)",
                description=(
                    f"**Estimado {miembro.mention},**\n"
                    f"La directiva de **{equipo_dt}**, representada por su Director Técnico {ctx.author.mention}, "
                    f"le presenta la siguiente oferta formal para unirse a sus filas.\n\n"
                    f"─────────────────────────\n"
                    f"💼 **TÉRMINOS DEL ACUERDO:**\n"
                    f"🔹 **Destino:** `{equipo_dt}`\n"
                    f"🔹 **Valoración de la Operación:** `${precio_jugador:,}`\n"
                    f"─────────────────────────\n\n"
                    f"⏳ *El contrato está sobre la mesa. Tiene 10 minutos para firmar o declinar.*"
                ),
                color=discord.Color.from_rgb(255, 215, 0) # Gold
            )
            canal_embed.set_thumbnail(url=miembro.display_avatar.url)
            canal_embed.set_footer(text="Responde usando los botones inferiores 👇")

            # Enviar mensaje al canal donde el DT ejecutó el comando (debe ser #ofertas)
            mensaje_oferta = await ctx.channel.send(content=miembro.mention, embed=canal_embed, view=view)
            
            # (Opcional) Enviar PM puramente informativo
            try:
                pm_info = discord.Embed(
                    title="⚽ Oferta en Curso",
                    description=f"El equipo **{equipo_dt}** te ha hecho una oferta.\n"
                                f"Revisa el canal {ctx.channel.mention} en el servidor **{ctx.guild.name}** para responder.",
                    color=discord.Color.blue()
                )
                await miembro.send(embed=pm_info)
            except (discord.Forbidden, discord.HTTPException):
                pass # Si los DMs están cerrados, no importa, ya está en el canal

            # Registrar oferta pendiente en MongoDB (persistente!)
            ofertas_col = get_collection('ofertas_pendientes')
            await ofertas_col.insert_one({
                'dt_id': str(ctx.author.id),
                'jugador_id': str(miembro.id),
                'equipo': equipo_dt,
                'monto_ofrecido': precio_jugador,
                'timestamp': datetime.utcnow()
            })

            enviados.append(miembro)
            logger.info(f"📢 Oferta Pública enviada: {equipo_dt} -> {miembro.name}")

            # Iniciar loop de expiración en 10 minutos
            asyncio.create_task(self._reminder_loop_canal(view, miembro, equipo_dt, ctx.author, mensaje_oferta))

        # Resumen de ofertas enviadas
        resumen_embed = discord.Embed(
            title="📨 OFERTAS ENVIADAS",
            color=discord.Color.blue()
        )

        # Ya no hay fallidos (DMs bloqueados), todos se envían al canal
        if enviados:
            lista_enviados = "\n".join([f"✅ {m.display_name}" for m in enviados])
            resumen_embed.add_field(name=f"📢 Ofertas Públicas ({len(enviados)})", value=lista_enviados, inline=False)

        if omitidos:
            lista_omitidos = "\n".join([f"❌ {m.display_name}: {razon}" for m, razon in omitidos])
            resumen_embed.add_field(name=f"🚫 Omitidos ({len(omitidos)})", value=lista_omitidos, inline=False)

        resumen_embed.set_footer(text=f"Cupos Ocupados/Disponibles: {cantidad_actual + len(enviados)}/{config.LIMITE_PLANTILLA}")

        await ctx.send(embed=resumen_embed, delete_after=60)



    async def _reminder_loop_canal(self, view, jugador, equipo, dt_member, mensaje_oferta):
        """Loop que expira ofertas en canal después de 10 minutos."""
        await asyncio.sleep(600)  # 10 minutos

        if not view.respondido:
            # Limpiar oferta de MongoDB
            ofertas_col = get_collection('ofertas_pendientes')
            await ofertas_col.delete_many({'jugador_id': str(jugador.id), 'dt_id': str(dt_member.id)})

            # Editar el mensaje original para inhabilitar los botones
            try:
                view.stop()

                if mensaje_oferta:
                    # Enviar expiración al canal de noticias
                    canal_noticias = discord.utils.get(dt_member.guild.text_channels, name=config.CANAL_FICHAJES)
                    expire_embed = discord.Embed(
                        title="⏱️ OFERTA EXPIRADA",
                        description=(
                            f"El plazo de negociación ha vencido.\n"
                            f"**{jugador.display_name}** no respondió a tiempo a la oferta de **{equipo}**.\n\n"
                            f"*El contrato ha sido retirado de la mesa.*"
                        ),
                        color=discord.Color.dark_grey()
                    )
                    if canal_noticias:
                        await canal_noticias.send(embed=expire_embed)

                    # Achicar la oferta original para limpiar
                    oferta_cerrada = discord.Embed(
                        description=f"⏰ Expirada: **{jugador.display_name}** no respondió a **{equipo}**.",
                        color=discord.Color.from_rgb(100, 100, 100) # Gris
                    )
                    await mensaje_oferta.edit(embed=oferta_cerrada, view=None)
            except (discord.Forbidden, discord.HTTPException):
                pass
            
            logger.info(f"⏰ Oferta en canal expirada: {equipo} -> {jugador.name}")

    @commands.hybrid_command(name="despedir", description="Despedir a un jugador de tu equipo")
    async def despedir(self, ctx, miembro: discord.Member):
        """Echa a un jugador del equipo (Solo DT)."""
        await ctx.defer()

        # Identificar equipo del DT
        equipo_dt = None
        rol_equipo = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                rol_equipo = rol
                break

        # Verificar mercado (async)
        if not await mercado_abierto_para(equipo_dt):
            await ctx.send(embed=discord.Embed(
                title="🔴 Mercado Cerrado",
                description="El mercado está cerrado o no está abierto para tu equipo.",
                color=discord.Color.red()
            ))
            return

        if not miembro:
            await ctx.send("❌ Uso: `/despedir @usuario`")
            return

        # Validaciones
        tiene_rol_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not tiene_rol_dt:
            await ctx.send("❌ Solo DTs.")
            return
        if not equipo_dt:
            await ctx.send("❌ No tienes equipo.")
            return

        jugadores_col = get_collection('jugadores')
        agentes_col = get_collection('agentes_libres')

        jugador_db = await jugadores_col.find_one({'discord_id': str(miembro.id)})
        if not jugador_db:
            await ctx.send("❌ El jugador no tiene equipo.")
            return
        if jugador_db['equipo'] != equipo_dt:
            await ctx.send(f"❌ El jugador es de **{jugador_db['equipo']}**, no tuyo.")
            return

        try:
            await jugadores_col.delete_one({'discord_id': str(miembro.id)})
            await miembro.remove_roles(rol_equipo)

            # Dar rol agente libre
            rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
            if rol_agente:
                await miembro.add_roles(rol_agente)

            left = await jugadores_col.count_documents({'equipo': equipo_dt})

            embed = discord.Embed(
                description=f"**{miembro.display_name}** ha sido removido de **{equipo_dt}**",
                color=discord.Color.dark_grey()
            )
            embed.set_author(name="📤 JUGADOR DESPEDIDO", icon_url=miembro.display_avatar.url)
            embed.add_field(name="Plantilla", value=f"{left}/{config.LIMITE_PLANTILLA}")
            await ctx.send(embed=embed)

            # Log de auditoría (async)
            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=config.AuditAction.DESPIDO,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                target_id=str(miembro.id),
                target_name=miembro.name,
                details={'equipo': equipo_dt, 'plantilla': left}
            )

            # Notificaciones
            canal_agentes = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_AGENTES_LIBRES)
            if canal_agentes:
                await canal_agentes.send(embed=discord.Embed(
                    title="🔓 NUEVO AGENTE LIBRE",
                    description=f"**{miembro.display_name}** busca equipo",
                    color=discord.Color.light_grey()
                ))

            await agentes_col.update_one(
                {'discord_id': str(miembro.id)},
                {'$set': {
                    'nombre': miembro.name,
                    'ex_equipo': equipo_dt,
                    'fecha': datetime.now().isoformat(),
                    'avatar_url': str(miembro.display_avatar.url)
                }},
                upsert=True
            )

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            logger.error(f"Error en despedir: {e}", exc_info=True)

    @commands.hybrid_command(name="agentes", description="Ver lista de agentes libres (privado)")
    async def agentes(self, ctx):
        """Muestra la lista de agentes libres. Solo visible para ti."""

        agentes_col = get_collection('agentes_libres')
        agentes_lista = await agentes_col.find({}).to_list(length=200)

        if not agentes_lista:
            embed = discord.Embed(
                title="📭 Sin Agentes Libres",
                description="No hay jugadores registrados como agentes libres actualmente.",
                color=discord.Color.from_rgb(45, 45, 45)
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Construir lista de agentes (usando cache de miembros, sin API calls)
        lista_texto = ""
        miembros_cache = {str(m.id): m for m in ctx.guild.members}

        for agente in agentes_lista:
            discord_id = agente.get('discord_id')
            nombre = agente.get('nombre', 'Desconocido')
            posicion = agente.get('posicion', '?')
            ex_equipo = agente.get('ex_equipo')

            miembro = miembros_cache.get(discord_id)
            nombre_mostrar = f"**{miembro.display_name}**" if miembro else f"**{nombre}**"

            if ex_equipo:
                lista_texto += f"🔹 `{posicion}` {nombre_mostrar} (Ex: {ex_equipo})\n"
            else:
                lista_texto += f"🔹 `{posicion}` {nombre_mostrar}\n"

        embed = discord.Embed(
            title="📋 AGENTES LIBRES",
            description=lista_texto if lista_texto else "Sin agentes",
            color=discord.Color.from_rgb(30, 30, 30)
        )
        embed.set_footer(text=f"Total: {len(agentes_lista)} agentes • Usa /fichar @jugador para ficharlo")

        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="ofertar_club", description="Hacer una oferta monetaria formala a otro Club por un jugador.")
    async def ofertar_club(self, ctx, jugador: discord.Member, monto: int):
        """Negociación de club a club: Oferta privada enviada al DT rival."""
        await ctx.defer(ephemeral=True)

        # 1. Identificar equipo comprador (DT que ejecuta)
        eq_comprador = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                eq_comprador = rol.name
                break

        if not eq_comprador or not any(r.name == config.ROL_DE_DT for r in ctx.author.roles):
            return await ctx.send("❌ Solo los Directores Técnicos (DT) con equipo pueden usar esto.")

        if monto <= 0:
            return await ctx.send("❌ El monto debe ser mayor a $0.")

        # Verificar si su mercado está abierto
        if not await mercado_abierto_para(eq_comprador):
            return await ctx.send("❌ El mercado está cerrado para tu equipo.")

        # 2. Identificar al jugador y su equipo actual (vendedor)
        jugadores_col = get_collection('jugadores')
        jugador_db = await jugadores_col.find_one({'discord_id': str(jugador.id)})
        
        if not jugador_db:
            return await ctx.send(f"❌ **{jugador.display_name}** es agente libre. Usa `/fichar @jugador` para contratarlo, no `/ofertar_club`.")
            
        eq_vendedor = jugador_db.get('equipo')
        
        if eq_vendedor == eq_comprador:
            return await ctx.send("❌ No puedes ofertar por un jugador de tu propio equipo. Usa sentido común.")

        # VALIDACIÓN DE RANGO DE PRECIO (75% - 200% del valor de mercado)
        validacion = await validateOffer(str(jugador.id), monto)
        if not validacion['valid']:
            # Enviar mensaje con información detallada del rango permitido
            embed_error = discord.Embed(
                title="⚠️ Validación de Oferta Fallida",
                description=validacion['message'],
                color=discord.Color.orange()
            )
            embed_error.add_field(
                name="📊 Información del Jugador",
                value=f"**Valor de mercado:** `${validacion['market_value']:,}`\n"
                      f"**Mínimo permitido (75%):** `${validacion['min_allowed']:,}`\n"
                      f"**Máximo permitido (200%):** `${validacion['max_allowed']:,}`",
                inline=False
            )
            embed_error.add_field(
                name="💰 Tu oferta",
                value=f"`${monto:,}`",
                inline=True
            )
            return await ctx.send(embed=embed_error, ephemeral=True)

        # 3. Revisar presupuesto del comprador
        equipos_col = get_collection('equipos')
        db_comprador = await equipos_col.find_one({'nombre': eq_comprador})
        if not db_comprador:
             return await ctx.send("❌ Error: Tu equipo no existe en la base de datos financiera.")
             
        presupuesto_comprador = db_comprador.get('presupuesto', 0)
        if presupuesto_comprador < monto:
            return await ctx.send(f"❌ **Fondos Insuficientes.** Tienes `${presupuesto_comprador:,}` y estás ofreciendo `${monto:,}`.")

        # 4. Buscar al DT Vendedor en Discord
        dt_vendedor_member = None
        rol_vendedor = discord.utils.get(ctx.guild.roles, name=eq_vendedor)
        if rol_vendedor:
            for m in rol_vendedor.members:
                if any(r.name == config.ROL_DE_DT for r in m.roles):
                    dt_vendedor_member = m
                    break
                    
        if not dt_vendedor_member:
            # Fallback a la base de datos de equipos de capitanes viejos
            if 'dt_discord_id' in db_comprador: # solo para testing en viejas estructuras
                pass
            return await ctx.send(f"❌ No se pudo encontrar al DT actual del **{eq_vendedor}** para enviarle la oferta.")

        # 5. Enviar el DM Intersctivo al DT Vendedor
        view = ConfirmacionTraspasoView(
            self.bot, 
            str(ctx.author.id), 
            str(dt_vendedor_member.id), 
            jugador, 
            eq_comprador, 
            eq_vendedor, 
            monto
        )
        
        embed_dm = discord.Embed(
            title="💼 OFERTA DE TRASPASO ENTRANTE",
            description=(
                f"El DT **{ctx.author.name}** del **{eq_comprador}** ha presentado una oferta formal.\n\n"
                f"🎯 **Objetivo:** {jugador.mention}\n"
                f"💰 **Cifra Ofertada:** `${monto:,}`\n\n"
                f"¿Aceptas vender a este jugador y recibir los fondos?\n*Rechaza el acuerdo mediante el botón rojo.*"
            ),
            color=discord.Color.dark_purple()
        )
        embed_dm.set_thumbnail(url=ctx.author.display_avatar.url)

        try:
            await dt_vendedor_member.send(embed=embed_dm, view=view)
            
            # Anuncio Rumor
            canal_noticias = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_FICHAJES)
            if canal_noticias:
                await canal_noticias.send(f"👀 📰 **[RUMOR]** Acaba de llegar una oferta a las oficinas del **{eq_vendedor}**... ¿Dejarán salir a {jugador.mention}?")
                
            await ctx.send(f"✅ ¡Oferta de `${monto:,}` enviada exitosamente por DM al DT del **{eq_vendedor}**!")
            logger.info(f"💼 Oferta Club a Club: {eq_comprador} ofrece ${monto} a {eq_vendedor} por {jugador.name}")
            
        except discord.Forbidden:
            await ctx.send(f"❌ El DT del **{eq_vendedor}** ({dt_vendedor_member.mention}) tiene los Mensajes Directos cerrados de bot. Pídele que los abra para enviarle propuestas.")
        except Exception as e:
            await ctx.send(f"❌ Ocurrió un error misterioso enviando el DM: {e}")


    @commands.hybrid_command(name="clausulazo", description="Robar a un jugador pagando su cláusula ignorando a su DT dueño.")
    async def clausulazo(self, ctx, jugador: discord.Member, monto: int):
        """Paga la cláusula por el jugador. No se avisa a su DT. El jugador tiene la decisión final vía DM."""
        await ctx.defer(ephemeral=False) # Hacemos esto público, ya que es un "bomba"

        # 1. Identificar equipo comprador (DT que ejecuta)
        eq_comprador = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                eq_comprador = rol.name
                break

        if not eq_comprador or not any(r.name == config.ROL_DE_DT for r in ctx.author.roles):
            return await ctx.send("❌ Solo los Directores Técnicos (DT) con equipo pueden usar este comando.")

        if monto <= 0:
            return await ctx.send("❌ El monto de la cláusula debe ser mayor a $0.")

        # Verificar si su mercado está abierto
        if not await mercado_abierto_para(eq_comprador):
            return await ctx.send("❌ El mercado está cerrado para tu equipo.")

        # 2. Identificar al jugador y su equipo actual (vendedor)
        jugadores_col = get_collection('jugadores')
        jugador_db = await jugadores_col.find_one({'discord_id': str(jugador.id)})
        
        if not jugador_db:
            return await ctx.send(f"❌ ERROR: **{jugador.display_name}** es agente libre. Usa `/fichar @jugador`.")
            
        eq_vendedor = jugador_db.get('equipo')
        
        if eq_vendedor == eq_comprador:
            return await ctx.send("❌ ¿Vas a pagar la cláusula de tu propio jugador? Usa la cabeza.")

        # 3. Revisar presupuesto del comprador
        equipos_col = get_collection('equipos')
        db_comprador = await equipos_col.find_one({'nombre': eq_comprador})
        if not db_comprador:
             return await ctx.send("❌ Error: Tu equipo no existe en la DB financiera.")
             
        presupuesto_comprador = db_comprador.get('presupuesto', 0)
        if presupuesto_comprador < monto:
            return await ctx.send(f"❌ **OFERTA RECHAZADA.** Tienes `${presupuesto_comprador:,}` y la cláusula a pagar es `${monto:,}`.")

        # 4. Enviar el DM DIRECTO AL JUGADOR
        view = ConfirmacionClausulazoView(
            self.bot, 
            str(ctx.author.id), 
            jugador, 
            eq_comprador, 
            eq_vendedor, 
            monto
        )
        
        embed_dm = discord.Embed(
            title="💣 ¡TÚ CLAÚSULA HA SIDO PAGADA!",
            description=(
                f"El DT {ctx.author.mention} del **{eq_comprador}** acaba de tirar la puerta abajo y "
                f"ha depositado `${monto:,}` para robarte del **{eq_vendedor}**.\n\n"
                f"Tu actual DT no puede hacer nada para evitarlo. El control total es tuyo.\n"
                f"¿Traicionas a tu actual club y te marchas a tu nuevo destino de lujo, o te quedas y demuestras amor por los colores?"
            ),
            color=discord.Color.from_rgb(255, 69, 0)
        )
        embed_dm.set_thumbnail(url=ctx.author.display_avatar.url)
        embed_dm.set_footer(text="Selecciona un botón para decidir tu futuro.")

        try:
            await jugador.send(embed=embed_dm, view=view)
            
            # Anuncio Rumor Bomba al canal
            canal_noticias = discord.utils.get(ctx.guild.text_channels, name=config.CANAL_FICHAJES)
            mensaje_publico = f"🚨 **[CLAUSULAZO]** ¡El **{eq_comprador}** ha depositado `${monto:,}` en las oficinas para arrancar a **{jugador.mention}** del **{eq_vendedor}**!\n*El control ahora lo tiene el jugador por Mensaje Directo. ¿Romperá su contrato?*"
            if canal_noticias:
                await canal_noticias.send(mensaje_publico)
                # Confirmación al DT
                await ctx.send(f"✅ ¡Cláusula pagada! Esperando la decisión de {jugador.mention}.")
            else:
                await ctx.send(mensaje_publico)
                
            logger.info(f"💣 Clausulazo: {eq_comprador} paga ${monto} por {jugador.name} ({eq_vendedor})")
            
        except discord.Forbidden:
            await ctx.send(f"❌ ¡Operación fallida! **{jugador.mention}** tiene sus Mensajes Directos cerrados de Servidor. Tiene que habilitarlos para poder enviarle el maletín millonario.")
            
async def setup(bot):
    await bot.add_cog(FichajesCog(bot))
