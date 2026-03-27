"""
config.py - Configuración centralizada del Bot Liga Haxball
Todas las constantes y configuraciones del bot en un solo lugar.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================
# CREDENCIALES (desde .env)
# ============================================
TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

# Validación de credenciales
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN no encontrado en .env")
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI no encontrado en .env")

# ============================================
# CONFIGURACIÓN DE ROLES (DEFAULTS)
# ============================================

# IDs de Roles Fundamentales
ROL_LICENCIA_ID = 1474670232181411994
ROL_DT_OFICIAL_ID = 1455963001810063486

# Rol que identifica a los Directores Técnicos
ROL_DE_DT = '【🧠】Director Tecnico'

# Rol de Agente Libre (jugadores sin equipo)
ROL_AGENTE_LIBRE = 'Agente libre'

# Roles que pueden usar comandos de administración del bot
ROLES_ADMIN = [
    "Depto. Moderación",
    "Depto. Administracion",
    "Depto. Contenido",
    "🎯 Supervisor General",
    "🎯 Supervisor Contenido",
    "🎯 Supervisor Moderación",
    "🎯 Supervisor ADM",
    "【🛡️】Moderador III",
    "【🛡️】Moderador II",
    "【🛡️】Moderador I",
    "【🌟】Admin de Sala III",
    "【🌟】Admin de Sala II",
    "【🌟】Admin de Sala I"
]

# ============================================
# CONFIGURACIÓN DE CANALES (IDs de Discord)
# ============================================

# IDs de canales (más estables que nombres)
CANAL_AGENTES_LIBRES_ID = 1485416400100135042  # Reemplazar con ID real del canal ✦【💼】agentes-libres
CANAL_FICHAJES_ID = 1485416341505708163         # Reemplazar con ID real del canal fichajes
CANAL_LOGS_ID = 1462261514433204321            # Reemplazar con ID real del canal logspicks
CANAL_BACKUPS_ID = 1462261514433204322         # Reemplazar con ID real del canal backups-bot

# Canal específico para ofertas de fichaje (por ID)
# DTs solo pueden usar /fichar en este canal
# Notificaciones de aceptar/rechazar/expirar van aquí
CANAL_OFERTAS_ID = 1485416456614187111

# Canal para anuncios de nuevos equipos
CANAL_ANUNCIOS_ID = 1477719914721579038  # ID real del canal de anuncios

# ============================================
# CONFIGURACIÓN DEL JUEGO
# ============================================

LIMITE_PLANTILLA = 12

# ============================================
# SISTEMA DE PUNTUACIÓN (Defaults modificables por Admin)
# ============================================

DEFAULT_PUNTUACION = {
    'pts_victoria': 3,
    'pts_empate': 1,
    'pts_derrota': 0,
}

# Walkover (Incomparecencia): resultado automático
WALKOVER_GOLES_FAVOR = 3
WALKOVER_GOLES_CONTRA = 0

EQUIPOS_POR_DEFECTO = [
    "Liverpool", "Arsenal", "AC Milan", "PSG", "FC Barcelona", "Villareal",
    "Chelsea FC", "FC Bayern Munich", "Manchester City", "Ajax De Amsterdam",
    "Inter De Milan", "Real Madrid FC"
]

# ============================================
# COLORES PREDEFINIDOS PARA EQUIPOS
# ============================================

COLORES_EQUIPOS = {
    'rojo': '#e74c3c',
    'azul': '#3498db',
    'verde': '#2ecc71',
    'amarillo': '#f1c40f',
    'naranja': '#e67e22',
    'morado': '#9b59b6',
    'negro': '#000000',
    'blanco': '#ffffff',
    'rosa': '#e91e63',
    'celeste': '#00bfff',
    'gris': '#95a5a6',
    'turquesa': '#1abc9c',
    'oro': '#ffd700',
    'plata': '#c0c0c0',
    'marron': '#a52a2a'
}

# ============================================
# CONFIGURACIÓN DEL BOT
# ============================================

COMMAND_PREFIX = '!'
AUTO_SYNC_INTERVAL_HOURS = 1
DB_NAME = 'liga_bot'

# Intervalo de backup automático (en horas)
BACKUP_INTERVAL_HOURS = 24

# ============================================
# TIPOS DE ACCIONES PARA AUDITORÍA
# ============================================

class AuditAction:
    """Tipos de acciones registradas en auditoría."""
    # Fichajes
    FICHAJE = "FICHAJE"
    DESPIDO = "DESPIDO"
    INTERCAMBIO = "INTERCAMBIO"
    
    # DT
    DT_ASIGNADO = "DT_ASIGNADO"
    DT_RENUNCIA = "DT_RENUNCIA"
    DT_ROL_CAMBIO = "DT_ROL_CAMBIO"
    
    # Equipos
    EQUIPO_CREADO = "EQUIPO_CREADO"
    
    # Mercado
    MERCADO_ABIERTO = "MERCADO_ABIERTO"
    MERCADO_CERRADO = "MERCADO_CERRADO"

    # Cesiones (préstamos)
    CESION = "CESION"
    
    # Admin
    SINCRONIZACION = "SINCRONIZACION"
    BACKUP_CREADO = "BACKUP_CREADO"
    BACKUP_RESTAURADO = "BACKUP_RESTAURADO"
    BD_RESETEADA = "BD_RESETEADA"
    CANAL_BLOQUEADO = "CANAL_BLOQUEADO"
    CANAL_DESBLOQUEADO = "CANAL_DESBLOQUEADO"
    
    # Temporadas
    TEMPORADA_NUEVA = "TEMPORADA_NUEVA"
    
    # Partidos / Clasificación
    RESULTADO_REGISTRADO = "RESULTADO_REGISTRADO"
    WALKOVER = "WALKOVER"
    PUNTUACION_MODIFICADA = "PUNTUACION_MODIFICADA"
    
    # Config
    CONFIG_MODIFICADA = "CONFIG_MODIFICADA"

# ============================================
# CONFIGURACIÓN POR DEFECTO PARA SERVIDORES
# ============================================

DEFAULT_SERVER_CONFIG = {
    'canal_fichajes': 'fichajes',
    'canal_agentes': '✦【💼】agentes-libres',
    'canal_logs': 'logspicks',
    'canal_backups': 'backups-bot',
    'rol_dt': '【🧠】Director Tecnico',
    'rol_agente': 'Agente libre',
    'limite_plantilla': LIMITE_PLANTILLA,
    'backup_automatico': True,
    'backup_intervalo_horas': 24,
    'temporada_actual': 1,
    'pts_victoria': 3,
    'pts_empate': 1,
    'pts_derrota': 0,
}
