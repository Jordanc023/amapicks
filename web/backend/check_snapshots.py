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

async def check_snapshots():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    db = client["liga_bot"]
    
    seasons = await db["temporadas"].find().to_list(None)
    print(f"--- Found {len(seasons)} seasons ---")
    for s in seasons:
        has_players = "snapshot_jugadores" in s and s["snapshot_jugadores"]
        has_teams = "snapshot_equipos" in s and s["snapshot_equipos"]
        num_players = len(s.get("snapshot_jugadores", []))
        num_teams = len(s.get("snapshot_equipos", []))
        print(f"Season {s.get('numero')}: {s.get('nombre')} - Activa: {s.get('activa')} - Players Snapshot: {num_players} - Teams Snapshot: {num_teams}")

if __name__ == "__main__":
    asyncio.run(check_snapshots())
