import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def list_all_dbs():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    
    client = AsyncIOMotorClient(uri)
    try:
        dbs = await client.list_database_names()
        print(f"Databases: {dbs}")
        for db_name in dbs:
            db = client[db_name]
            collections = await db.list_collection_names()
            print(f"[{db_name}] -> {len(collections)} collections")
            if "jugadores" in collections:
                count = await db["jugadores"].count_documents({})
                print(f"   !!! Found 'jugadores' in {db_name} with {count} docs")
            if "agentes_libres" in collections:
                count = await db["agentes_libres"].count_documents({})
                print(f"   !!! Found 'agentes_libres' in {db_name} with {count} docs")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(list_all_dbs())
