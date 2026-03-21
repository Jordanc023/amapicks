from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Cargar variables de entorno
load_dotenv()


app = FastAPI(title="AMAPICKS API", version="1.0.0")

raw_cors_origins = os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_URL", "http://localhost:5173"))
cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client[os.getenv("DB_NAME", "liga_bot")]

# Importar Routers
from routers import liga, auth, admin, estadisticas, partidos, ligas_manager

app.include_router(liga.router, prefix="/api", tags=["liga"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(estadisticas.router, prefix="/api", tags=["estadisticas"])
app.include_router(partidos.router, prefix="/api", tags=["partidos"])
app.include_router(ligas_manager.router, prefix="/api/admin", tags=["ligas"])


@app.get("/")
async def read_root():
    return {"message": "Damas y caballeros, bienvenidos a AMAPICKS API v1.0"}

@app.get("/health")
async def health_check():
    try:
        # Verificar conexión BD
        await db.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
