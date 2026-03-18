from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from pydantic import BaseModel
from database import get_collection
from routers.auth import require_current_user
from datetime import datetime
import re
import os
import shutil
import uuid

router = APIRouter()

# Ya no usamos BaseModel FundarClub porque FormData requiere recibir campos sueltos
# class FundarClub(BaseModel): ...

@router.post("/club/fundar")
async def fundar_club(
    nombre: str = Form(...),
    color: str = Form(...),
    logo: UploadFile = File(...),
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
    nombre = nombre.strip()
    color = color.strip()
    
    if len(nombre) < 3 or len(nombre) > 32:
        raise HTTPException(status_code=400, detail="El nombre del equipo debe tener entre 3 y 32 caracteres.")
        
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
        raise HTTPException(status_code=400, detail="El formato del color debe ser Hexadecimal (ej. #FF0000).")
        
    # Validar Archivo
    if not logo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo subido debe ser una imagen.")

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

    # --- Guardado Físico en la VPS ---
    UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "escudos"))
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = os.path.splitext(logo.filename)[1]
    if not file_ext:
        file_ext = ".png" # fallback

    safe_name = re.sub(r'[^a-zA-Z0-9]', '', nombre)
    unique_filename = f"{current_user['sub']}_{safe_name}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen en el servidor: {str(e)}")
        
    public_logo_url = f"http://104.243.47.46/uploads/escudos/{unique_filename}"

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
