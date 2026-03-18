from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "liga_bot")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

def get_collection(name: str):
    """Devuelve una colección de MongoDB de forma asíncrona."""
    return db[name]

async def get_db():
    """Dependency para FastAPI: retorna la instancia de la base de datos."""
    return db
