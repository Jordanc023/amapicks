from fastapi import APIRouter, HTTPException, Body
from database import get_collection
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter()

# --- Models ---
class FichajeRequest(BaseModel):
    jugador_id: str         # Discord ID del jugador
    equipo_comprador_id: str # ID o Nombre del equipo comprador (role_id o nombre)
    precio_pagado: int      # El precio al momento de la compra (para registro)

# --- Endpoints ---

@router.post("/fichajes")
async def realizar_fichaje(fichaje: FichajeRequest):
    """
    Realiza un fichaje (Clausulazo).
    1. Verifica que el equipo comprador tenga fondos.
    2. Resta fondos al comprador.
    3. Suma fondos al vendedor (si tiene equipo).
    4. Actualiza el equipo del jugador.
    5. Registra el historial.
    """
    equipos_col = get_collection("equipos")
    jugadores_col = get_collection("jugadores")
    
    # 1. Obtener datos
    # Buscamos equipo comprador por role_id (int) o nombre
    query_comprador = {
        "$or": [
            {"role_id": int(fichaje.equipo_comprador_id) if fichaje.equipo_comprador_id.isdigit() else None},
            {"nombre": fichaje.equipo_comprador_id},
            {"role_name": fichaje.equipo_comprador_id}
        ]
    }
    # Limpiar nulls
    query_comprador["$or"] = [q for q in query_comprador["$or"] if list(q.values())[0] is not None]
    
    equipo_comprador = await equipos_col.find_one(query_comprador)
    if not equipo_comprador:
        raise HTTPException(status_code=404, detail="Equipo comprador no encontrado")
        
    jugador = await jugadores_col.find_one({"discord_id": fichaje.jugador_id})
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    # Verificar si el jugador ya es del equipo
    if jugador.get("equipo") == equipo_comprador.get("nombre"):
        raise HTTPException(status_code=400, detail="El jugador ya pertenece a este equipo")

    # 2. Validar Presupuesto
    precio = fichaje.precio_pagado
    presupuesto_actual = equipo_comprador.get("presupuesto", 0)
    
    if presupuesto_actual < precio:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes. Tienes ${presupuesto_actual} y necesitas ${precio}")

    # 3. Identificar Vendedor (para pagarle)
    equipo_vendedor_nombre = jugador.get("equipo")
    equipo_vendedor = None
    if equipo_vendedor_nombre:
        equipo_vendedor = await equipos_col.find_one({"nombre": equipo_vendedor_nombre})

    # --- INICIO TRANSACCIÓN (Simulada/Manual en Mongo) ---
    
    # A. Cobrar al Comprador
    await equipos_col.update_one(
        {"_id": equipo_comprador["_id"]},
        {"$inc": {"presupuesto": -precio}}
    )
    
    # B. Pagar al Vendedor (Si existe) -> Opcional: ¿100% del valor? ¿O se quema algo?
    # Por ahora 100% al vendedor.
    if equipo_vendedor:
        await equipos_col.update_one(
            {"_id": equipo_vendedor["_id"]},
            {"$inc": {"presupuesto": precio}}
        )
        # Actualizar plantilla vendedor (sacar al jugador)
        await equipos_col.update_one(
             {"_id": equipo_vendedor["_id"]},
             {"$pull": {"plantilla": {"discord_id": jugador["discord_id"]}}}
        )

    # C. Transferir Jugador
    nuevo_historial = {
        "timestamp": datetime.utcnow().isoformat(),
        "action_type": "FICHAJE",
        "details": {
            "equipo_origen": equipo_vendedor_nombre,
            "equipo_destino": equipo_comprador.get("nombre"),
            "precio": precio
        }
    }
    
    await jugadores_col.update_one(
        {"_id": jugador["_id"]},
        {
            "$set": {
                "equipo": equipo_comprador.get("nombre"),
                "fecha_fichaje": datetime.utcnow().isoformat()
            },
            "$push": {"historial": nuevo_historial}
        }
    )

    # D. Agregar a plantilla comprador (Si mantenemos array en equipos)
    # Es mejor traer los datos frescos del jugador para meter al array
    jugador_actualizado = await jugadores_col.find_one({"_id": jugador["_id"]})
    # Simplificamos el objeto para el array plantilla
    jugador_summary = {
        "discord_id": jugador_actualizado["discord_id"],
        "nombre": jugador_actualizado["nombre"],
        "posicion": jugador_actualizado.get("posicion"),
        "avatar_url": jugador_actualizado.get("avatar_url"),
        "media": jugador_actualizado.get("media")
    }
    
    await equipos_col.update_one(
        {"_id": equipo_comprador["_id"]},
        {"$push": {"plantilla": jugador_summary}}
    )

    # E. Registrar auditoría financiera
    auditoria_col = get_collection("transacciones_financieras")
    await auditoria_col.insert_one({
        "timestamp": datetime.utcnow().isoformat(),
        "tipo": "TRANSFERENCIA",
        "actor": equipo_comprador.get("nombre"),
        "actor_id": str(equipo_comprador["_id"]),
        "monto": precio,
        "detalles": f"El equipo {equipo_comprador.get('nombre')} compró a {jugador['nombre']}" + 
                    (f" desde el equipo {equipo_vendedor_nombre}" if equipo_vendedor_nombre else " (Agente Libre)")
    })

    # TODO: Enviar Webhook a Discord aqui
    # await enviar_webhook_discord(...)

    return {
        "status": "success",
        "message": f"Fuchaje completado: {jugador['nombre']} al {equipo_comprador.get('nombre')}",
        "nuevo_presupuesto": presupuesto_actual - precio
    }
