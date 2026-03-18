from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import httpx
from jose import jwt, JWTError
from datetime import datetime, timedelta
from database import get_collection
from typing import Optional

# --- SEGURIDAD: Bearer token ---
security = HTTPBearer()


async def require_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependencia que valida el JWT y retorna los datos del usuario."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "supersecretkey_cambiar_en_produccion"), algorithms=["HS256"])
        if payload.get("exp") and payload["exp"] < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expirado")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependencia que valida que el usuario sea administrador."""
    user = await require_current_user(credentials)
    if not user.get("admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren permisos de administrador.")
    return user

router = APIRouter()

# --- CONFIG ---
# (Idealmente en .env)
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
# Ajusta esto si tu puerto/dominio cambia.
# Debe coincidir EXACTAMENTE con lo que pongas en Discord Dev Portal
DISCORD_REDIRECT_URI = "http://20.81.152.127:8001/api/auth/callback" 
FRONTEND_URL = "http://20.81.152.127:5173"

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_cambiar_en_produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 semana

# --- OAUTH2 URLS ---
DISCORD_LOGIN_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

# --- HELPERS ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- ENDPOINTS ---

@router.get("/auth/login")
async def login_discord():
    """Redirige al usuario a Discord para aprobar la app."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Faltan credenciales de Discord en el servidor.")
        
    scope = "identify guilds" # 'guilds' si queremos validar pertenencia al server
    return RedirectResponse(
        f"{DISCORD_LOGIN_URL}?response_type=code&client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&scope={scope}"
    )

@router.get("/auth/callback")
async def callback_discord(code: str):
    """Callback de Discord. Intercambia código por Token y genera JWT."""
    
    # 1. Intercambiar code por Access Token
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        token_response = await client.post(DISCORD_TOKEN_URL, data=data, headers=headers)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener token de Discord")
        
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        # 2. Obtener datos del usuario
        user_response = await client.get(DISCORD_USER_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener perfil de Discord")
            
        discord_user = user_response.json()
        
    # 3. Determinar Roles (DT, Admin, Jugador)
    discord_id = discord_user.get("id")
    username = discord_user.get("username")
    avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_user.get('avatar')}.png"
    
    # --- Lógica de Roles ---
    es_admin = False
    team_data = None
    
    # A. Chequear si es Admin (Hardcoded por ahora o por ID especifico en .env)
    # Ejemplo: Si el ID coincide con el del Developer
    ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
    if discord_id in ADMIN_IDS:
        es_admin = True
    
    # B. Chequear si es DT (Buscar en colección 'jugadores')
    jugadores_col = get_collection("jugadores")
    print(f"Buscando a {username} con discord_id: '{discord_id}' (Tipo: {type(discord_id)})")
    jugador_doc = await jugadores_col.find_one({"discord_id": str(discord_id)})
    print(f"Resultado en BD: {jugador_doc}")
    
    es_dt_asignado = False
    equipo_del_dt = None
    guild_id = None
    
    if jugador_doc and jugador_doc.get("es_dt"):
        print("EL USUARIO TIENE ES_DT = TRUE")
        es_dt_asignado = True
        equipo_del_dt = jugador_doc.get("equipo")
        guild_id = jugador_doc.get("guild_id")
    else:
        print("EL USUARIO NO TIENE ES_DT o NO FUE ENCONTRADO")

    # 4. Generar JWT
    token_data = {
        "sub": discord_id,
        "name": username,
        "avatar": avatar,
        "admin": es_admin,
        "es_dt": es_dt_asignado,
        "team_name": equipo_del_dt, # Si es None pero es_dt=True, el user tiene licencia para fundar
        "guild_id": guild_id
    }
    
    jwt_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # 5. Redirigir al Frontend con el token
    return RedirectResponse(f"{FRONTEND_URL}/auth/callback?token={jwt_token}")

@router.get("/auth/me")
async def get_current_user_info(token: str):
    """Decodifica el token para validar sesión en frontend (opcional si frontend decodifica JWT)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
