import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_all_collections():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "liga_bot")
    
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    collections = await db.list_collection_names()
    print(f"Database: {db_name}")
    for name in sorted(collections):
        count = await db[name].count_documents({})
        print(f"[{name}] -> {count} docs")

if __name__ == "__main__":
    asyncio.run(check_all_collections())
