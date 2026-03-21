import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_db():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "liga_bot")
    
    print(f"--- DATABASE STATUS ---")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    collections = await db.list_collection_names()
    print(f"Colecciones totales: {len(collections)}")
    print(f"Nombres: {collections}")
    
    for name in ["jugadores", "agentes_libres"]:
        count = await db[name].count_documents({})
        print(f"Collection '{name}': {count} documents")
        if count > 0:
            doc = await db[name].find_one({}, {"_id": 0})
            print(f"  Sample: {doc}")

if __name__ == "__main__":
    asyncio.run(check_db())
