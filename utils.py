"""
utils.py - Utilidades compartidas del Bot Liga Haxball
Funciones de ayuda y decoradores usados en múltiples módulos.
"""
import discord
from discord.ext import commands
from config import ROLES_ADMIN
from logger import get_module_logger
from database import get_collection

logger = get_module_logger("utils")

# Default Fallbacks imported from config.py
from config import (
    LIMITE_PLANTILLA, CANAL_OFERTAS_ID, CANAL_FICHAJES, CANAL_AGENTES_LIBRES,
    ROL_DE_DT, ROL_AGENTE_LIBRE, WALKOVER_GOLES_FAVOR, WALKOVER_GOLES_CONTRA
)

class ConfigCache:
    _cache = None
    _last_update = None
    
    @classmethod
    async def get_config(cls):
        from datetime import datetime
        now = datetime.now()
        # Refresh cache every 60 seconds
        if cls._cache is None or cls._last_update is None or (now - cls._last_update).total_seconds() > 60:
            config_col = get_collection("server_config")
            cfg = await config_col.find_one({}) or {}
            
            mercado_col = get_collection("configuracion")
            m_cfg = await mercado_col.find_one({"clave": "mercado_abierto"}) or {}
            
            # Construir objeto de cache
            cls._cache = {
                "limite_plantilla": cfg.get("limite_plantilla", LIMITE_PLANTILLA),
                "pts_victoria": cfg.get("pts_victoria", 3),
                "pts_empate": cfg.get("pts_empate", 1),
                "pts_derrota": cfg.get("pts_derrota", 0),
                "walkover_gf": cfg.get("walkover_gf", WALKOVER_GOLES_FAVOR),
                "walkover_gc": cfg.get("walkover_gc", WALKOVER_GOLES_CONTRA),
                "canal_ofertas_id": int(cfg.get("canal_ofertas_id", CANAL_OFERTAS_ID)),
                "canal_fichajes": cfg.get("canal_fichajes", CANAL_FICHAJES),
                "canal_agentes": cfg.get("canal_agentes", CANAL_AGENTES_LIBRES),
                "rol_dt": cfg.get("rol_dt", ROL_DE_DT),
                "rol_agente": cfg.get("rol_agente_libre", ROL_AGENTE_LIBRE),
                "mercado_abierto": m_cfg.get("valor", "true") == "true"
            }
            cls._last_update = now
            
        return cls._cache

async def get_bot_config():
    """Obtiene la configuración dinámica cacheada de la Base de Datos (se refresca automagicamente cada 60s)."""
    return await ConfigCache.get_config()

def es_admin(member: discord.Member) -> bool:
    """
    Verifica si un miembro es administrador del bot.
    
    Puede ser admin por:
    1. Tener permisos de administrador nativos de Discord
    2. Tener alguno de los roles definidos en ROLES_ADMIN
    
    Args:
        member: Miembro de Discord a verificar
    
    Returns:
        True si es admin, False si no
    """
    # Verificar permisos nativos de Discord
    if member.guild_permissions.administrator:
        return True
    
    # Verificar por roles configurados
    for rol in member.roles:
        if rol.name in ROLES_ADMIN:
            return True
    
    return False


def check_es_admin():
    """
    Decorador para comandos que requieren permisos de administrador.
    
    Uso:
        @bot.command()
        @check_es_admin()
        async def mi_comando(ctx):
            ...
    
    Raises:
        commands.MissingPermissions si no es admin
    """
    async def predicate(ctx):
        if es_admin(ctx.author):
            return True
        raise commands.MissingPermissions(['admin_del_bot'])
    return commands.check(predicate)


def guild_only():
    """
    Decorador que verifica que el comando se ejecuta en un servidor (no en DMs).
    
    Previene crashes de NoneType cuando ctx.guild es None en mensajes directos.
    
    Uso:
        @bot.command()
        @guild_only()
        async def mi_comando(ctx):
            # ctx.guild siempre será válido aquí
            ...
    
    Raises:
        commands.NoPrivateMessage si se usa en DM
    """
    async def predicate(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage("Este comando solo funciona en servidores.")
        return True
    return commands.check(predicate)


def buscar_equipo(nombre_buscar: str, lista_equipos: list) -> tuple:
    """
    Busca un equipo por nombre (exacto o parcial).
    Ignora guiones y espacios para búsqueda más flexible.
    
    Args:
        nombre_buscar: Nombre a buscar
        lista_equipos: Lista de nombres de equipos disponibles
    
    Returns:
        Tupla (equipo_encontrado, lista_coincidencias)
        - Si hay coincidencia exacta: (nombre_equipo, [])
        - Si hay una parcial: (nombre_equipo, [])
        - Si hay múltiples: (None, [lista de coincidencias])
        - Si no hay ninguna: (None, [])
    """
    # Normalizar: minúsculas, sin guiones ni espacios
    def normalizar(texto):
        return texto.lower().replace('-', '').replace(' ', '')
    
    nombre_norm = normalizar(nombre_buscar)
    
    # Búsqueda exacta primero (normalizada)
    for equipo in lista_equipos:
        if normalizar(equipo) == nombre_norm:
            return (equipo, [])
    
    # Búsqueda parcial (el texto buscado está contenido en el nombre del equipo)
    coincidencias = [eq for eq in lista_equipos if nombre_norm in normalizar(eq)]
    
    if len(coincidencias) == 1:
        return (coincidencias[0], [])
    elif len(coincidencias) > 1:
        return (None, coincidencias)
    else:
        return (None, [])


def crear_embed_error(mensaje: str, titulo: str = "❌ Error") -> discord.Embed:
    """
    Crea un embed de error estandarizado.
    
    Args:
        mensaje: Mensaje de error
        titulo: Título del embed
    
    Returns:
        discord.Embed configurado
    """
    return discord.Embed(
        title=titulo,
        description=mensaje,
        color=discord.Color.red()
    )


def crear_embed_exito(mensaje: str, titulo: str = "✅ Éxito") -> discord.Embed:
    """
    Crea un embed de éxito estandarizado.
    
    Args:
        mensaje: Mensaje de éxito
        titulo: Título del embed
    
    Returns:
        discord.Embed configurado
    """
    return discord.Embed(
        title=titulo,
        description=mensaje,
        color=discord.Color.green()
    )


def crear_embed_info(mensaje: str, titulo: str = "ℹ️ Información") -> discord.Embed:
    """
    Crea un embed de información estandarizado.
    
    Args:
        mensaje: Mensaje informativo
        titulo: Título del embed
    
    Returns:
        discord.Embed configurado
    """
    return discord.Embed(
        title=titulo,
        description=mensaje,
        color=discord.Color.blue()
    )


def crear_embed_advertencia(mensaje: str, titulo: str = "⚠️ Advertencia") -> discord.Embed:
    """
    Crea un embed de advertencia estandarizado.
    
    Args:
        mensaje: Mensaje de advertencia
        titulo: Título del embed
    
    Returns:
        discord.Embed configurado
    """
    return discord.Embed(
        title=titulo,
        description=mensaje,
        color=discord.Color.orange()
    )


async def enviar_log(guild: discord.Guild, embed: discord.Embed, canal_nombre: str = 'logspicks'):
    """
    Envía un embed al canal de logs si existe.
    
    Args:
        guild: Servidor de Discord
        embed: Embed a enviar
        canal_nombre: Nombre del canal de logs
    """
    canal = discord.utils.get(guild.text_channels, name=canal_nombre)
    if canal:
        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"⚠️ Sin permisos para enviar al canal {canal_nombre}")
        except Exception as e:
            logger.error(f"⚠️ Error enviando log: {e}")
