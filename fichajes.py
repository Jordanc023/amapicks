"""
fichajes.py - Cog para sistema de fichajes
Comandos: /fichar, /despedir, /agentes
Ofertas persistentes en MongoDB (no se pierden al reiniciar)
"""
import discord
from logger import get_module_logger

logger = get_module_logger("fichajes")
import asyncio
from bson import ObjectId
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

        # ... (rest of the code remains the same)

            await miembro.remove_roles(rol_vendedor)
        if rol_comprador:
            await miembro.add_roles(rol_comprador)

        # 4. Anuncio público en canal de fichajes
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
        if canal_noticias:
            es_clausulazo = (dt_vendedor_id == "clara_traicion")
            titulo = "💣 ¡CLAUSULAZO COMPLETADO!" if es_clausulazo else "🤝 TRASPASO OFICIAL"
            color = discord.Color.from_rgb(255, 69, 0) if es_clausulazo else discord.Color.brand_green()

        # ... (rest of the code remains the same)

        # Limpiar oferta pendiente de MongoDB
        await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

        # Obtener el canal de noticias de fichajes
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
        
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

        # ... (rest of the code remains the same)

        # Limpiar oferta pendiente de MongoDB
        await eliminar_oferta_pendiente(str(self.ctx.author.id), str(self.jugador.id))

        # Obtener el canal de noticias de fichajes
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)

        # Enviar anuncio de rechazo al canal de fichajes
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

        # ... (rest of the code remains the same)

        # Asignar rol en Discord
        await miembro.add_roles(rol_equipo)

        # Mensaje de confirmación (Se enviará al canal de noticias, no al de ofertas)
        canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)

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

        # ... (rest of the code remains the same)

        try:
            view.stop()

            if mensaje_oferta:
                # Enviar expiración al canal de noticias
                canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
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
        except Exception as e:
            logger.warning(f"Error al procesar expiración: {e}")

        # ... (rest of the code remains the same)

        try:
            await dt_vendedor_member.send(embed=embed_dm, view=view)
            
            # Anuncio Rumor
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            if canal_noticias:
                await canal_noticias.send(f"👀 📰 **[RUMOR]** Acaba de llegar una oferta a las oficinas del **{eq_vendedor}**... ¿Dejarán salir a {jugador.mention}?")
                
            await ctx.send(f"✅ ¡Oferta de `${monto:,}` enviada exitosamente por DM al DT del **{eq_vendedor}**!")
            logger.info(f"💼 Oferta Club a Club: {eq_comprador} ofrece ${monto} a {eq_vendedor} por {jugador.name}")
        except discord.Forbidden:
            await ctx.send(f"❌ No se pudo enviar DM al DT del {eq_vendedor}.")

        # ... (rest of the code remains the same)

        try:
            await jugador.send(embed=embed_dm, view=view)
            
            # Anuncio Rumor Bomba al canal
            canal_noticias = self.bot.get_channel(config.CANAL_FICHAJES_ID)
            mensaje_publico = f"🚨 **[CLAUSULAZO]** ¡El **{eq_comprador}** ha depositado `${monto:,}` en las oficinas para arrancar a **{jugador.mention}** del **{eq_vendedor}**!\n*El control ahora lo tiene el jugador por Mensaje Directo. ¿Romperá su contrato?*"
            if canal_noticias:
                await canal_noticias.send(mensaje_publico)
                # Confirmación al DT
                await ctx.send(f"✅ ¡Cláusula pagada! Esperando la decisión de {jugador.mention}.")
                await ctx.send(mensaje_publico)
                
            logger.info(f"💣 Clausulazo: {eq_comprador} paga ${monto} por {jugador.name} ({eq_vendedor})")
            
        except discord.Forbidden:
            await ctx.send(f"❌ ¡Operación fallida! **{jugador.mention}** tiene sus Mensajes Directos cerrados de Servidor. Tiene que habilitarlos para poder enviarle el maletín millonario.")
            
async def setup(bot):
    await bot.add_cog(FichajesCog(bot))
