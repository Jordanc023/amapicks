"""
fichajes.py - Cog para sistema de fichajes
Comandos: /fichar, /despedir
Ofertas persistentes en MongoDB (no se pierden al reiniciar)
"""
import discord
from logger import get_module_logger

logger = get_module_logger("fichajes")
import asyncio
from bson import ObjectId
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime

import config
from database import (
    get_collection, mercado_abierto_para, contar_jugadores_equipo, log_action,
    crear_oferta_pendiente, eliminar_oferta_pendiente,
    tiene_oferta_pendiente, tiene_oferta_de_otro_dt
)

# Helper para obtener canal por ID
def get_channel_by_id(guild, channel_id):
    """Obtiene un canal por su ID."""
    return guild.get_channel(int(channel_id)) if channel_id else None

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
    
    # Usar cláusula como market_value, o precio si no existe cláusula o es 0
    market_value = jugador.get('clausula') or jugador.get('precio') or 0
    
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


def calcular_costo_cesion(pj: int, market_value: int) -> int:
    """Calcula el costo de cesión según reglas del negocio."""
    factors = {
        3: 0.15,
        5: 0.25,
        10: 0.50,
    }
    if pj not in factors:
        raise ValueError("PJ inválido para cesión")

    return int(market_value * factors[pj])


# ============================================
# FUNCIÓN STANDALONE: EJECUTAR TRASPASO ENTRE CLUBES
# ============================================

async def ejecutar_traspaso_clubes(bot, interaction, dt_comprador_id, dt_vendedor_id,
                                    jugador, equipo_comprador, equipo_vendedor, monto):
    """
    Ejecuta un traspaso entre clubes: actualiza roles en Discord,
    mueve al jugador en MongoDB y anuncia en el canal de fichajes.
    
    Se usa tanto para traspasos normales como para clausulazos.
    En clausulazos, dt_vendedor_id = "clara_traicion".
    """
    try:
        jugadores_col = get_collection('jugadores')
        equipos_col = get_collection('equipos')

        # Resolver el guild (las interacciones de DM no tienen guild)
        guild = interaction.guild
        if not guild:
            for g in bot.guilds:
                if g.get_member(jugador.id):
                    guild = g
                    break
        if not guild:
            logger.error("No se encontró el servidor para ejecutar el traspaso.")
            return

        # Obtener miembro en el guild
        miembro = guild.get_member(jugador.id)
        if not miembro:
            try:
                miembro = await guild.fetch_member(jugador.id)
            except Exception:
                logger.error(f"No se pudo encontrar al jugador {jugador.id} en el servidor.")
                return

        # 1. Actualizar BD: mover jugador de equipo
        await jugadores_col.update_one(
            {'discord_id': str(jugador.id)},
            {'$set': {
                'equipo': equipo_comprador,
                'fecha_fichaje': datetime.now().isoformat()
            }}
        )

        # 2. Actualizar presupuestos
        await equipos_col.update_one(
            {'nombre': equipo_comprador},
            {'$inc': {'presupuesto': -monto}}
        )
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
        es_clausulazo = (dt_vendedor_id == "clara_traicion")
        canal_noticias = bot.get_channel(config.CANAL_FICHAJES_ID)

        if canal_noticias:
            titulo = "💣 ¡CLAUSULAZO COMPLETADO!" if es_clausulazo else "🤝 TRASPASO OFICIAL"
            color = discord.Color.from_rgb(255, 69, 0) if es_clausulazo else discord.Color.brand_green()

            embed = discord.Embed(
                title=titulo,
                description=(
                    f"**{miembro.mention}** ha sido transferido del **{equipo_vendedor}** "
                    f"al **{equipo_comprador}** por `${monto:,}`."
                ),
                color=color
            )
            embed.set_thumbnail(url=miembro.display_avatar.url)
            embed.set_footer(text=f"Traspaso completado • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            await canal_noticias.send(embed=embed)

        # 5. Notificar al DT comprador
        try:
            comprador = await bot.fetch_user(int(dt_comprador_id))
            if comprador:
                await comprador.send(
                    f"✅ ¡Traspaso completado! **{jugador.name}** ahora es jugador "
                    f"de tu equipo **{equipo_comprador}**."
                )
        except Exception as e:
            logger.error(f"No se pudo notificar al DT comprador: {e}")

        # 6. Log de auditoría
        await log_action(
            guild_id=str(guild.id),
            action_type=config.AuditAction.FICHAJE,
            actor_id=str(dt_comprador_id),
            actor_name=f"DT {equipo_comprador}",
            target_id=str(jugador.id),
            target_name=jugador.name,
            details={
                'tipo': 'clausulazo' if es_clausulazo else 'traspaso',
                'equipo_origen': equipo_vendedor,
                'equipo_destino': equipo_comprador,
                'monto': monto
            }
        )

        # 7. Limpiar oferta pendiente
        await eliminar_oferta_pendiente(str(dt_comprador_id), str(jugador.id))

        logger.info(
            f"{'💣 Clausulazo' if es_clausulazo else '🤝 Traspaso'}: "
            f"{jugador.name} → {equipo_comprador} (${monto:,})"
        )

    except Exception as e:
        logger.error(f"Error ejecutando traspaso entre clubes: {e}", exc_info=True)


# ============================================
# VISTA: CONFIRMACIÓN DE TRASPASO (DT→DT)
# ============================================

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

        # Limpiar oferta pendiente
        await eliminar_oferta_pendiente(str(self.dt_comprador_id), str(self.jugador.id))

        # Anuncio en canal de fichajes
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
        if canal_noticias:
            embed_noticia = discord.Embed(
                title="❌ OFERTA RECHAZADA",
                description=(
                    f"Las negociaciones se han roto.\n"
                    f"El **{self.equipo_vendedor}** ha rechazado la oferta de `${self.monto:,}` "
                    f"del **{self.equipo_comprador}** por **{self.jugador.name}**.\n\n"
                    f"*El contrato ha sido retirado de la mesa.*"
                ),
                color=discord.Color.brand_red()
            )
            embed_noticia.set_footer(text="El DT declinó la oferta")
            await canal_noticias.send(embed=embed_noticia)

    async def on_timeout(self):
        """Expiración del traspaso club-a-club (24h)."""
        try:
            await eliminar_oferta_pendiente(str(self.dt_comprador_id), str(self.jugador.id))

            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            if canal_noticias:
                embed = discord.Embed(
                    title="⏱️ OFERTA EXPIRADA",
                    description=(
                        f"El plazo de negociación ha vencido.\n"
                        f"La oferta del **{self.equipo_comprador}** por **{self.jugador.name}** "
                        f"del **{self.equipo_vendedor}** ha expirado.\n\n"
                        f"*El contrato ha sido retirado de la mesa.*"
                    ),
                    color=discord.Color.dark_grey()
                )
                await canal_noticias.send(embed=embed)
        except Exception as e:
            logger.warning(f"Error al procesar expiración de traspaso: {e}")


# ============================================
# VISTA: CONFIRMACIÓN DE CLAUSULAZO (Jugador decide)
# ============================================

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

        # Ejecutar traspaso con "clara_traicion" como id vendedor (el DT vendedor no interviene)
        await ejecutar_traspaso_clubes(
            self.bot, interaction, self.dt_comprador_id, "clara_traicion",
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
        except Exception:
            pass

        # Limpiar oferta pendiente
        await eliminar_oferta_pendiente(str(self.dt_comprador_id), str(self.jugador.id))

        # Anunciar el rechazo en el Canal Fichajes
        guild = interaction.guild
        if not guild:
            for g in self.bot.guilds:
                if g.get_member(self.jugador.id):
                    guild = g
                    break
        if guild:
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
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

    async def on_timeout(self):
        """Expiración del clausulazo (24h)."""
        try:
            await eliminar_oferta_pendiente(str(self.dt_comprador_id), str(self.jugador.id))

            # Buscar guild para anunciar
            guild = None
            for g in self.bot.guilds:
                if g.get_member(self.jugador.id):
                    guild = g
                    break

            if guild:
                canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
                if canal_noticias:
                    embed = discord.Embed(
                        title="⏱️ CLAUSULAZO EXPIRADO",
                        description=(
                            f"El plazo para decidir ha vencido.\n"
                            f"**{self.jugador.name}** no respondió al clausulazo del **{self.equipo_comprador}**.\n\n"
                            f"*El dinero de la cláusula ha sido devuelto.*"
                        ),
                        color=discord.Color.dark_grey()
                    )
                    await canal_noticias.send(embed=embed)
        except Exception as e:
            logger.warning(f"Error al procesar expiración de clausulazo: {e}")


# ============================================
# VISTA: OFERTA DE FICHAJE (Agente Libre)
# ============================================

class OfertaFichajeView(View):
    """Vista interactiva enviada por DM a un agente libre para aceptar/rechazar una oferta de fichaje."""

    def __init__(self, bot, ctx, jugador: discord.Member, equipo_dt: str):
        super().__init__(timeout=600)  # 10 minutos para agentes libres
        self.bot = bot
        self.ctx = ctx
        self.jugador = jugador
        self.equipo_dt = equipo_dt
        self.respondido = False

    @discord.ui.button(label="✅ Firmar Contrato", style=discord.ButtonStyle.green)
    async def aceptar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.jugador.id:
            await interaction.response.send_message("❌ Esta oferta no es para ti.", ephemeral=True)
            return

        if self.respondido:
            await interaction.response.send_message("⚠️ Ya respondiste a esta oferta.", ephemeral=True)
            return

        await interaction.response.defer()
        self.respondido = True

        # Desactivar botones
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = "✅ CONTRATO FIRMADO"
        embed.set_footer(text="Bienvenido al club.")
        await interaction.message.edit(embed=embed, view=self)

        # Ejecutar fichaje del agente libre
        try:
            guild = self.ctx.guild
            miembro = guild.get_member(self.jugador.id)
            if not miembro:
                miembro = await guild.fetch_member(self.jugador.id)

            jugadores_col = get_collection('jugadores')
            agentes_col = get_collection('agentes_libres')

            # Actualizar BD: agregar jugador al equipo
            await jugadores_col.update_one(
                {'discord_id': str(self.jugador.id)},
                {'$set': {
                    'discord_id': str(self.jugador.id),
                    'nombre': self.jugador.name,
                    'equipo': self.equipo_dt,
                    'avatar_url': str(self.jugador.display_avatar.url),
                    'fecha_fichaje': datetime.now().isoformat()
                }},
                upsert=True
            )

            # Quitar de agentes libres
            await agentes_col.delete_one({'discord_id': str(self.jugador.id)})

            # Roles en Discord
            rol_equipo = discord.utils.get(guild.roles, name=self.equipo_dt)
            rol_agente = discord.utils.get(guild.roles, name=config.ROL_AGENTE_LIBRE)

            if rol_agente and rol_agente in miembro.roles:
                await miembro.remove_roles(rol_agente)
            if rol_equipo:
                await miembro.add_roles(rol_equipo)

            cantidad_jugadores = await contar_jugadores_equipo(self.equipo_dt)

            # Limpiar oferta pendiente
            await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

            # Anuncio en canal de fichajes
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)

            embed_noticia = discord.Embed(
                title="📸 PRESENTACIÓN OFICIAL",
                description=(
                    f"**{miembro.display_name}** posa con la camiseta de "
                    f"**{self.equipo_dt}** tras firmar su nuevo contrato."
                ),
                color=discord.Color.gold()
            )
            embed_noticia.set_author(name="✅ TRASPASO CONFIRMADO", icon_url=miembro.display_avatar.url)
            embed_noticia.add_field(name="👤 Jugador", value=miembro.mention, inline=True)
            embed_noticia.add_field(name="🛡️ Equipo", value=f"**{self.equipo_dt}**", inline=True)
            embed_noticia.add_field(
                name="📊 Plantilla",
                value=f"`{cantidad_jugadores}/{config.LIMITE_PLANTILLA}`",
                inline=True
            )
            embed_noticia.set_thumbnail(url=miembro.display_avatar.url)
            embed_noticia.set_footer(text=f"Operación gestionada por el DT: {self.ctx.author.display_name}")

            if canal_noticias:
                await canal_noticias.send(embed=embed_noticia)

            # Log de auditoría
            await log_action(
                guild_id=str(guild.id),
                action_type=config.AuditAction.FICHAJE,
                actor_id=str(self.ctx.author.id),
                actor_name=self.ctx.author.name,
                target_id=str(self.jugador.id),
                target_name=self.jugador.name,
                details={'equipo': self.equipo_dt, 'tipo': 'agente_libre'}
            )

            logger.info(f"✅ Fichaje: {self.jugador.name} → {self.equipo_dt}")

        except Exception as e:
            logger.error(f"Error ejecutando fichaje de agente libre: {e}", exc_info=True)
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            if canal_noticias:
                await canal_noticias.send(f"❌ Error procesando el fichaje de {self.jugador.mention}: {e}")

    @discord.ui.button(label="❌ Rechazar Oferta", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.jugador.id:
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
        embed.title = "❌ OFERTA RECHAZADA"
        embed.set_footer(text="Has declinado la oferta.")
        await interaction.message.edit(embed=embed, view=self)

        # Limpiar oferta pendiente
        await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

        # Anuncio en canal de fichajes
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
        if canal_noticias:
            embed_noticia = discord.Embed(
                title="❌ OFERTA RECHAZADA",
                description=(
                    f"Las negociaciones se han roto.\n"
                    f"**{self.jugador.mention}** ha rechazado formalmente la oferta de **{self.equipo_dt}**.\n\n"
                    f"*El contrato ha sido retirado de la mesa.*"
                ),
                color=discord.Color.brand_red()
            )
            embed_noticia.set_footer(text="El jugador declinó la oferta")
            await canal_noticias.send(embed=embed_noticia)

        logger.info(f"❌ Oferta rechazada: {self.jugador.name} declinó {self.equipo_dt}")

    async def on_timeout(self):
        """Expiración de oferta a agente libre (10 min)."""
        try:
            await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            if canal_noticias:
                expire_embed = discord.Embed(
                    title="⏱️ OFERTA EXPIRADA",
                    description=(
                        f"El plazo de negociación ha vencido.\n"
                        f"**{self.jugador.display_name}** no respondió a tiempo "
                        f"a la oferta de **{self.equipo_dt}**.\n\n"
                        f"*El contrato ha sido retirado de la mesa.*"
                    ),
                    color=discord.Color.dark_grey()
                )
                await canal_noticias.send(embed=expire_embed)
        except Exception as e:
            logger.warning(f"Error al procesar expiración de oferta: {e}")


# ============================================
# COG PRINCIPAL: FICHAJES
# ============================================

class FichajesCog(commands.Cog):
    """Cog para sistema de fichajes: /fichar, /despedir."""

    def __init__(self, bot):
        self.bot = bot

    # ============================================
    # COMANDO: /fichar
    # ============================================

    @commands.hybrid_command(name="fichar", description="Enviar oferta de fichaje a un jugador")
    @app_commands.describe(
        jugador="El jugador que quieres fichar",
        monto="Monto de la oferta (obligatorio si el jugador pertenece a otro equipo)"
    )
    async def fichar(self, ctx, jugador: discord.Member, monto: int = None):
        """
        Envía una oferta de fichaje a un jugador.
        
        Tres escenarios posibles:
        A) Agente Libre → oferta directa al jugador (sin monto)
        B) Jugador en otro equipo → oferta al DT del equipo vendedor (con monto)
        C) Clausulazo → monto >= cláusula, el jugador decide (no el DT)
        """
        await ctx.defer()

        # 1. Verificar que sea DT
        es_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not es_dt:
            await ctx.followup.send("❌ Solo los **Directores Técnicos** pueden usar este comando.")
            return

        # 2. Verificar canal de ofertas
        if ctx.channel.id != config.CANAL_OFERTAS_ID:
            canal_ofertas = self.bot.get_channel(config.CANAL_OFERTAS_ID)
            if canal_ofertas:
                await ctx.followup.send(f"❌ Este comando solo puede usarse en {canal_ofertas.mention}.", delete_after=10)
            else:
                await ctx.followup.send("❌ Canal de ofertas no configurado.", delete_after=10)
            return

        # 3. Encontrar equipo del DT
        equipo_dt = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                break

        if not equipo_dt:
            await ctx.followup.send("❌ No se encontró tu equipo.")
            return

        # 4. Verificar mercado abierto para este equipo
        mercado_ok = await mercado_abierto_para(equipo_dt)
        if not mercado_ok:
            await ctx.followup.send("❌ El mercado de fichajes está **cerrado**.")
            return

        # 5. Validaciones de jugador
        if jugador.id == ctx.author.id:
            await ctx.followup.send("❌ No puedes ficharte a ti mismo.")
            return

        if jugador.bot:
            await ctx.followup.send("❌ No puedes fichar a un bot.")
            return

        # 6. Verificar ofertas duplicadas
        if await tiene_oferta_pendiente(str(ctx.author.id), str(jugador.id)):
            await ctx.followup.send("⚠️ Ya tienes una oferta pendiente con este jugador.")
            return

        otro_equipo = await tiene_oferta_de_otro_dt(str(jugador.id), str(ctx.author.id))
        if otro_equipo:
            await ctx.followup.send(f"⚠️ Otro equipo (**{otro_equipo}**) ya tiene una oferta pendiente con este jugador.")
            return

        # 7. Determinar tipo de fichaje
        es_agente_libre = any(rol.name == config.ROL_AGENTE_LIBRE for rol in jugador.roles)
        equipo_jugador = None
        for rol in jugador.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_jugador = rol.name
                break

        # Verificar que no sea del mismo equipo
        if equipo_jugador == equipo_dt:
            await ctx.followup.send("❌ Ese jugador ya pertenece a tu equipo.")
            return

        # 8. Verificar plantilla no llena
        cantidad = await contar_jugadores_equipo(equipo_dt)
        if cantidad >= config.LIMITE_PLANTILLA:
            await ctx.followup.send(f"❌ Tu plantilla está llena ({cantidad}/{config.LIMITE_PLANTILLA}).")
            return

        # ===== CASO A: AGENTE LIBRE (sin monto necesario) =====
        if es_agente_libre or not equipo_jugador:
            # Crear oferta pendiente con TTL de 10 minutos
            await crear_oferta_pendiente(str(ctx.author.id), str(jugador.id), equipo_dt, expira_minutos=10)

            # Crear View y enviar DM al jugador
            view = OfertaFichajeView(self.bot, ctx, jugador, equipo_dt)

            embed_dm = discord.Embed(
                title="� OFERTA DE FICHAJE",
                description=(
                    f"¡El **{equipo_dt}** quiere ficharte!\n\n"
                    f"👤 **DT:** {ctx.author.display_name}\n"
                    f"🛡️ **Equipo:** {equipo_dt}\n\n"
                    f"Tienes **10 minutos** para responder."
                ),
                color=discord.Color.blue()
            )
            embed_dm.set_thumbnail(url=ctx.author.display_avatar.url)
            embed_dm.set_footer(text="Usa los botones para responder")

            try:
                await jugador.send(embed=embed_dm, view=view)

                # Obtener info del equipo comprador para el embed
                equipos_col = get_collection('equipos')
                equipo_db = await equipos_col.find_one({'nombre': equipo_dt})
                
                color_equipo = discord.Color.blue()
                escudo_url = None
                if equipo_db:
                    color_hex = equipo_db.get('color', '#3498db')
                    try:
                        color_equipo = int(color_hex.lstrip('#'), 16)
                    except ValueError:
                        color_equipo = discord.Color.blue()
                    escudo_url = equipo_db.get('escudo_url')

                # Embed profesional en canal de fichajes
                canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
                if canal_noticias:
                    embed_canal = discord.Embed(
                        title="📋 OFERTA DE FICHAJE",
                        description=(
                            f"El **{equipo_dt}** ha presentado una oferta formal por **{jugador.mention}**\n\n"
                            f"👤 **Agente Libre**\n"
                            f"⏱️ **Tiempo límite:** 10 minutos\n"
                            f"💬 **Estado:** Esperando respuesta del jugador"
                        ),
                        color=color_equipo,
                        timestamp=datetime.now()
                    )
                    embed_canal.set_author(
                        name=f"Oficial {equipo_dt}",
                        icon_url=escudo_url if escudo_url else ctx.author.display_avatar.url
                    )
                    embed_canal.set_thumbnail(url=jugador.display_avatar.url)
                    embed_canal.set_footer(
                        text=f"DT: {ctx.author.display_name}",
                        icon_url=ctx.author.display_avatar.url
                    )
                    await canal_noticias.send(embed=embed_canal)

                await ctx.followup.send(
                    f"✅ Oferta enviada a **{jugador.display_name}** por DM. "
                    f"Tiene 10 minutos para responder."
                )
                logger.info(f"📩 Oferta: {equipo_dt} → {jugador.name} (Agente Libre)")

            except discord.Forbidden:
                await eliminar_oferta_pendiente(str(ctx.author.id), str(jugador.id))
                await ctx.followup.send(
                    f"❌ No se pudo enviar DM a **{jugador.display_name}**. "
                    f"Debe tener los DMs abiertos."
                )

            return

        # ===== CASO B y C: JUGADOR EN OTRO EQUIPO (requiere monto) =====
        if not monto:
            await ctx.followup.send(
                "❌ Debes especificar un monto para fichar a un jugador de otro equipo.\n"
                "Uso: `/fichar @Jugador 5000000`"
            )
            return

        if monto <= 0:
            await ctx.followup.send("❌ El monto debe ser un número positivo.")
            return

        # Validar rango de oferta (75%-200% del valor de mercado)
        validacion = await validateOffer(str(jugador.id), monto)
        if not validacion['valid']:
            await ctx.followup.send(validacion['message'])
            return

        # Verificar presupuesto del comprador
        equipos_col = get_collection('equipos')
        equipo_comprador_doc = await equipos_col.find_one({'nombre': equipo_dt})
        presupuesto = equipo_comprador_doc.get('presupuesto', 0) if equipo_comprador_doc else 0

        if monto > presupuesto:
            await ctx.followup.send(
                f"❌ **Fondos insuficientes.** Tu presupuesto es `${presupuesto:,}` "
                f"y la oferta es `${monto:,}`."
            )
            return

        eq_comprador = equipo_dt
        eq_vendedor = equipo_jugador
        market_value = validacion['market_value']

        # Registrar oferta pendiente (24h para club-a-club)
        await crear_oferta_pendiente(str(ctx.author.id), str(jugador.id), equipo_dt, expira_minutos=1440)

        # Verificar cláusula para determinar si es clausulazo
        jugadores_col = get_collection('jugadores')
        jugador_db = await jugadores_col.find_one({'discord_id': str(jugador.id)})
        clausula = jugador_db.get('clausula', 0) if jugador_db else 0

        if clausula > 0 and monto >= clausula:
            # ===== CASO C: CLAUSULAZO =====
            view = ConfirmacionClausulazoView(
                self.bot, str(ctx.author.id), jugador, eq_comprador, eq_vendedor, monto
            )

            embed_dm = discord.Embed(
                title="💣 CLAUSULAZO ACTIVADO",
                description=(
                    f"El **{eq_comprador}** ha pagado tu cláusula de rescisión.\n\n"
                    f"💰 **Monto:** `${monto:,}`\n"
                    f"📊 **Tu cláusula:** `${clausula:,}`\n"
                    f"🛡️ **Tu equipo actual:** {eq_vendedor}\n\n"
                    f"**¿Quieres abandonar tu club y fichar por el {eq_comprador}?**\n"
                    f"Esta decisión es tuya. Tu DT no puede impedirlo."
                ),
                color=discord.Color.from_rgb(255, 69, 0)
            )
            embed_dm.set_footer(text="Tienes 24 horas para decidir")

            try:
                await jugador.send(embed=embed_dm, view=view)

                # Embed profesional en canal de fichajes - CLAUSULAZO
                canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
                if canal_noticias:
                    equipo_comprador_db = await equipos_col.find_one({'nombre': eq_comprador})
                    
                    color_clausula = discord.Color.from_rgb(255, 69, 0)
                    escudo_comprador = None
                    if equipo_comprador_db:
                        color_hex = equipo_comprador_db.get('color', '#FF4500')
                        try:
                            color_clausula = int(color_hex.lstrip('#'), 16)
                        except ValueError:
                            color_clausula = discord.Color.from_rgb(255, 69, 0)
                        escudo_comprador = equipo_comprador_db.get('escudo_url')

                    embed_canal = discord.Embed(
                        title="💣 CLAUSULAZO ACTIVADO",
                        description=(
                            f"¡Bomba en el mercado! El **{eq_comprador}** ha ejecutado la cláusula de rescisión\n"
                            f"de **{jugador.mention}** por **${monto:,}**"
                        ),
                        color=color_clausula,
                        timestamp=datetime.now()
                    )
                    embed_canal.set_author(
                        name=f"Oficial {eq_comprador}",
                        icon_url=escudo_comprador if escudo_comprador else ctx.author.display_avatar.url
                    )
                    embed_canal.set_thumbnail(url=jugador.display_avatar.url)
                    embed_canal.add_field(
                        name="📊 Detalles",
                        value=(
                            f"**Jugador:** {jugador.display_name}\n"
                            f"**Equipo origen:** {eq_vendedor}\n"
                            f"**Cláusula:** ${clausula:,}\n"
                            f"**Decisión:** En manos del jugador (24h)"
                        ),
                        inline=False
                    )
                    embed_canal.set_footer(
                        text=f"DT: {ctx.author.display_name} • Oferta irrevocable",
                        icon_url=ctx.author.display_avatar.url
                    )
                    await canal_noticias.send(embed=embed_canal)

                await ctx.followup.send(f"✅ ¡Cláusula pagada! Esperando la decisión de {jugador.mention}.")
                logger.info(f"💣 Clausulazo: {eq_comprador} paga ${monto} por {jugador.name} ({eq_vendedor})")

            except discord.Forbidden:
                await eliminar_oferta_pendiente(str(ctx.author.id), str(jugador.id))
                await ctx.followup.send(
                    f"❌ ¡Operación fallida! **{jugador.mention}** tiene sus Mensajes Directos cerrados "
                    f"de Servidor. Tiene que habilitarlos para poder enviarle el maletín millonario."
                )
        else:
            # ===== CASO B: TRASPASO CLUB A CLUB =====
            # Buscar DT del equipo vendedor
            dt_vendedor_member = None
            rol_equipo_vendedor = discord.utils.get(ctx.guild.roles, name=eq_vendedor)
            if rol_equipo_vendedor:
                for miembro in rol_equipo_vendedor.members:
                    if any(r.name == config.ROL_DE_DT for r in miembro.roles):
                        dt_vendedor_member = miembro
                        break

            if not dt_vendedor_member:
                await eliminar_oferta_pendiente(str(ctx.author.id), str(jugador.id))
                await ctx.followup.send(f"❌ No se encontró al DT del **{eq_vendedor}** en el servidor.")
                return

            view = ConfirmacionTraspasoView(
                self.bot, str(ctx.author.id), str(dt_vendedor_member.id),
                jugador, eq_comprador, eq_vendedor, monto
            )

            embed_dm = discord.Embed(
                title="💼 OFERTA DE TRASPASO",
                description=(
                    f"El **{eq_comprador}** quiere comprar a **{jugador.name}** de tu equipo.\n\n"
                    f"💰 **Monto ofrecido:** `${monto:,}`\n"
                    f"📊 **Valor de mercado:** `${market_value:,}`\n"
                    f"👤 **Jugador:** {jugador.mention}\n\n"
                    f"¿Aceptas vender a tu jugador?"
                ),
                color=discord.Color.blue()
            )
            embed_dm.set_thumbnail(url=jugador.display_avatar.url)
            embed_dm.set_footer(text="Tienes 24 horas para decidir")

            try:
                await dt_vendedor_member.send(embed=embed_dm, view=view)

                # Embed profesional en canal de fichajes - TRASPASO
                canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
                if canal_noticias:
                    equipo_comprador_db = await equipos_col.find_one({'nombre': eq_comprador})
                    
                    color_traspaso = discord.Color.blue()
                    escudo_comprador = None
                    if equipo_comprador_db:
                        color_hex = equipo_comprador_db.get('color', '#3498db')
                        try:
                            color_traspaso = int(color_hex.lstrip('#'), 16)
                        except ValueError:
                            color_traspaso = discord.Color.blue()
                        escudo_comprador = equipo_comprador_db.get('escudo_url')

                    embed_canal = discord.Embed(
                        title="💼 OFERTA DE TRASPASO",
                        description=(
                            f"Negociaciones en curso: El **{eq_comprador}** ha presentado\n"
                            f"una oferta formal por **{jugador.mention}**"
                        ),
                        color=color_traspaso,
                        timestamp=datetime.now()
                    )
                    embed_canal.set_author(
                        name=f"Oficial {eq_comprador}",
                        icon_url=escudo_comprador if escudo_comprador else ctx.author.display_avatar.url
                    )
                    embed_canal.set_thumbnail(url=jugador.display_avatar.url)
                    embed_canal.add_field(
                        name="💰 Oferta",
                        value=f"**${monto:,}**\nValor de mercado: ${market_value:,}",
                        inline=True
                    )
                    embed_canal.add_field(
                        name="🛡️ Equipos",
                        value=f"**Origen:** {eq_vendedor}\n**Destino:** {eq_comprador}",
                        inline=True
                    )
                    embed_canal.add_field(
                        name="⏱️ Estado",
                        value=f"Esperando respuesta del DT de **{eq_vendedor}** (24h)",
                        inline=False
                    )
                    embed_canal.set_footer(
                        text=f"DT Ofertante: {ctx.author.display_name}",
                        icon_url=ctx.author.display_avatar.url
                    )
                    await canal_noticias.send(embed=embed_canal)

                await ctx.followup.send(f"✅ ¡Oferta de `${monto:,}` enviada exitosamente por DM al DT del **{eq_vendedor}**!")
                logger.info(f"💼 Oferta Club a Club: {eq_comprador} ofrece ${monto} a {eq_vendedor} por {jugador.name}")

            except discord.Forbidden:
                await eliminar_oferta_pendiente(str(ctx.author.id), str(jugador.id))
                await ctx.followup.send(f"❌ No se pudo enviar DM al DT del {eq_vendedor}.")

    # ============================================
    # COMANDO: /despedir
    # ============================================

    @commands.hybrid_command(name="despedir", description="Despedir a un jugador de tu equipo")
    @app_commands.describe(jugador="El jugador que quieres despedir")
    async def despedir(self, ctx, jugador: discord.Member):
        """Despide a un jugador de tu equipo (solo DTs)."""
        await ctx.defer()

        # 1. Verificar que sea DT
        es_dt = any(rol.name == config.ROL_DE_DT for rol in ctx.author.roles)
        if not es_dt:
            await ctx.followup.send("❌ Solo los **Directores Técnicos** pueden despedir jugadores.")
            return

        # 2. Encontrar equipo del DT
        equipo_dt = None
        for rol in ctx.author.roles:
            if rol.name in self.bot.roles_equipos:
                equipo_dt = rol.name
                break

        if not equipo_dt:
            await ctx.followup.send("❌ No se encontró tu equipo.")
            return

        # 3. Verificar que el jugador sea de su equipo
        jugadores_col = get_collection('jugadores')
        jugador_db = await jugadores_col.find_one({
            'discord_id': str(jugador.id),
            'equipo': equipo_dt
        })

        if not jugador_db:
            await ctx.followup.send(f"❌ **{jugador.display_name}** no es jugador de tu equipo.")
            return

        # 4. No puede despedirse a sí mismo
        if jugador.id == ctx.author.id:
            await ctx.followup.send("❌ No puedes despedirte a ti mismo. Usa `/renunciar`.")
            return

        # 5. No puede despedir a otro DT
        es_dt_jugador = any(rol.name == config.ROL_DE_DT for rol in jugador.roles)
        if es_dt_jugador:
            await ctx.followup.send("❌ No puedes despedir a otro Director Técnico. Debe usar `/renunciar`.")
            return

        # 6. Ejecutar despido
        try:
            # Eliminar de jugadores en BD
            await jugadores_col.delete_one({'discord_id': str(jugador.id)})

            # Quitar rol de equipo en Discord
            rol_equipo = discord.utils.get(ctx.guild.roles, name=equipo_dt)
            if rol_equipo and rol_equipo in jugador.roles:
                await jugador.remove_roles(rol_equipo)

            # Dar rol de agente libre
            rol_agente = discord.utils.get(ctx.guild.roles, name=config.ROL_AGENTE_LIBRE)
            if rol_agente:
                await jugador.add_roles(rol_agente)

            # Guardar en agentes libres
            agentes_col = get_collection('agentes_libres')
            await agentes_col.update_one(
                {'discord_id': str(jugador.id)},
                {'$set': {
                    'discord_id': str(jugador.id),
                    'nombre': jugador.name,
                    'ex_equipo': equipo_dt,
                    'fecha': datetime.now().isoformat()
                }},
                upsert=True
            )

            # Embed de confirmación
            embed = discord.Embed(
                description=f"**{jugador.display_name}** ha sido despedido de **{equipo_dt}**.",
                color=discord.Color.red()
            )
            embed.set_author(name="🚪 JUGADOR DESPEDIDO", icon_url=jugador.display_avatar.url)
            await ctx.followup.send(embed=embed)

            # Notificar al jugador por DM
            try:
                dm_embed = discord.Embed(
                    title="🚪 Has sido despedido",
                    description=(
                        f"El DT de **{equipo_dt}** ha decidido prescindir de tus servicios.\n\n"
                        f"Ahora eres **Agente Libre**. Usa `/aglibre` para actualizar tu posición "
                        f"y aparecer en el tablón de fichajes."
                    ),
                    color=discord.Color.red()
                )
                await jugador.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # DMs cerrados, no bloquea el proceso

            # Anuncio en canal de fichajes
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            if canal_noticias:
                noti = discord.Embed(
                    title="📋 CARTA DE LIBERTAD",
                    description=(
                        f"**{jugador.mention}** ha recibido la carta de libertad del **{equipo_dt}**.\n"
                        f"El jugador queda como **Agente Libre**."
                    ),
                    color=discord.Color.dark_grey()
                )
                noti.set_footer(text=f"Despido autorizado por {ctx.author.display_name}")
                await canal_noticias.send(embed=noti)

            # Log de auditoría
            await log_action(
                guild_id=str(ctx.guild.id),
                action_type=config.AuditAction.DESPIDO,
                actor_id=str(ctx.author.id),
                actor_name=ctx.author.name,
                target_id=str(jugador.id),
                target_name=jugador.name,
                details={'equipo': equipo_dt}
            )

            logger.info(f"🚪 Despido: {jugador.name} de {equipo_dt} (por {ctx.author.name})")

        except discord.Forbidden:
            await ctx.followup.send("❌ No tengo permisos para modificar roles.")
        except Exception as e:
            await ctx.followup.send(f"❌ Error al despedir: {e}")
            logger.error(f"Error en despedir: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(FichajesCog(bot))
