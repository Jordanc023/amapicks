import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def deep_check():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    
    dbs = await client.list_database_names()
    print(f"Databases found: {dbs}")
    
    for db_name in ["haxball", "liga_bot"]:
        if db_name not in dbs:
            print(f"Database {db_name} NOT FOUND in cluster.")
            continue
            
        db = client[db_name]
        cols = await db.list_collection_names()
        print(f"\n--- Database: {db_name} ({len(cols)} collections) ---")
        for col_name in sorted(cols):
            count = await db[col_name].count_documents({})
            print(f"  [{col_name}] -> {count} docs")
            if count > 0 and col_name in ["jugadores", "agentes_libres", "equipos"]:
                sample = await db[col_name].find_one({}, {"_id": 0})
                print(f"    Sample: {str(sample)[:100]}...")

if __name__ == "__main__":
    asyncio.run(deep_check())
