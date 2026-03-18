"""
estadisticas.py - Endpoints para estadísticas de la liga
Tabla de posiciones, últimos resultados, actividad reciente, rankings.
"""
from fastapi import APIRouter
from database import get_collection

router = APIRouter()


@router.get("/estadisticas")
async def get_estadisticas():
    """Endpoint principal que retorna todas las estadísticas de la liga."""

    # 1. Tabla de Posiciones
    tabla_col = get_collection("tabla_posiciones")
    tabla_raw = await tabla_col.find({}, {"_id": 0}).sort([
        ("pts", -1), ("dif", -1), ("gf", -1)
    ]).to_list(50)

    # 2. Últimos Resultados (partidos jugados)
    partidos_col = get_collection("partidos")
    ultimos_resultados = await partidos_col.find(
        {"estado": "jugado"},
        {"_id": 0, "equipo_local": 1, "equipo_visitante": 1,
         "goles_local": 1, "goles_visitante": 1, "resultado": 1,
         "fecha_resultado": 1}
    ).sort("fecha_resultado", -1).to_list(10)

    # Convertir fechas a string
    for r in ultimos_resultados:
        if "fecha_resultado" in r and r["fecha_resultado"]:
            r["fecha_resultado"] = r["fecha_resultado"].isoformat()

    # 3. Partidos Pendientes
    pendientes = await partidos_col.find(
        {"estado": {"$in": ["pendiente", "notificado"]}},
        {"_id": 0, "equipo_local": 1, "equipo_visitante": 1,
         "fecha_hora": 1, "estado": 1}
    ).sort("fecha_hora", 1).to_list(5)

    for p in pendientes:
        if "fecha_hora" in p and p["fecha_hora"]:
            p["fecha_hora"] = p["fecha_hora"].isoformat()

    # 4. Actividad Reciente (audit_logs)
    audit_col = get_collection("audit_logs")
    actividad = await audit_col.find(
        {"action_type": {"$in": [
            "FICHAJE", "DESPIDO", "DT_ASIGNADO", "DT_RENUNCIA",
            "MERCADO_ABIERTO", "MERCADO_CERRADO", "RESULTADO_REGISTRADO"
        ]}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(15)

    for a in actividad:
        if "timestamp" in a and a["timestamp"]:
            a["timestamp"] = a["timestamp"].isoformat()

    # 5. Rankings de jugadores (los más caros)
    jugadores_col = get_collection("jugadores")
    top_jugadores = await jugadores_col.find(
        {},
        {"_id": 0, "nombre": 1, "equipo": 1, "precio": 1,
         "clausula": 1, "posicion": 1, "avatar_url": 1, "es_dt": 1}
    ).sort("precio", -1).to_list(100)

    # Agentes libres
    agentes_col = get_collection("agentes_libres")
    agentes = await agentes_col.find(
        {},
        {"_id": 0, "nombre": 1, "precio": 1, "clausula": 1,
         "posicion": 1, "avatar_url": 1}
    ).sort("precio", -1).to_list(100)

    # Stats generales
    total_partidos_jugados = await partidos_col.count_documents({"estado": "jugado"})
    total_partidos_pendientes = await partidos_col.count_documents(
        {"estado": {"$in": ["pendiente", "notificado"]}}
    )
    total_jugadores = await jugadores_col.count_documents({})
    total_agentes = await agentes_col.count_documents({})
    total_fichajes = await audit_col.count_documents({"action_type": "FICHAJE"})
    total_despidos = await audit_col.count_documents({"action_type": "DESPIDO"})

    # Total de goles en todos los partidos
    goles_pipeline = [
        {"$match": {"estado": "jugado"}},
        {"$group": {
            "_id": None,
            "total_goles": {"$sum": {"$add": [
                {"$ifNull": ["$goles_local", 0]},
                {"$ifNull": ["$goles_visitante", 0]}
            ]}}
        }}
    ]
    goles_result = await partidos_col.aggregate(goles_pipeline).to_list(1)
    total_goles = goles_result[0]["total_goles"] if goles_result else 0

    # Equipos con su data
    equipos_col = get_collection("equipos")
    equipos = await equipos_col.find({}, {"_id": 0}).to_list(50)

    # Enrichir rankings con equipos más ricos
    equipos_ranking = []
    for eq in equipos:
        nombre = eq.get("role_name") or eq.get("nombre", "?")
        jugadores_eq = [j for j in top_jugadores if j.get("equipo") == nombre]
        valor_plantilla = sum(j.get("precio", 0) for j in jugadores_eq)
        equipos_ranking.append({
            "nombre": nombre,
            "presupuesto": eq.get("presupuesto", 0),
            "valor_plantilla": valor_plantilla,
            "total_jugadores": len(jugadores_eq)
        })

    equipos_ranking.sort(key=lambda x: x["valor_plantilla"], reverse=True)

    return {
        "tabla_posiciones": tabla_raw,
        "ultimos_resultados": ultimos_resultados,
        "partidos_pendientes": pendientes,
        "actividad_reciente": actividad,
        "top_jugadores": top_jugadores[:5],
        "equipos_ranking": equipos_ranking,
        "stats_generales": {
            "total_partidos_jugados": total_partidos_jugados,
            "total_partidos_pendientes": total_partidos_pendientes,
            "total_jugadores": total_jugadores,
            "total_agentes_libres": total_agentes,
            "total_fichajes": total_fichajes,
            "total_despidos": total_despidos,
            "total_goles": total_goles,
            "promedio_goles": round(total_goles / max(total_partidos_jugados, 1), 1)
        }
    }
