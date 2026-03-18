from fastapi import APIRouter, HTTPException, Body, Depends
from database import get_collection
from repositories.admin_repository import AdminRepository
from typing import Optional, List
from pydantic import BaseModel
from routers.auth import require_admin
from datetime import datetime

router = APIRouter()

# Walkover defaults (matching bot config)
WALKOVER_GF = 3
WALKOVER_GC = 0

# --- Models ---
class UpdateTeamBudget(BaseModel):
    presupuesto: int

class UpdatePlayerPrice(BaseModel):
    precio: int
    clausula: int

class UpdatePlayerStats(BaseModel):
    goles: int
    asistencias: int
    mvps: int
    amarillas: int
    rojas: int

class UpdatePlayerBan(BaseModel):
    baneado: bool
    motivo: Optional[str] = None

class RegistrarResultado(BaseModel):
    equipo_local: str
    equipo_visitante: str
    goles_local: int
    goles_visitante: int

class RegistrarWalkover(BaseModel):
    ganador: str
    perdedor: str

class UpdatePuntuacion(BaseModel):
    pts_victoria: int
    pts_empate: int
    pts_derrota: int

# --- Liga Automation Models ---
class LigaConfig(BaseModel):
    nombre: str
    equipos_participantes: List[str]
    num_equipos: int
    formato: str = "todos_contra_todos"
    jornadas_total: int
    dias_entre_jornadas: int
    fecha_inicio: str
    playoffs_habilitados: bool = True
    clasificados_playoffs: int = 4

class GenerarCalendario(BaseModel):
    dias_entre_jornadas: int = 3
    fecha_inicio: str
    hora_default: str = "20:00"
    playoffs_habilitados: bool = True
    clasificados_playoffs: int = 4

# --- System Action Models ---
class PM2Action(BaseModel):
    action: str
    app_name: str = "amapicks-bot"

class AnnouncementData(BaseModel):
    titulo: str
    mensaje: str
    imagen_url: Optional[str] = None
    color: str = "#e74c3c" # Hex format
    canal_destino: str = "anuncios" # fallback channel name

class SystemConfigUpdate(BaseModel):
    limite_plantilla: int
    pts_victoria: int
    pts_empate: int
    pts_derrota: int
    walkover_gf: int
    walkover_gc: int
    canal_ofertas_id: str
    canal_fichajes: str
    rol_dt: str
    rol_agente_libre: str
    mercado_abierto: bool

class NukeConfirm(BaseModel):
    confirmation_text: str

# --- Endpoints (Protegidos con JWT + Admin) ---

@router.patch("/equipos/{equipo_id}/presupuesto")
async def update_team_budget(equipo_id: str, data: UpdateTeamBudget, admin_user: dict = Depends(require_admin)):
    """Actualiza el presupuesto de un equipo (Admin)."""
    equipo = await AdminRepository.get_equipo_by_id_or_name(equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
        
    presupuesto_anterior = equipo.get("presupuesto", 0)
    dinero_movido = data.presupuesto - presupuesto_anterior
    
    await AdminRepository.update_equipo_presupuesto(equipo["_id"], data.presupuesto)
    
    await AdminRepository.log_transaccion_financiera(
        actor=admin_user.get("name", "Admin Desconocido"),
        actor_id=admin_user.get("sub", ""),
        equipo_id=equipo_id,
        equipo_nombre=equipo.get('nombre', equipo_id),
        dinero_movido=dinero_movido,
        nuevo_presupuesto=data.presupuesto
    )
        
    return {"message": "Presupuesto actualizado", "presupuesto": data.presupuesto}

@router.patch("/jugadores/{discord_id}/economia")
async def update_player_economy(discord_id: str, data: UpdatePlayerPrice, admin_user: dict = Depends(require_admin)):
    """Actualiza precio y cláusula de un jugador (Admin)."""
    success = await AdminRepository.update_player_economy(discord_id, data.precio, data.clausula)
        
    if not success:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    return {"message": "Economía de jugador actualizada", "data": {"precio": data.precio, "clausula": data.clausula}}

@router.patch("/jugadores/{discord_id}/stats")
async def update_player_stats(discord_id: str, data: UpdatePlayerStats, admin_user: dict = Depends(require_admin)):
    """Actualiza estadísticas de un jugador en la temporada actual (Admin)."""
    update_data = {
        "estadisticas_temporada.goles": data.goles,
        "estadisticas_temporada.asistencias": data.asistencias,
        "estadisticas_temporada.mvps": data.mvps,
        "estadisticas_temporada.amarillas": data.amarillas,
        "estadisticas_temporada.rojas": data.rojas
    }
    
    success = await AdminRepository.update_player_stats(discord_id, update_data)
    
    if not success:
        raise HTTPException(status_code=404, detail="Jugador no encontrado (o es agente libre sin estadísticas)")
        
    return {"message": "Estadísticas del jugador actualizadas", "data": update_data}

@router.patch("/jugadores/{discord_id}/ban")
async def update_player_ban(discord_id: str, data: UpdatePlayerBan, admin_user: dict = Depends(require_admin)):
    """Aplica o remueve un baneo a un jugador (Admin)."""
    success = await AdminRepository.update_player_ban(discord_id, data.baneado, data.motivo)
        
    if not success:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    return {"message": f"Estado de baneo actualizado: {data.baneado}", "data": {"baneado": data.baneado, "motivo_ban": data.motivo}}

@router.get("/auditoria")
async def get_auditoria(limit: int = 50, admin_user: dict = Depends(require_admin)):
    """Obtiene el historial de transacciones financieras."""
    logs = await AdminRepository.get_auditoria_logs(limit)
    
    # Limpiar _id para serializacion JSON
    for log in logs:
        if "_id" in log:
            log["id"] = str(log["_id"])
            del log["_id"]
            
    return {"logs": logs}

# ============================================
# CLASIFICACIÓN — Resultado, Walkover, Puntuación
# ============================================

async def _get_puntuacion(config_col):
    """Helper: lee puntuación configurable del server_config."""
    cfg = await config_col.find_one({})
    return {
        "pts_victoria": cfg.get("pts_victoria", 3) if cfg else 3,
        "pts_empate": cfg.get("pts_empate", 1) if cfg else 1,
        "pts_derrota": cfg.get("pts_derrota", 0) if cfg else 0,
    }

async def _actualizar_tabla(tabla_col, guild_id, eq_local, eq_visitante, gl, gv, punt):
    """Helper: actualiza tabla_posiciones con puntuación configurable."""
    if gl > gv:
        pts_l, pts_v = punt["pts_victoria"], punt["pts_derrota"]
    elif gl < gv:
        pts_l, pts_v = punt["pts_derrota"], punt["pts_victoria"]
    else:
        pts_l, pts_v = punt["pts_empate"], punt["pts_empate"]

    await tabla_col.update_one(
        {"guild_id": guild_id, "equipo": eq_local},
        {"$inc": {
            "pj": 1, "pg": 1 if gl > gv else 0, "pe": 1 if gl == gv else 0,
            "pp": 1 if gl < gv else 0, "gf": gl, "gc": gv,
            "dif": gl - gv, "pts": pts_l
        }}, upsert=True
    )
    await tabla_col.update_one(
        {"guild_id": guild_id, "equipo": eq_visitante},
        {"$inc": {
            "pj": 1, "pg": 1 if gv > gl else 0, "pe": 1 if gl == gv else 0,
            "pp": 1 if gv < gl else 0, "gf": gv, "gc": gl,
            "dif": gv - gl, "pts": pts_v
        }}, upsert=True
    )

@router.get("/puntuacion")
async def get_puntuacion(admin_user: dict = Depends(require_admin)):
    """Obtiene la configuración de puntuación actual."""
    config_col = get_collection("server_config")
    punt = await _get_puntuacion(config_col)
    return punt

@router.patch("/puntuacion")
async def update_puntuacion(data: UpdatePuntuacion, admin_user: dict = Depends(require_admin)):
    """Actualiza la puntuación y recalcula toda la tabla."""
    if data.pts_victoria < 0 or data.pts_empate < 0 or data.pts_derrota < 0:
        raise HTTPException(status_code=400, detail="Los puntos no pueden ser negativos")

    config_col = get_collection("server_config")
    # Upsert en server_config
    await config_col.update_one(
        {},
        {"$set": {
            "pts_victoria": data.pts_victoria,
            "pts_empate": data.pts_empate,
            "pts_derrota": data.pts_derrota,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )

    # Recalcular tabla completa
    equipos_recalculados = await _recalcular_tabla_completa(data.pts_victoria, data.pts_empate, data.pts_derrota)

    return {
        "message": "Puntuación actualizada y tabla recalculada",
        "puntuacion": {"pts_victoria": data.pts_victoria, "pts_empate": data.pts_empate, "pts_derrota": data.pts_derrota},
        "equipos_recalculados": equipos_recalculados
    }

async def _recalcular_tabla_completa(pts_v, pts_e, pts_d):
    """Recalcula toda la tabla desde el historial de partidos usando MongoDB Aggregation Pipeline."""
    tabla_col = get_collection("tabla_posiciones")
    partidos_col = get_collection("partidos")

    # Obtener guild_ids únicos
    guild_ids = await partidos_col.distinct("guild_id")
    total_equipos = 0

    for gid in guild_ids:
        await tabla_col.delete_many({"guild_id": gid})
        
        pipeline = [
            {'$match': {
                'guild_id': gid,
                'estado': {'$in': ['jugado', 'finalizado', 'walkover']}
            }},
            {'$facet': {
                'locales': [
                    {'$project': {
                        'equipo': '$equipo_local',
                        'gf': {'$ifNull': ['$goles_local', 0]},
                        'gc': {'$ifNull': ['$goles_visitante', 0]}
                    }}
                ],
                'visitantes': [
                    {'$project': {
                        'equipo': '$equipo_visitante',
                        'gf': {'$ifNull': ['$goles_visitante', 0]},
                        'gc': {'$ifNull': ['$goles_local', 0]}
                    }}
                ]
            }},
            {'$project': {'todos_partidos': {'$concatArrays': ['$locales', '$visitantes']}}},
            {'$unwind': '$todos_partidos'},
            {'$replaceRoot': {'newRoot': '$todos_partidos'}},
            {'$match': {'equipo': {'$ne': None}}},
            {'$group': {
                '_id': '$equipo',
                'pj': {'$sum': 1},
                'gf': {'$sum': '$gf'},
                'gc': {'$sum': '$gc'},
                'pg': {'$sum': {'$cond': [{'$gt': ['$gf', '$gc']}, 1, 0]}},
                'pe': {'$sum': {'$cond': [{'$eq': ['$gf', '$gc']}, 1, 0]}},
                'pp': {'$sum': {'$cond': [{'$lt': ['$gf', '$gc']}, 1, 0]}},
                'dif': {'$sum': {'$subtract': ['$gf', '$gc']}}
            }},
            {'$project': {
                '_id': 0,
                'guild_id': gid,
                'equipo': '$_id',
                'pj': 1, 'pg': 1, 'pe': 1, 'pp': 1, 'gf': 1, 'gc': 1, 'dif': 1,
                'pts': {
                    '$add': [
                        {'$multiply': ['$pg', pts_v]},
                        {'$multiply': ['$pe', pts_e]},
                        {'$multiply': ['$pp', pts_d]}
                    ]
                }
            }}
        ]

        resultados = await partidos_col.aggregate(pipeline).to_list(length=None)
        
        if resultados:
            await tabla_col.insert_many(resultados)
        
        total_equipos += len(resultados)

    return total_equipos

@router.post("/resultado")
async def registrar_resultado(data: RegistrarResultado, admin_user: dict = Depends(require_admin)):
    """Registra un resultado normal y actualiza la tabla."""
    if data.goles_local < 0 or data.goles_visitante < 0:
        raise HTTPException(status_code=400, detail="Los goles no pueden ser negativos")
    if data.equipo_local == data.equipo_visitante:
        raise HTTPException(status_code=400, detail="Un equipo no puede jugar contra sí mismo")

    partidos_col = get_collection("partidos")
    tabla_col = get_collection("tabla_posiciones")
    config_col = get_collection("server_config")
    punt = await _get_puntuacion(config_col)

    # Usar guild_id "0" para web (sin contexto de guild específico)
    guild_id = "0"

    await partidos_col.insert_one({
        "guild_id": guild_id,
        "equipo_local": data.equipo_local,
        "equipo_visitante": data.equipo_visitante,
        "goles_local": data.goles_local,
        "goles_visitante": data.goles_visitante,
        "estado": "jugado",
        "tipo": "normal",
        "registrado_por": admin_user.get("sub", "web_admin"),
        "fecha_registro": datetime.utcnow()
    })

    await _actualizar_tabla(tabla_col, guild_id, data.equipo_local, data.equipo_visitante, data.goles_local, data.goles_visitante, punt)

    return {
        "message": f"Resultado registrado: {data.equipo_local} {data.goles_local}-{data.goles_visitante} {data.equipo_visitante}",
        "tipo": "normal"
    }

@router.post("/walkover")
async def registrar_walkover(data: RegistrarWalkover, admin_user: dict = Depends(require_admin)):
    """Registra un Walkover (W.O.) — victoria automática 3-0."""
    if data.ganador == data.perdedor:
        raise HTTPException(status_code=400, detail="No se puede dictar W.O. contra el mismo equipo")

    partidos_col = get_collection("partidos")
    tabla_col = get_collection("tabla_posiciones")
    config_col = get_collection("server_config")
    punt = await _get_puntuacion(config_col)

    guild_id = "0"

    await partidos_col.insert_one({
        "guild_id": guild_id,
        "equipo_local": data.ganador,
        "equipo_visitante": data.perdedor,
        "goles_local": WALKOVER_GF,
        "goles_visitante": WALKOVER_GC,
        "estado": "walkover",
        "tipo": "walkover",
        "registrado_por": admin_user.get("sub", "web_admin"),
        "fecha_registro": datetime.utcnow()
    })

    await _actualizar_tabla(tabla_col, guild_id, data.ganador, data.perdedor, WALKOVER_GF, WALKOVER_GC, punt)

    return {
        "message": f"W.O. dictado: {data.ganador} {WALKOVER_GF}-{WALKOVER_GC} {data.perdedor}",
        "tipo": "walkover",
        "marcador": f"{WALKOVER_GF}-{WALKOVER_GC}"
    }

@router.post("/recalcular_tabla")
async def recalcular_tabla(admin_user: dict = Depends(require_admin)):
    """Recalcula toda la tabla desde el historial de partidos."""
    config_col = get_collection("server_config")
    punt = await _get_puntuacion(config_col)
    equipos = await _recalcular_tabla_completa(punt["pts_victoria"], punt["pts_empate"], punt["pts_derrota"])
    return {"message": "Tabla recalculada", "equipos_procesados": equipos}

@router.post("/resetear_tabla")
async def resetear_tabla(admin_user: dict = Depends(require_admin)):
    """Borra toda la tabla de posiciones."""
    tabla_col = get_collection("tabla_posiciones")
    result = await tabla_col.delete_many({})
    return {"message": "Tabla reseteada", "registros_eliminados": result.deleted_count}

# ============================================
# LIGA AUTOMATION — Calendar Generation
# ============================================

def _generar_fixture_round_robin(equipos: List[str]):
    """Genera fixture round-robin (todos contra todos)."""
    n = len(equipos)
    if n % 2 == 1:
        equipos = equipos + ["BYE"]  # Equipo impar, agrega BYE
    
    fixture = []
    equipos_rotacion = equipos.copy()
    
    for jornada_num in range(n - 1):
        partidos_jornada = []
        for i in range(n // 2):
            local = equipos_rotacion[i]
            visitante = equipos_rotacion[n - 1 - i]
            
            if local != "BYE" and visitante != "BYE":
                partidos_jornada.append({
                    "equipo_local": local,
                    "equipo_visitante": visitante
                })
        
        # Rotación: mantener primer equipo fijo, rotar el resto
        equipos_rotacion = [equipos_rotacion[0]] + equipos_rotacion[-1:] + equipos_rotacion[1:-1]
        fixture.append({
            "jornada": jornada_num + 1,
            "partidos": partidos_jornada
        })
    
    return fixture

@router.post("/generar_calendario_liga")
async def generar_calendario_liga(data: GenerarCalendario, admin_user: dict = Depends(require_admin)):
    """Genera automáticamente todo el calendario de liga (round-robin)."""
    equipos_col = get_collection("equipos")
    partidos_col = get_collection("partidos")
    config_liga_col = get_collection("config_liga")
    
    # Obtener equipos activos
    equipos_cursor = equipos_col.find({"activo": True})
    equipos = await equipos_cursor.to_list(length=50)
    equipos_nombres = [eq["nombre"] for eq in equipos]
    
    if len(equipos_nombres) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 equipos activos")
    
    # Generar fixture
    fixture = _generar_fixture_round_robin(equipos_nombres)
    
    # Parse fecha inicio
    try:
        fecha_inicio = datetime.strptime(data.fecha_inicio, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Crear partidos en BD
    partidos_creados = 0
    for jornada_data in fixture:
        jornada_num = jornada_data["jornada"]
        fecha_jornada = fecha_inicio + datetime.timedelta(days=(jornada_num - 1) * data.dias_entre_jornadas)
        
        for partido in jornada_data["partidos"]:
            fecha_hora = datetime.combine(
                fecha_jornada.date(), 
                datetime.strptime(data.hora_default, "%H:%M").time()
            )
            
            await partidos_col.insert_one({
                "guild_id": "0",
                "equipo_local": partido["equipo_local"],
                "equipo_visitante": partido["equipo_visitante"],
                "fecha_hora": fecha_hora.isoformat(),
                "jornada": jornada_num,
                "fase": "Liga Regular",
                "estado": "pendiente",
                "auto_generado": True,
                "creado_por": admin_user.get("sub", "admin_web"),
                "creado_en": datetime.utcnow()
            })
            partidos_creados += 1
    
    # Guardar configuración de liga
    await config_liga_col.update_one(
        {"_id": "liga_actual"},
        {"$set": {
            "nombre": f"Temporada {datetime.now().year}",
            "equipos_participantes": equipos_nombres,
            "num_equipos": len(equipos_nombres),
            "formato": "todos_contra_todos",
            "jornadas_total": len(fixture),
            "dias_entre_jornadas": data.dias_entre_jornadas,
            "fecha_inicio": data.fecha_inicio,
            "hora_default": data.hora_default,
            "playoffs_habilitados": data.playoffs_habilitados,
            "clasificados_playoffs": data.clasificados_playoffs,
            "estado": "en_curso",
            "jornada_actual": 1,
            "actualizado_por": admin_user.get("sub", "admin_web"),
            "actualizado_en": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {
        "message": f"Calendario generado exitosamente",
        "equipos": len(equipos_nombres),
        "jornadas": len(fixture),
        "partidos_creados": partidos_creados,
        "playoffs_habilitados": data.playoffs_habilitados
    }

@router.get("/estado_liga")
async def get_estado_liga(admin_user: dict = Depends(require_admin)):
    """Obtiene el estado actual de la liga y progreso."""
    partidos_col = get_collection("partidos")
    config_liga_col = get_collection("config_liga")
    
    config = await config_liga_col.find_one({"_id": "liga_actual"})
    if not config:
        return {"estado": "no_iniciada", "message": "No hay una liga configurada"}
    
    # Contar partidos por estado
    total_liga = await partidos_col.count_documents({"fase": "Liga Regular"})
    jugados_liga = await partidos_col.count_documents({"fase": "Liga Regular", "estado": "finalizado"})
    
    progreso = {
        "estado": config["estado"],
        "jornadas_total": config["jornadas_total"],
        "partidos_total": total_liga,
        "partidos_jugados": jugados_liga,
        "porcentaje_completado": round((jugados_liga / total_liga) * 100, 1) if total_liga > 0 else 0,
        "playoffs_habilitados": config.get("playoffs_habilitados", False),
        "clasificados_playoffs": config.get("clasificados_playoffs", 4)
    }
    
    # Verificar si se pueden generar playoffs
    if config["estado"] == "en_curso" and jugados_liga == total_liga and config.get("playoffs_habilitados"):
        progreso["playoffs_listos"] = True
    
    return progreso

@router.post("/generar_playoffs")
async def generar_playoffs(admin_user: dict = Depends(require_admin)):
    """Genera automáticamente los playoffs basados en la tabla de posiciones."""
    partidos_col = get_collection("partidos")
    tabla_col = get_collection("tabla_posiciones")
    config_liga_col = get_collection("config_liga")
    
    config = await config_liga_col.find_one({"_id": "liga_actual"})
    if not config or not config.get("playoffs_habilitados"):
        raise HTTPException(status_code=400, detail="Los playoffs no están habilitados en esta liga")
    
    # Obtener tabla de posiciones actual
    tabla_cursor = tabla_col.find({"guild_id": "0"}).sort([("pts", -1), ("dif", -1), ("gf", -1)])
    tabla = await tabla_cursor.to_list(length=20)
    
    clasificados = config.get("clasificados_playoffs", 4)
    if len(tabla) < clasificados:
        raise HTTPException(status_code=400, detail=f"No hay suficientes equipos en la tabla. Se necesitan {clasificados}")
    
    # Tomar top N equipos
    equipos_clasificados = tabla[:clasificados]
    
    # Generar semifinales: 1° vs 4°, 2° vs 3°
    if clasificados == 4:
        semifinales = [
            {"local": equipos_clasificados[0]["equipo"], "visitante": equipos_clasificados[3]["equipo"]},
            {"local": equipos_clasificados[1]["equipo"], "visitante": equipos_clasificados[2]["equipo"]}
        ]
        
        # Crear partidos de semifinales
        fecha_playoffs = datetime.now() + datetime.timedelta(days=3)  # 3 días después
        
        for i, partido in enumerate(semifinales, 1):
            await partidos_col.insert_one({
                "guild_id": "0",
                "equipo_local": partido["local"],
                "equipo_visitante": partido["visitante"],
                "fecha_hora": (fecha_playoffs + datetime.timedelta(days=i-1)).isoformat(),
                "jornada": None,
                "fase": "Semifinal",
                "estado": "pendiente",
                "auto_generado": True,
                "creado_por": admin_user.get("sub", "admin_web"),
                "creado_en": datetime.utcnow()
            })
        
        # Actualizar estado de liga
        await config_liga_col.update_one(
            {"_id": "liga_actual"},
            {"$set": {"estado": "playoffs", "actualizado_en": datetime.utcnow()}}
        )
        
        return {
            "message": "Playoffs generados exitosamente",
            "semifinales_creadas": 2,
            "equipos_clasificados": [eq["equipo"] for eq in equipos_clasificados]
        }
    
    else:
        raise HTTPException(status_code=400, detail="Sólo se soporta playoffs de 4 equipos actualmente")

@router.get("/system/status")
async def get_system_status(admin_user: dict = Depends(require_admin)):
    """Obtiene el estado en vivo del Bot de Discord y de la API."""
    try:
        config_col = get_collection("config_col")
        bot_status = await config_col.find_one({"_id": "bot_status"})
        
        # Valores por defecto si el bot nunca ha reportado
        is_online = False
        uptime_string = "0d 0h 0m"
        latency_ms = 0
        
        if bot_status:
            last_update = bot_status.get("last_update")
            uptime_start = bot_status.get("uptime_start")
            
            # Si el último latido fue hace menos de 3 minutos, el bot está online
            if last_update:
                time_diff = (datetime.now() - last_update).total_seconds()
                if time_diff < 180: # 3 min tolerancia
                    is_online = True
                    
            if uptime_start and is_online:
                diff = datetime.now() - uptime_start
                days = diff.days
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                uptime_string = f"{days}d {hours}h {minutes}m"
                
            latency_ms = bot_status.get("latency_ms", 0)
            
        return {
            "api_status": "Online",
            "bot_status": "Online" if is_online else "Offline",
            "bot_latency": latency_ms,
            "bot_uptime": uptime_string
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/sync")
async def force_sync_bot_commands(admin_user: dict = Depends(require_admin)):
    """Activa una bandera en la base de datos para que el bot de Discord sincronice sus comandos (Slash Commands) en el próximo latido (máximo 1 minuto)."""
    try:
        config_col = get_collection("config_col")
        
        # Enviar la orden de sincronización
        await config_col.update_one(
            {"_id": "bot_commands"},
            {"$set": {"force_sync": True, "requested_at": datetime.now(), "requested_by": admin_user.get("sub", "admin_web")}},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Orden de Sincronización enviada. El bot aplicará los cambios en los próximos 60 segundos."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import asyncio
import re

@router.post("/system/pm2")
async def execute_pm2_action(data: PM2Action, admin_user: dict = Depends(require_admin)):
    """Ejecuta una acción de PM2 en el servidor host para controlar el bot."""
    if data.action not in ["restart", "stop", "start", "reload"]:
        raise HTTPException(status_code=400, detail="Acción de PM2 no soportada. Use restart, stop, start o reload.")
        
    # Validar app_name para evitar inyección de comandos en OS
    if not re.match(r"^[a-zA-Z0-9_\-]+$", data.app_name):
        raise HTTPException(status_code=400, detail="Nombre de aplicación no válido. Intento de inyección bloqueado.")
        
    try:
        comando_str = f"pm2 {data.action} {data.app_name}"
        # Usamos asyncio exec execution (lista de args) en vez de shell string
        process = await asyncio.create_subprocess_exec(
            "pm2", data.action, data.app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode().strip()
        error_output = stderr.decode().strip()
        
        if process.returncode != 0:
            # Tolerancia para entornos de desarrollo local de Windows que no tienen PM2 instalado.
            if "pm2" in error_output.lower() or "pm2" in output.lower():
                return {
                    "success": False, 
                    "message": f"Alerta local: PM2 no está instalado o reconocido en este sistema. El comando '{comando_str}' falló.", 
                    "simulated": True
                }
            raise HTTPException(status_code=500, detail=f"Fallo PM2: {error_output}")
            
        return {
            "success": True,
            "message": f"Comando '{comando_str}' ejecutado exitosamente. El bot aplicará la acción.",
            "output": output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando PM2: {str(e)}")

@router.post("/system/announce")
async def send_global_announcement(data: AnnouncementData, admin_user: dict = Depends(require_admin)):
    """Encola un anuncio global en MongoDB para que el bot lo dispare casi instantáneamente."""
    try:
        anuncios_col = get_collection("anuncios_pendientes")
        
        anuncio = {
            "titulo": data.titulo,
            "mensaje": data.mensaje,
            "imagen_url": data.imagen_url,
            "color": data.color,
            "canal_destino": data.canal_destino,
            "creado_por": admin_user.get("sub", "admin_web"),
            "creado_en": datetime.utcnow()
        }
        
        await anuncios_col.insert_one(anuncio)
        
        # Opcionalmente, forzar una revisión del bot usando la misma técnica de force_sync
        config_col = get_collection("config_col")
        await config_col.update_one(
            {"_id": "bot_commands"},
            {"$set": {"force_announce_check": True}},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Anuncio encolado exitosamente. El bot lo publicará en breve."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/config")
async def get_system_config(admin_user: dict = Depends(require_admin)):
    """Obtiene toda la configuración global del sistema y variables de Discord."""
    config_col = get_collection("server_config")
    mercado_col = get_collection("configuracion")
    
    server_cfg = await config_col.find_one({}) or {}
    mercado_cfg = await mercado_col.find_one({"clave": "mercado_abierto"}) or {}
    
    mercado_val = mercado_cfg.get("valor", "true") == "true"
    
    # Import Defaults from config to prepopulate if missing
    from config import LIMITE_PLANTILLA, CANAL_OFERTAS_ID, CANAL_FICHAJES, ROL_DE_DT, ROL_AGENTE_LIBRE
    
    return {
        "limite_plantilla": server_cfg.get("limite_plantilla", LIMITE_PLANTILLA),
        "pts_victoria": server_cfg.get("pts_victoria", 3),
        "pts_empate": server_cfg.get("pts_empate", 1),
        "pts_derrota": server_cfg.get("pts_derrota", 0),
        "walkover_gf": server_cfg.get("walkover_gf", 3),
        "walkover_gc": server_cfg.get("walkover_gc", 0),
        "canal_ofertas_id": server_cfg.get("canal_ofertas_id", str(CANAL_OFERTAS_ID)),
        "canal_fichajes": server_cfg.get("canal_fichajes", CANAL_FICHAJES),
        "rol_dt": server_cfg.get("rol_dt", ROL_DE_DT),
        "rol_agente_libre": server_cfg.get("rol_agente_libre", ROL_AGENTE_LIBRE),
        "mercado_abierto": mercado_val
    }

@router.post("/system/config")
async def update_system_config(data: SystemConfigUpdate, admin_user: dict = Depends(require_admin)):
    """Actualiza la configuración unificada de la liga y el bot."""
    config_col = get_collection("server_config")
    mercado_col = get_collection("configuracion")
    
    # Update server variables
    await config_col.update_one(
        {}, 
        {"$set": {
            "limite_plantilla": data.limite_plantilla,
            "pts_victoria": data.pts_victoria,
            "pts_empate": data.pts_empate,
            "pts_derrota": data.pts_derrota,
            "walkover_gf": data.walkover_gf,
            "walkover_gc": data.walkover_gc,
            "canal_ofertas_id": data.canal_ofertas_id,
            "canal_fichajes": data.canal_fichajes,
            "rol_dt": data.rol_dt,
            "rol_agente_libre": data.rol_agente_libre,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    # Update Mercado Status
    await mercado_col.update_one(
        {"clave": "mercado_abierto"},
        {"$set": {"valor": "true" if data.mercado_abierto else "false"}},
        upsert=True
    )
    
    return {"success": True, "message": "Ajustes Globales actualizados y aplicados en caliente."}

# ============================================
# ZONA DE PELIGRO Y MANTENIMIENTO
# ============================================

import json
from fastapi.responses import Response

@router.post("/system/backup")
async def generate_backup(admin_user: dict = Depends(require_admin)):
    """Genera un volcado completo de la base de datos en JSON."""
    try:
        collections = await get_collection("system.namespaces").database.list_collection_names()
        db_dump = {}
        
        for coll_name in collections:
            # Skip system collections
            if coll_name.startswith("system."): continue
            
            coll = get_collection(coll_name)
            docs = await coll.find({}).to_list(length=None)
            
            # Limpiar _id (ObjectIDs) para la serialización JSON
            for doc in docs:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            db_dump[coll_name] = docs
            
        json_data = json.dumps(db_dump, default=str)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amapicks_backup_{timestamp}.json"
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/reset-season")
async def reset_season(admin_user: dict = Depends(require_admin)):
    """Limpia la temporada actual (Partidos, Tabla de posiciones, Estadísticas de temporada).
    Mantiene Equipos, Jugadores y Economía.
    """
    try:
        await get_collection("partidos").delete_many({})
        await get_collection("tabla_posiciones").delete_many({})
        
        # Limpiar estadísticas_temporada en Jugadores
        await get_collection("jugadores").update_many(
            {}, 
            {"$set": {
                "estadisticas_temporada": {
                    "goles": 0, "asistencias": 0, "mvps": 0, "amarillas": 0, "rojas": 0
                }
            }}
        )
        
        return {"success": True, "message": "Temporada reseteada. Todas las posiciones, estadísticas y partidos han sido limpiados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/nuke")
async def nuke_database(data: NukeConfirm, admin_user: dict = Depends(require_admin)):
    """Peligro inminente: Purgar toda la base de datos principal."""
    if data.confirmation_text != "CONFIRMAR BORRADO TOTAL Y COMENZAR DE CERO":
        raise HTTPException(status_code=400, detail="Texto de confirmación incorrecto. Borrado abortado.")
        
    try:
        collections_to_nuke = [
            "jugadores", "equipos", "partidos", "agentes_libres", 
            "transacciones_finacieras", "tabla_posiciones", "ofertas_pendientes"
        ]
        
        for coll_name in collections_to_nuke:
            await get_collection(coll_name).delete_many({})
            
        # Opcional: limpiar también logs antigüos
        from datetime import timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        await get_collection("log_auditoria").delete_many({"timestamp": {"$lt": thirty_days_ago}})

        return {"success": True, "message": "NUCLEAR LAUNCH DETECTED. Base de datos reseteada desde cero exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo cataclísmico al intentar borrar BD: {str(e)}")

@router.post("/system/purge-logs")
async def purge_logs(admin_user: dict = Depends(require_admin)):
    """Limpia los reportes auditoria que sean viejos."""
    try:
        from datetime import timedelta
        # Eliminar auditoría con más de 60 días
        cutoff_date = datetime.now() - timedelta(days=60)
        
        fin_res = await get_collection("transacciones_finacieras").delete_many({"timestamp": {"$lt": cutoff_date}})
        aud_res = await get_collection("log_auditoria").delete_many({"timestamp": {"$lt": cutoff_date}})
        
        total_deleted = fin_res.deleted_count + aud_res.deleted_count
        
        return {"success": True, "message": f"Purga de Logs completada. {total_deleted} registros antiguos eliminados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
