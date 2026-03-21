import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_haxball():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    db_name = "haxball"
    
    print(f"--- DB: {db_name} ---")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    for name in ["jugadores", "agentes_libres"]:
        count = await db[name].count_documents({})
        print(f"[{name}] -> {count} docs")
        if count > 0:
            doc = await db[name].find_one({}, {"_id": 0})
            print(f"   Sample {name}: {doc}")

if __name__ == "__main__":
    asyncio.run(check_haxball())
