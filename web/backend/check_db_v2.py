import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_db():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "liga_bot")
    
    print(f"--- DB: {db_name} ---")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    try:
        collections = await db.list_collection_names()
        for name in collections:
            count = await db[name].count_documents({})
            print(f"[{name}] -> {count} docs")
            if count > 0:
                doc = await db[name].find_one({}, {"_id": 0})
                # Print keys to avoid huge output
                print(f"   Keys: {list(doc.keys())}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
