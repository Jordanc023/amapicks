import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def force_sync():
    # URL de conexión de MongoDB (basada en el estándar de la app)
    mongo_url = "mongodb://localhost:27017" # Ajustar si es diferente, pero suele ser el default
    client = AsyncIOMotorClient(mongo_url)
    db = client['liga_haxball'] # Nombre de la BD
    config_col = db['config_col']
    
    print("Enviando comando force_sync a MongoDB...")
    await config_col.update_one(
        {'_id': 'bot_commands'},
        {'$set': {'force_sync': True}},
        upsert=True
    )
    print("✅ Comando enviado. El bot debería sincronizar sus comandos en el próximo minuto.")
    client.close()

if __name__ == "__main__":
    asyncio.run(force_sync())
