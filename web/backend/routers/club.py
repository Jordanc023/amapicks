from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from database import get_collection
from routers.auth import require_current_user
from datetime import datetime
import re
import os
import uuid
import base64

router = APIRouter()

class FundarClubRequest(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=32)
    color: str = Field(..., pattern=r'^#(?:[0-9a-fA-F]{3}){1,2}$')
    logo_url: str = Field(..., min_length=10)

@router.post("/club/fundar")
async def fundar_club(
    payload: FundarClubRequest,
    current_user: dict = Depends(require_current_user)
):
    """ Endpoint para que un DT sin equipo pueda fundar su club. """
    # 1. Validar estado REAL en MongoDB (para evitar Tokens cacheados/desactualizados)
    jugadores_col = get_collection("jugadores")
    jugador_db = await jugadores_col.find_one({"discord_id": current_user["sub"]})
    
    if not jugador_db:
        raise HTTPException(status_code=403, detail="Usuario no encontrado en la base de datos.")
        
    es_dt = jugador_db.get("es_dt", False)
    equipo_actual = jugador_db.get("equipo")
    
    if not es_dt:
        raise HTTPException(status_code=403, detail="No tienes una Licencia de Director Técnico válida. Ya no tienes permisos de Fundador.")
    
    if equipo_actual:
        raise HTTPException(status_code=400, detail="Ya diriges o fundaste un equipo recientemente. No puedes fundar otro.")
        
    # 2. Validar Inputs
    nombre = payload.nombre.strip()
    color = payload.color.strip()
    public_logo_url = payload.logo_url.strip()

    if not public_logo_url.startswith("http"):
        raise HTTPException(status_code=400, detail="La URL del logo debe empezar con http:// o https://")

    # 3. Validar si ya existe en BD
    equipos_col = get_collection("equipos")
    existente = await equipos_col.find_one({"nombre": {"$regex": f"^{nombre}$", "$options": "i"}})
    if existente:
        raise HTTPException(status_code=400, detail=f"El nombre '{nombre}' ya está registrado en la Liga.")
        
    pendientes_col = get_collection("clubes_pendientes_creacion")
    pendiente = await pendientes_col.find_one({"nombre": {"$regex": f"^{nombre}$", "$options": "i"}})
    if pendiente:
        raise HTTPException(status_code=400, detail="Este nombre de equipo ya se encuentra en trámite de fundación.")

    # Permitir una sola solicitud por usuario
    ya_pidio = await pendientes_col.find_one({"discord_id": current_user["sub"]})
    if ya_pidio:
        raise HTTPException(status_code=400, detail="Ya has enviado una solicitud, espera a que sea procesada.")

    # 4. Enviar a colección temporal para que el Bot lo procese
    await pendientes_col.insert_one({
        "discord_id": current_user["sub"],
        "dt_name": current_user["name"],
        "nombre": nombre,
        "color": color,
        "logo_url": public_logo_url,
        "guild_id": current_user.get("guild_id"),
        "fecha_solicitud": datetime.utcnow()
    })
    
    return {"success": True, "message": "¡Solicitud enviada! El sistema de la liga está inaugurando tu club. Revisa el servidor de Discord en unos segundos."}
