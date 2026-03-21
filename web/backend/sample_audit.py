import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def get_sample():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    db = client["liga_bot"]
    
    sample = await db["audit_logs"].find_one()
    if sample:
        sample["_id"] = str(sample["_id"])
        print(json.dumps(sample, indent=2, cls=DateTimeEncoder))
    else:
        print("No audit logs found.")

if __name__ == "__main__":
    asyncio.run(get_sample())
