import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def generate_report():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    
    report = {"databases": {}}
    
    dbs = await client.list_database_names()
    for db_name in dbs:
        if db_name in ["admin", "local", "config"]:
            continue
        db = client[db_name]
        cols = await db.list_collection_names()
        report["databases"][db_name] = {"collection_count": len(cols), "collections": {}}
        for col_name in cols:
            count = await db[col_name].count_documents({})
            report["databases"][db_name]["collections"][col_name] = count

    with open("db_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("Report generated in db_report.json")

if __name__ == "__main__":
    asyncio.run(generate_report())
