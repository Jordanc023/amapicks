import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_audit():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    db = client["liga_bot"]
    
    logs = await db["audit_logs"].find().sort("timestamp", -1).limit(20).to_list(None)
    print("--- Last 20 Audit Logs ---")
    for log in logs:
        print(f"[{log.get('timestamp')}] {log.get('accion')} - {log.get('detalles')}")

if __name__ == "__main__":
    asyncio.run(check_audit())
