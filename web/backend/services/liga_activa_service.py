"""
Resolución de la liga activa del sistema y puntuación / W.O. unificados.
Fuente de verdad: documento en `ligas` (liga activa); `server_config` como espejo para el bot.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId

from database import get_collection


async def _liga_id_activa() -> Optional[str]:
    config_col = get_collection("server_config")
    config_global = await config_col.find_one({"_id": "config_global"})
    if config_global and config_global.get("liga_activa_id"):
        return str(config_global["liga_activa_id"])
    ligas_col = get_collection("ligas")
    liga_fb = await ligas_col.find_one({"activa": True})
    if liga_fb:
        return str(liga_fb.get("_id"))
    return None


async def obtener_liga_activa_doc() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Devuelve (liga_id str, documento liga o None)."""
    liga_id = await _liga_id_activa()
    if not liga_id:
        return None, None
    ligas_col = get_collection("ligas")
    try:
        doc = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    except InvalidId:
        return liga_id, None
    return liga_id, doc


async def obtener_puntuacion_operativa() -> Dict[str, Any]:
    """
    Puntos y goles W.O. para operaciones admin (resultado, walkover, recalcular).
    Prioridad: liga activa → server_config → defaults.
    """
    config_col = get_collection("server_config")
    cfg = await config_col.find_one({}) or {}

    liga_id, liga = await obtener_liga_activa_doc()

    def _from_liga_or_cfg(key_liga: str, key_cfg: str, default):
        if liga and liga.get(key_liga) is not None:
            return int(liga.get(key_liga))
        v = cfg.get(key_cfg)
        return int(v) if v is not None else default

    pts_v = _from_liga_or_cfg("puntos_victoria", "pts_victoria", 3)
    pts_e = _from_liga_or_cfg("puntos_empate", "pts_empate", 1)
    pts_d = _from_liga_or_cfg("puntos_derrota", "pts_derrota", 0)
    wgf = _from_liga_or_cfg("walkover_gf", "walkover_gf", 3)
    wgc = _from_liga_or_cfg("walkover_gc", "walkover_gc", 0)

    return {
        "pts_victoria": pts_v,
        "pts_empate": pts_e,
        "pts_derrota": pts_d,
        "walkover_gf": wgf,
        "walkover_gc": wgc,
        "liga_id": liga_id,
        "liga_nombre": (liga.get("nombre") if liga else None),
    }


async def actualizar_puntuacion_liga_activa(
    pts_victoria: int,
    pts_empate: int,
    pts_derrota: int,
    walkover_gf: int,
    walkover_gc: int,
) -> Tuple[Optional[str], bool]:
    """
    Actualiza el documento de la liga activa (si existe) y espeja en server_config.
    Retorna (liga_id, actualizo_liga).
    """
    config_col = get_collection("server_config")
    liga_id, liga = await obtener_liga_activa_doc()
    actualizo_liga = False

    if liga_id and liga:
        ligas_col = get_collection("ligas")
        try:
            await ligas_col.update_one(
                {"_id": ObjectId(liga_id)},
                {
                    "$set": {
                        "puntos_victoria": pts_victoria,
                        "puntos_empate": pts_empate,
                        "puntos_derrota": pts_derrota,
                        "walkover_gf": walkover_gf,
                        "walkover_gc": walkover_gc,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            actualizo_liga = True
        except InvalidId:
            pass

    await config_col.update_one(
        {},
        {
            "$set": {
                "pts_victoria": pts_victoria,
                "pts_empate": pts_empate,
                "pts_derrota": pts_derrota,
                "walkover_gf": walkover_gf,
                "walkover_gc": walkover_gc,
            }
        },
        upsert=True,
    )

    return liga_id, actualizo_liga
