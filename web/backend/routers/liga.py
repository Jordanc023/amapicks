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
async def get_clasificacion():
    """Obtiene la tabla de posiciones calculada según puntos y diferencia de goles.
    Lee la puntuación configurable del servidor desde server_config.
    """
    equipos_col = get_collection("equipos")
    config_col = get_collection("server_config")
    
    # Leer puntuación configurable (usar defaults si no existe)
    server_cfg = await config_col.find_one({})
    pts_v = server_cfg.get("pts_victoria", 3) if server_cfg else 3
    pts_e = server_cfg.get("pts_empate", 1) if server_cfg else 1
    pts_d = server_cfg.get("pts_derrota", 0) if server_cfg else 0
    
    equipos_cursor = equipos_col.find({}, {"_id": 0, "nombre": 1, "estadisticas_temporada": 1, "logo_url": 1})
    equipos_db = await equipos_cursor.to_list(100)
    
    tabla = []
    for eq in equipos_db:
        stats = eq.get("estadisticas_temporada", {})
        pg = stats.get("victorias", 0)
        pe = stats.get("empates", 0)
        pp = stats.get("derrotas", 0)
        gf = stats.get("goles_favor", 0)
        gc = stats.get("goles_contra", 0)
        
        # Calcular dinámicos con puntuación configurable
        pj = pg + pe + pp
        puntos = (pg * pts_v) + (pe * pts_e) + (pp * pts_d)
        dif_goles = gf - gc
        
        tabla.append({
            "equipo": eq.get("nombre", "Desconocido"),
            "logo": eq.get("logo_url", "https://cdn.discordapp.com/embed/avatars/0.png"),
            "pj": pj,
            "pg": pg,
            "pe": pe,
            "pp": pp,
            "gf": gf,
            "gc": gc,
            "dg": dif_goles,
            "pts": puntos
        })
        
    # Ordenar por: 1º Puntos, 2º Diferencia Goles, 3º Goles Favor
    tabla_ordenada = sorted(tabla, key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
    
    # Asignar posición
    for i, t in enumerate(tabla_ordenada):
        t["pos"] = i + 1
    
    # Incluir metadata de puntuación para el frontend
    return {
        "tabla": tabla_ordenada,
        "puntuacion": {"victoria": pts_v, "empate": pts_e, "derrota": pts_d}
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
