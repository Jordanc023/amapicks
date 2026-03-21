"""
Lógica compartida para tabla de posiciones desde partidos + equipos por liga.
Usada por GET /clasificacion y GET /estadisticas (Tabla completa en frontend).
"""
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from database import get_collection


async def obtener_tabla_clasificacion(liga_id: Optional[str] = None) -> dict:
    """Calcula clasificación. Si liga_id es None, usa liga activa del sistema."""
    equipos_col = get_collection("equipos")
    partidos_col = get_collection("partidos")
    config_col = get_collection("server_config")
    ligas_col = get_collection("ligas")

    if not liga_id:
        config_global = await config_col.find_one({"_id": "config_global"})
        if config_global and config_global.get("liga_activa_id"):
            liga_id = config_global["liga_activa_id"]
        else:
            liga_fb = await ligas_col.find_one({"activa": True})
            if liga_fb:
                liga_id = str(liga_fb.get("_id"))

    liga = None
    if liga_id:
        try:
            liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
        except InvalidId:
            raise HTTPException(status_code=400, detail="liga_id no es un ObjectId válido")

    server_cfg = await config_col.find_one({})
    pts_v = liga.get("puntos_victoria", 3) if liga else (server_cfg.get("pts_victoria", 3) if server_cfg else 3)
    pts_e = liga.get("puntos_empate", 1) if liga else (server_cfg.get("pts_empate", 1) if server_cfg else 1)
    pts_d = liga.get("puntos_derrota", 0) if liga else (server_cfg.get("pts_derrota", 0) if server_cfg else 0)

    equipos_db = []
    if liga_id:
        equipos_db = await equipos_col.find(
            {"liga_id": liga_id},
            {"_id": 0, "nombre": 1, "logo_url": 1, "liga_id": 1},
        ).to_list(100)
        if not equipos_db:
            try:
                equipos_db = await equipos_col.find(
                    {"liga_id": ObjectId(liga_id)},
                    {"_id": 0, "nombre": 1, "logo_url": 1, "liga_id": 1},
                ).to_list(100)
            except InvalidId:
                pass

    if liga_id:
        locales = await partidos_col.distinct("equipo_local", {"liga_id": liga_id})
        visitas = await partidos_col.distinct("equipo_visitante", {"liga_id": liga_id})
        ya = {e.get("nombre") for e in equipos_db if e.get("nombre")}
        for nombre in list(dict.fromkeys(locales + visitas)):
            if not nombre or nombre in ya:
                continue
            doc = await equipos_col.find_one({"nombre": nombre}, {"_id": 0, "nombre": 1, "logo_url": 1})
            if doc:
                equipos_db.append(doc)
            else:
                equipos_db.append({"nombre": nombre, "logo_url": None})
            ya.add(nombre)

    if not liga_id:
        equipos_db = await equipos_col.find({}, {"_id": 0, "nombre": 1, "logo_url": 1}).to_list(100)

    if not equipos_db and liga_id:
        equipos_db = await equipos_col.find({}, {"_id": 0, "nombre": 1, "logo_url": 1}).to_list(100)

    query_partidos = {
        "estado": {"$in": ["finalizado", "walkover", "jugado"]}
    }
    if liga_id:
        query_partidos["liga_id"] = liga_id

    partidos_cursor = partidos_col.find(query_partidos)
    partidos = await partidos_cursor.to_list(length=1000)

    stats_por_equipo = {}
    for eq in equipos_db:
        nombre = eq.get("nombre", "Desconocido")
        stats_por_equipo[nombre] = {
            "equipo": nombre,
            "logo": eq.get("logo_url", "https://cdn.discordapp.com/embed/avatars/0.png"),
            "pj": 0, "pg": 0, "pe": 0, "pp": 0,
            "gf": 0, "gc": 0, "pts": 0
        }

    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        gl = p.get("goles_local", 0)
        gv = p.get("goles_visitante", 0)

        if local not in stats_por_equipo:
            stats_por_equipo[local] = {"equipo": local, "logo": "https://cdn.discordapp.com/embed/avatars/0.png", "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "pts": 0}
        if visitante not in stats_por_equipo:
            stats_por_equipo[visitante] = {"equipo": visitante, "logo": "https://cdn.discordapp.com/embed/avatars/0.png", "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "pts": 0}

        stats_por_equipo[local]["pj"] += 1
        stats_por_equipo[visitante]["pj"] += 1
        stats_por_equipo[local]["gf"] += gl
        stats_por_equipo[local]["gc"] += gv
        stats_por_equipo[visitante]["gf"] += gv
        stats_por_equipo[visitante]["gc"] += gl

        if gl > gv:
            stats_por_equipo[local]["pg"] += 1
            stats_por_equipo[local]["pts"] += pts_v
            stats_por_equipo[visitante]["pp"] += 1
            stats_por_equipo[visitante]["pts"] += pts_d
        elif gl < gv:
            stats_por_equipo[visitante]["pg"] += 1
            stats_por_equipo[visitante]["pts"] += pts_v
            stats_por_equipo[local]["pp"] += 1
            stats_por_equipo[local]["pts"] += pts_d
        else:
            stats_por_equipo[local]["pe"] += 1
            stats_por_equipo[local]["pts"] += pts_e
            stats_por_equipo[visitante]["pe"] += 1
            stats_por_equipo[visitante]["pts"] += pts_e

    tabla = []
    for nombre, stats in stats_por_equipo.items():
        stats["dg"] = stats["gf"] - stats["gc"]
        stats["dif"] = stats["dg"]
        tabla.append(stats)

    tabla_ordenada = sorted(tabla, key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)

    for i, t in enumerate(tabla_ordenada):
        t["pos"] = i + 1

    liga_info = None
    if liga:
        liga_info = {
            "id": liga_id,
            "nombre": liga.get("nombre"),
            "division": liga.get("division"),
            "jornada_actual": liga.get("jornada_actual", 1),
            "estado": liga.get("estado", "configuracion")
        }

    return {
        "tabla": tabla_ordenada,
        "puntuacion": {"victoria": pts_v, "empate": pts_e, "derrota": pts_d},
        "liga": liga_info,
        "total_partidos": len(partidos),
    }
