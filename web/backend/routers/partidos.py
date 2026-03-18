from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from database import get_db

from .auth import require_current_user, require_admin

router = APIRouter()

# Modelos Pydantic
class PartidoCreate(BaseModel):
    equipo_local: str
    equipo_visitante: str
    fecha_hora: str
    jornada: Optional[int] = None
    fase: Optional[str] = "Liga Regular"

class GolesJugador(BaseModel):
    discord_id: str
    goles: int
    asistencias: int
    es_mvp: Optional[bool] = False

class PartidoReporte(BaseModel):
    goles_local: int
    goles_visitante: int
    jugadores_local: List[GolesJugador] = []
    jugadores_visitante: List[GolesJugador] = []
    evidencia_url: Optional[str] = None
    notas_admin: Optional[str] = None

@router.get("/partidos")
async def listar_partidos(
    estado: Optional[str] = None, 
    db = Depends(get_db) # Acceso público o privado
):
    filtros = {}
    if estado:
        filtros["estado"] = estado
    
    cursor = db.partidos.find(filtros).sort("fecha_hora", 1)
    partidos = await cursor.to_list(length=100)
    
    for p in partidos:
        p["_id"] = str(p["_id"])
        
    return partidos

@router.post("/partidos")
async def programar_partido(
    partido: PartidoCreate, 
    user = Depends(require_admin), 
    db = Depends(get_db)
):
    nuevo_partido = {
        "guild_id": user.get("guild_id", "0"),
        "equipo_local": partido.equipo_local,
        "equipo_visitante": partido.equipo_visitante,
        "fecha_hora": partido.fecha_hora,
        "jornada": partido.jornada,
        "fase": partido.fase,
        "estado": "pendiente", # pendiente | auditoria | finalizado
        "creado_por": user.get("sub", "unknown"),
        "creado_en": datetime.now(),
        "reporte": None
    }
    
    result = await db.partidos.insert_one(nuevo_partido)
    return {"message": "Partido programado", "id": str(result.inserted_id)}

@router.post("/partidos/{partido_id}/directo")
async def reportar_resultado_directo(
    partido_id: str, 
    reporte: PartidoReporte, 
    user = Depends(require_admin), 
    db = Depends(get_db)
):
    try:
        pid = ObjectId(partido_id)
    except:
        raise HTTPException(status_code=400, detail="ID Invalido")
        
    partido_db = await db.partidos.find_one({"_id": pid})
    if not partido_db:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
        
    if partido_db.get("estado") == "finalizado":
        raise HTTPException(status_code=400, detail="El partido ya esta cerrado/aprobado")

    # LOGICA DE ASIGNACION DE PUNTOS
    g_local = reporte.goles_local
    g_visitante = reporte.goles_visitante
    
    # Determinar ganador/perdedor
    victoria_local = g_local > g_visitante
    victoria_visitante = g_visitante > g_local
    empate = g_local == g_visitante

    # Preparar el reporte final
    reporte_dict = reporte.dict()
    reporte_dict["reportado_por"] = user.get("sub", "unknown")
    reporte_dict["fecha_reporte"] = datetime.now()

    # 1. Finalizar partido en BD
    await db.partidos.update_one(
        {"_id": pid},
        {"$set": {
            "estado": "finalizado",
            "goles_local": g_local,
            "goles_visitante": g_visitante,
            "reporte_final": reporte_dict,
            "aprobado_por": user.get("sub", "unknown")
        }}
    )
    
    # 2. Actualizar Tabla de Posiciones de Equipo Local
    await db.equipos.update_one(
        {"nombre": partido_db["equipo_local"]},
        {"$inc": {
            "estadisticas_temporada.goles_favor": g_local,
            "estadisticas_temporada.goles_contra": g_visitante,
            "estadisticas_temporada.victorias": 1 if victoria_local else 0,
            "estadisticas_temporada.empates": 1 if empate else 0,
            "estadisticas_temporada.derrotas": 1 if victoria_visitante else 0
        }}
    )
    
    # 3. Actualizar Tabla de Posiciones de Equipo Visitante
    await db.equipos.update_one(
        {"nombre": partido_db["equipo_visitante"]},
        {"$inc": {
            "estadisticas_temporada.goles_favor": g_visitante,
            "estadisticas_temporada.goles_contra": g_local,
            "estadisticas_temporada.victorias": 1 if victoria_visitante else 0,
            "estadisticas_temporada.empates": 1 if empate else 0,
            "estadisticas_temporada.derrotas": 1 if victoria_local else 0
        }}
    )

    # 4. Actualizar estadísticas individuales de jugadores reportados
    todos_jugadores_reporte = reporte.jugadores_local + reporte.jugadores_visitante
    for jug in todos_jugadores_reporte:
        inc_fields = {}
        if jug.goles > 0:
            inc_fields["estadisticas_temporada.goles"] = jug.goles
        if jug.asistencias > 0:
            inc_fields["estadisticas_temporada.asistencias"] = jug.asistencias
        if jug.es_mvp:
            inc_fields["estadisticas_temporada.mvps"] = 1

        if inc_fields:
            await db.jugadores.update_one(
                {"discord_id": jug.discord_id},
                {"$inc": inc_fields}
            )
    
    return {"message": "✅ Resultado Oficial Reportado y Puntos actualizados con éxito en la Tabla."}

@router.patch("/partidos/{partido_id}/aprobar")
async def aprobar_resultado(
    partido_id: str, 
    user = Depends(require_admin), 
    db = Depends(get_db)
):
    try:
        pid = ObjectId(partido_id)
    except:
        raise HTTPException(status_code=400, detail="ID Invalido")
        
    partido = await db.partidos.find_one({"_id": pid})
    if not partido or partido.get("estado") != "auditoria":
        raise HTTPException(status_code=404, detail="Debe haber un reporte en auditoría")
        
    reporte = partido.get("reporte_temporal", {})
    if not reporte:
        raise HTTPException(status_code=400, detail="Sin reporte temporal")
        
    # LOGICA DE ASIGNACION DE PUNTOS
    g_local = reporte["goles_local"]
    g_visitante = reporte["goles_visitante"]
    pts_local = 3 if g_local > g_visitante else (1 if g_local == g_visitante else 0)
    pts_visitante = 3 if g_visitante > g_local else (1 if g_local == g_visitante else 0)
    
    # 1) Cerrar Partido Oficialmente
    await db.partidos.update_one(
        {"_id": pid},
        {"$set": {
            "estado": "finalizado",
            "goles_local": g_local,
            "goles_visitante": g_visitante,
            "reporte_final": reporte,
            "aprobado_por": user.get("sub", "unknown")
        },
        "$unset": {"reporte_temporal": ""}
        }
    )
    
    # IMPORTANTE: Aquí se deberían actualizar las Estadísticas (win/loss, goles de jugadores) usando db.jugadores
    # Y los puntajes de equipo (db.equipos)
    # Por mantenerlo directo, lo dejamos como TODO para integrarlo con funciones utils.

    return {"message": "¡El partido ha sido APROBADO oficialmente!"}

@router.patch("/partidos/{partido_id}/rechazar")
async def rechazar_resultado(
    partido_id: str, 
    user = Depends(require_admin), 
    db = Depends(get_db)
):
    try:
        pid = ObjectId(partido_id)
    except:
        raise HTTPException(status_code=400, detail="ID Invalido")
        
    await db.partidos.update_one(
        {"_id": pid},
        {"$set": {"estado": "pendiente"},
         "$unset": {"reporte_temporal": ""}
        }
    )
    return {"message": "Reporte rechazado. El partido vuelve a estado PENDIENTE."}

@router.delete("/partidos/{partido_id}")
async def eliminar_partido(
    partido_id: str, 
    user = Depends(require_admin), 
    db = Depends(get_db)
):
    try:
        pid = ObjectId(partido_id)
    except:
        raise HTTPException(status_code=400, detail="ID Invalido")
    
    # Verificar que el partido existe
    partido = await db.partidos.find_one({"_id": pid})
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    # Eliminar el partido
    await db.partidos.delete_one({"_id": pid})
    
    return {"message": "Partido eliminado correctamente"}
