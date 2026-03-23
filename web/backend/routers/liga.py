from fastapi import APIRouter, HTTPException, Query
from database import get_collection
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from services.clasificacion_service import obtener_tabla_clasificacion

router = APIRouter()

@router.get("/equipos")
async def get_equipos():
    """Obtiene todos los equipos con sus jugadores."""
    equipos_col = get_collection("equipos")
    jugadores_col = get_collection("jugadores")
    
    # 1. Obtener equipos
    equipos = await equipos_col.find({}, {"_id": 0}).to_list(100)
    
    # 2. Obtener todos los jugadores con equipo
    jugadores = await jugadores_col.find({}, {"_id": 0}).to_list(1000)
    
    # 3. Agrupar jugadores por equipo
    jugadores_por_equipo = {}
    for j in jugadores:
        eq = j.get("equipo")
        if eq:
            if eq not in jugadores_por_equipo:
                jugadores_por_equipo[eq] = []
            
            # Avatar fallback
            if "avatar_url" not in j:
                j["avatar_url"] = "https://cdn.discordapp.com/embed/avatars/0.png"
                
            jugadores_por_equipo[eq].append(j)
            
    # 4. Adjuntar a cada equipo
    for equipo in equipos:
        nombre_equipo = equipo.get("role_name") # Asumiendo que el nombre es la clave o role_name
        # Si no tiene role_name, usar 'nombre' o el campo que se use como ID
        if not nombre_equipo:
             nombre_equipo = equipo.get("nombre")
             
        equipo["plantilla"] = jugadores_por_equipo.get(nombre_equipo, [])
        equipo["total_jugadores"] = len(equipo["plantilla"])
        
    return equipos

@router.get("/clasificacion")
async def get_clasificacion(liga_id: Optional[str] = Query(None)):
    """Obtiene la tabla de posiciones calculada según puntos y diferencia de goles.
    Si no se especifica liga_id, usa la liga activa del sistema.
    """
    return await obtener_tabla_clasificacion(liga_id)

@router.get("/ligas-disponibles")
async def get_ligas_disponibles():
    """Obtiene lista de ligas activas para el selector de clasificación."""
    ligas_col = get_collection("ligas")
    
    ligas_cursor = ligas_col.find({"activa": True}).sort("division", 1)
    ligas = await ligas_cursor.to_list(length=20)
    
    return [
        {
            "id": str(l.get("_id")),
            "nombre": l.get("nombre"),
            "division": l.get("division"),
            "estado": l.get("estado", "configuracion"),
            "total_equipos": l.get("total_equipos", 0)
        }
        for l in ligas
    ]

@router.get("/jornadas/{liga_id}")
async def get_jornadas(liga_id: str, jornada: int = None):
    """
    Obtiene los partidos organizados por jornada para una liga.
    Si se especifica jornada, devuelve solo esa jornada.
    """
    partidos_col = get_collection("partidos")
    ligas_col = get_collection("ligas")
    
    try:
        liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="liga_id no es válido")
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Query base
    query = {"liga_id": liga_id}
    if jornada:
        query["jornada"] = jornada
    
    # Obtener partidos ordenados por jornada y fecha
    partidos_cursor = partidos_col.find(query).sort([("jornada", 1), ("fecha_hora", 1)])
    partidos = await partidos_cursor.to_list(length=500)
    
    # Organizar por jornada
    jornadas_dict = {}
    for p in partidos:
        jornada_num = p.get("jornada", 0)
        if jornada_num not in jornadas_dict:
            jornadas_dict[jornada_num] = {
                "jornada": jornada_num,
                "partidos": [],
                "fecha": None,
                "estado": "completada"  # default
            }
        
        # Determinar estado del partido
        estado = p.get("estado", "pendiente")
        estado_display = {
            "pendiente": "Pendiente",
            "jugado": "Jugado",
            "finalizado": "Finalizado",
            "walkover": "Walkover",
            "aplazado": "Aplazado"
        }.get(estado, estado.capitalize())
        
        partido_data = {
            "id": str(p.get("_id")),
            "equipo_local": p.get("equipo_local"),
            "equipo_visitante": p.get("equipo_visitante"),
            "goles_local": p.get("goles_local"),
            "goles_visitante": p.get("goles_visitante"),
            "estado": estado,
            "estado_display": estado_display,
            "fecha_hora": p.get("fecha_hora"),
            "jornada": jornada_num,
            "es_copa": p.get("copa", False),
            "ronda_copa": p.get("ronda") if p.get("copa") else None
        }
        
        jornadas_dict[jornada_num]["partidos"].append(partido_data)
        
        # Actualizar estado de jornada si hay partidos pendientes
        if estado == "pendiente":
            jornadas_dict[jornada_num]["estado"] = "en_curso"
        
        # Usar fecha del primer partido como fecha de la jornada
        if not jornadas_dict[jornada_num]["fecha"] and p.get("fecha_hora"):
            try:
                from datetime import datetime
                fecha = datetime.fromisoformat(p.get("fecha_hora"))
                jornadas_dict[jornada_num]["fecha"] = fecha.strftime("%d/%m/%Y")
            except:
                pass
    
    # Convertir a lista y ordenar
    jornadas_list = list(jornadas_dict.values())
    jornadas_list.sort(key=lambda x: x["jornada"])
    
    # Determinar jornada actual
    jornada_actual = liga.get("jornada_actual", 1)
    
    return {
        "liga": {
            "id": liga_id,
            "nombre": liga.get("nombre"),
            "division": liga.get("division"),
            "jornada_actual": jornada_actual,
            "total_jornadas": liga.get("jornadas_ida", 11) + liga.get("jornadas_vuelta", 11)
        },
        "jornada_actual": jornada_actual,
        "jornadas": jornadas_list,
        "total_partidos": len(partidos)
    }

@router.get("/partidos-equipo/{equipo_nombre}")
async def get_partidos_equipo(equipo_nombre: str, liga_id: str = None):
    """
    Obtiene todos los partidos (pasados y futuros) de un equipo específico.
    Útil para que los usuarios vean el calendario de su equipo.
    """
    partidos_col = get_collection("partidos")
    
    # Query para buscar donde el equipo es local o visitante
    query = {
        "$or": [
            {"equipo_local": equipo_nombre},
            {"equipo_visitante": equipo_nombre}
        ]
    }
    
    if liga_id:
        query["liga_id"] = liga_id
    
    partidos_cursor = partidos_col.find(query).sort([("jornada", 1), ("fecha_hora", 1)])
    partidos = await partidos_cursor.to_list(length=100)
    
    partidos_formateados = []
    for p in partidos:
        es_local = p.get("equipo_local") == equipo_nombre
        rival = p.get("equipo_visitante") if es_local else p.get("equipo_local")
        
        # Determinar resultado
        estado = p.get("estado", "pendiente")
        resultado = "pendiente"
        goles_favor = None
        goles_contra = None
        
        if estado in ["finalizado", "jugado", "walkover"]:
            gl = p.get("goles_local", 0)
            gv = p.get("goles_visitante", 0)
            goles_favor = gl if es_local else gv
            goles_contra = gv if es_local else gl
            
            if goles_favor > goles_contra:
                resultado = "victoria"
            elif goles_favor < goles_contra:
                resultado = "derrota"
            else:
                resultado = "empate"
        
        partidos_formateados.append({
            "id": str(p.get("_id")),
            "jornada": p.get("jornada"),
            "es_local": es_local,
            "rival": rival,
            "fecha_hora": p.get("fecha_hora"),
            "estado": estado,
            "goles_favor": goles_favor,
            "goles_contra": goles_contra,
            "resultado": resultado,
            "es_copa": p.get("copa", False),
            "ronda_copa": p.get("ronda") if p.get("copa") else None
        })
    
    return {
        "equipo": equipo_nombre,
        "liga_id": liga_id,
        "total_partidos": len(partidos_formateados),
        "partidos": partidos_formateados
    }

@router.get("/stats/general")
async def get_general_stats():
    """Obtiene estadísticas generales para el dashboard."""
    jugadores = await get_collection("jugadores").count_documents({})
    agentes = await get_collection("agentes_libres").count_documents({})
    partidos_pendientes = await get_collection("partidos").count_documents({"estado": "pendiente"})
    
    return {
        "jugadores_totales": jugadores,
        "agentes_libres": agentes,
        "partidos_pendientes": partidos_pendientes,
        "fichajes_activos": 0 # Placeholder por ahora
    }

@router.get("/mercado/status")
async def get_mercado_status():
    """Obtiene el estado del mercado de fichajes."""
    config = await get_collection("configuracion").find_one({"clave": "mercado_abierto"})
    if not config:
        return {"abierto": False, "detalle": "Configuración no encontrada"}
    
    valor = config.get("valor", "false")
    return {
        "abierto": valor == "true",
        "detalle": valor if valor not in ["true", "false"] else None
    }

@router.get("/mercado/jugadores")
async def get_jugadores_mercado(filtro: str = "todos"):
    """Obtiene jugadores para el mercado (Agentes Libres y Jugadores con equipo). Excluye DTs."""
    if filtro == "todos":
        jugadores_equipo = await get_collection("jugadores").find(
            {"es_dt": {"$ne": True}}, {"_id": 0}
        ).to_list(1000)
        agentes_libres = await get_collection("agentes_libres").find({}, {"_id": 0}).to_list(1000)
        
        for j in agentes_libres:
            j["equipo"] = None
            
        jugadores = jugadores_equipo + agentes_libres
    elif filtro == "con_equipo":
        jugadores = await get_collection("jugadores").find(
            {"es_dt": {"$ne": True}}, {"_id": 0}
        ).to_list(1000)
    else:
        collection_name = "agentes_libres"
        jugadores = await get_collection(collection_name).find({}, {"_id": 0}).to_list(1000)
    
    # Enriquecer con avatar simulado si no tienen (para demo)
    for i, j in enumerate(jugadores):
        if "avatar_url" not in j:
            # Avatar default de Discord
            j["avatar_url"] = f"https://cdn.discordapp.com/embed/avatars/{i % 5}.png"
            
    return jugadores

@router.get("/jugadores/{discord_id}")
async def get_jugador_detalle(discord_id: str):
    """Obtiene detalles completos de un jugador, incluyendo historial."""
    
    # 1. Buscar en Jugadores (Con equipo)
    jugador = await get_collection("jugadores").find_one({"discord_id": discord_id}, {"_id": 0})
    estado = "Contratado"
    
    # 2. Si no está, buscar en Agentes Libres
    if not jugador:
        jugador = await get_collection("agentes_libres").find_one({"discord_id": discord_id}, {"_id": 0})
        estado = "Agente Libre"
        
    if not jugador:
        return {"error": "Jugador no encontrado"}
    
    # 3. Obtener Historial (Audit Logs)
    # Buscamos logs donde target_id sea el jugador y la acción sea relevante
    historial_cursor = get_collection("audit_logs").find({
        "target_id": discord_id,
        "action_type": {"$in": ["FICHAJE", "DESPIDO", "RENUNCIA"]}
    }).sort("timestamp", -1).limit(10)
    
    historial = await historial_cursor.to_list(10)
    
    # Limpiar _id y convertir fechas
    for h in historial:
        h.pop("_id", None)
        if "timestamp" in h:
            h["timestamp"] = h["timestamp"].isoformat()

    # Añadir metadatos
    jugador["estado_actual"] = estado
    jugador["historial"] = historial
    
    # Avatar fallback
    if "avatar_url" not in jugador:
        jugador["avatar_url"] = "https://cdn.discordapp.com/embed/avatars/0.png"
        
    return jugador
