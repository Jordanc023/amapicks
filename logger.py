"""
logger.py - Sistema de logging centralizado del Bot Liga Haxball
Reemplaza todos los print() con logging estructurado con niveles,
timestamps y rotación automática de archivos de log.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "gbleagues") -> logging.Logger:
    """
    Configura y retorna el logger principal del bot.

    - Salida a consola con colores via emojis
    - Salida a archivo con rotación (5 MB máx, 3 backups)
    - Formato: [TIMESTAMP] [NIVEL] [MÓDULO] Mensaje

    Args:
        name: Nombre del logger

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si se llama múltiples veces
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ─── Formato para consola (con emojis, legible) ─────────────
    console_formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # ─── Formato para archivo (detallado, para debugging) ───────
    file_formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)s.%(funcName)s:%(lineno)d │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    try:
        file_handler = RotatingFileHandler(
            filename="gbleagues.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB por archivo
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError):
        # Si no se puede escribir archivo (ej: en Discloud), solo consola
        pass

    logger.addHandler(console_handler)

    return logger


# Logger principal — importar desde cualquier módulo:
#   from logger import log
log = setup_logger("gbleagues")

# Sub-loggers para módulos específicos (opcional, hereda configuración)
# Se pueden crear así:
#   from logger import get_module_logger
#   logger = get_module_logger("fichajes")


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Crea un sub-logger para un módulo específico.
    Hereda la configuración del logger principal.

    Args:
        module_name: Nombre del módulo (ej: 'fichajes', 'partidos')

    Returns:
        Sub-logger configurado
    """
    return logging.getLogger(f"gbleagues.{module_name}")
