from fastapi import APIRouter, HTTPException
from database import get_collection
from typing import List

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
async def get_clasificacion(liga_id: str = None):
    """Obtiene la tabla de posiciones calculada según puntos y diferencia de goles.
    Lee la puntuación configurable del servidor desde server_config.
    Si no se especifica liga_id, usa la liga activa del sistema.
    """
    equipos_col = get_collection("equipos")
    partidos_col = get_collection("partidos")
    config_col = get_collection("server_config")
    ligas_col = get_collection("ligas")
    
    # Determinar liga a consultar
    if not liga_id:
        # Buscar liga activa
        config_global = await config_col.find_one({"_id": "config_global"})
        if config_global and config_global.get("liga_activa_id"):
            liga_id = config_global["liga_activa_id"]
        else:
            # Fallback: primera liga activa
            liga = await ligas_col.find_one({"activa": True})
            if liga:
                liga_id = str(liga.get("_id"))
    
    # Obtener datos de la liga
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)}) if liga_id else None
    
    # Leer puntuación configurable
    server_cfg = await config_col.find_one({})
    pts_v = liga.get("puntos_victoria", 3) if liga else (server_cfg.get("pts_victoria", 3) if server_cfg else 3)
    pts_e = liga.get("puntos_empate", 1) if liga else (server_cfg.get("pts_empate", 1) if server_cfg else 1)
    pts_d = liga.get("puntos_derrota", 0) if liga else (server_cfg.get("pts_derrota", 0) if server_cfg else 0)
    
    # Obtener equipos de la liga
    query_equipos = {"liga_id": liga_id} if liga_id else {}
    equipos_cursor = equipos_col.find(query_equipos, {"_id": 0, "nombre": 1, "logo_url": 1, "liga_id": 1})
    equipos_db = await equipos_cursor.to_list(100)
    
    # Si no hay equipos con liga_id, fallback a todos
    if not equipos_db and liga_id:
        equipos_cursor = equipos_col.find({}, {"_id": 0, "nombre": 1, "logo_url": 1})
        equipos_db = await equipos_cursor.to_list(100)
    
    # Obtener partidos finalizados de la liga
    query_partidos = {
        "estado": {"$in": ["finalizado", "walkover", "jugado"]}
    }
    if liga_id:
        query_partidos["liga_id"] = liga_id
    
    partidos_cursor = partidos_col.find(query_partidos)
    partidos = await partidos_cursor.to_list(length=1000)
    
    # Inicializar stats por equipo
    stats_por_equipo = {}
    for eq in equipos_db:
        nombre = eq.get("nombre", "Desconocido")
        stats_por_equipo[nombre] = {
            "equipo": nombre,
            "logo": eq.get("logo_url", "https://cdn.discordapp.com/embed/avatars/0.png"),
            "pj": 0, "pg": 0, "pe": 0, "pp": 0,
            "gf": 0, "gc": 0, "pts": 0
        }
    
    # Procesar partidos
    for p in partidos:
        local = p.get("equipo_local")
        visitante = p.get("equipo_visitante")
        gl = p.get("goles_local", 0)
        gv = p.get("goles_visitante", 0)
        
        # Asegurar que ambos equipos existen en stats
        if local not in stats_por_equipo:
            stats_por_equipo[local] = {"equipo": local, "logo": "https://cdn.discordapp.com/embed/avatars/0.png", "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "pts": 0}
        if visitante not in stats_por_equipo:
            stats_por_equipo[visitante] = {"equipo": visitante, "logo": "https://cdn.discordapp.com/embed/avatars/0.png", "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "pts": 0}
        
        # Actualizar stats
        stats_por_equipo[local]["pj"] += 1
        stats_por_equipo[visitante]["pj"] += 1
        stats_por_equipo[local]["gf"] += gl
        stats_por_equipo[local]["gc"] += gv
        stats_por_equipo[visitante]["gf"] += gv
        stats_por_equipo[visitante]["gc"] += gl
        
        if gl > gv:  # Gana local
            stats_por_equipo[local]["pg"] += 1
            stats_por_equipo[local]["pts"] += pts_v
            stats_por_equipo[visitante]["pp"] += 1
            stats_por_equipo[visitante]["pts"] += pts_d
        elif gl < gv:  # Gana visitante
            stats_por_equipo[visitante]["pg"] += 1
            stats_por_equipo[visitante]["pts"] += pts_v
            stats_por_equipo[local]["pp"] += 1
            stats_por_equipo[local]["pts"] += pts_d
        else:  # Empate
            stats_por_equipo[local]["pe"] += 1
            stats_por_equipo[local]["pts"] += pts_e
            stats_por_equipo[visitante]["pe"] += 1
            stats_por_equipo[visitante]["pts"] += pts_e
    
    # Convertir a lista y calcular diferencia de goles
    tabla = []
    for nombre, stats in stats_por_equipo.items():
        stats["dg"] = stats["gf"] - stats["gc"]
        tabla.append(stats)
    
    # Ordenar por: 1º Puntos, 2º Diferencia Goles, 3º Goles Favor
    tabla_ordenada = sorted(tabla, key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
    
    # Asignar posición
    for i, t in enumerate(tabla_ordenada):
        t["pos"] = i + 1
    
    # Info de la liga
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
        "total_partidos": len(partidos)
    }

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
    
    # Verificar liga existe
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
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
    """Obtiene jugadores para el mercado (Agentes Libres y Jugadores con equipo)."""
    # Por defecto traemos agentes libres
    query = {}
    collection_name = "agentes_libres"
    
    if filtro == "con_equipo":
        collection_name = "jugadores"
    
    # Simulación de datos si la colección está vacía para ver el diseño
    # En producción esto vendrá de la BD real
    jugadores_col = get_collection(collection_name)
    jugadores = await jugadores_col.find({}, {"_id": 0}).to_list(100)
    
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
