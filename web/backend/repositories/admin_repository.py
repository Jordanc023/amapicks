from datetime import datetime
from database import get_collection
from typing import Optional, Dict, Any, List

class AdminRepository:
    """Repositorio para separar la lógica de BBDD relacionada a la administración."""
    
    @staticmethod
    async def get_equipo_by_id_or_name(equipo_id: str) -> Optional[Dict[str, Any]]:
        equipos_col = get_collection("equipos")
        query_conditions = []
        if equipo_id.isdigit():
            query_conditions.append({"role_id": int(equipo_id)})
        query_conditions.append({"nombre": equipo_id})
        query_conditions.append({"role_name": equipo_id})
        
        query = {"$or": query_conditions}
        return await equipos_col.find_one(query)

    @staticmethod
    async def update_equipo_presupuesto(equipo_db_id: Any, nuevo_presupuesto: int) -> bool:
        equipos_col = get_collection("equipos")
        result = await equipos_col.update_one(
            {"_id": equipo_db_id},
            {"$set": {"presupuesto": nuevo_presupuesto}}
        )
        return result.modified_count > 0

    @staticmethod
    async def log_transaccion_financiera(actor: str, actor_id: str, equipo_id: str, equipo_nombre: str, dinero_movido: int, nuevo_presupuesto: int):
        auditoria_col = get_collection("transacciones_finacieras")
        accion_txt = "inyectó" if dinero_movido > 0 else "retiró"
        monto_abs = abs(dinero_movido)
        
        await auditoria_col.insert_one({
            "timestamp": datetime.utcnow().isoformat(),
            "tipo": "ADMIN_BUDGET_CHANGE",
            "actor": actor,
            "actor_id": actor_id,
            "equipo_id": equipo_id,
            "monto": dinero_movido,
            "detalles": f"Admin {actor} {accion_txt} ${monto_abs} al equipo {equipo_nombre} (Nuevo saldo: ${nuevo_presupuesto})"
        })

    @staticmethod
    async def update_player_economy(discord_id: str, precio: int, clausula: int) -> bool:
        jugadores_col = get_collection("jugadores")
        agentes_col = get_collection("agentes_libres")
        
        update_data = {
            "precio": precio,
            "clausula": clausula
        }
        
        result = await jugadores_col.update_one({"discord_id": discord_id}, {"$set": update_data})
        if result.matched_count == 0:
            result = await agentes_col.update_one({"discord_id": discord_id}, {"$set": update_data})
            
        return result.matched_count > 0

    @staticmethod
    async def update_player_stats(discord_id: str, update_data: Dict[str, int]) -> bool:
        jugadores_col = get_collection("jugadores")
        result = await jugadores_col.update_one(
            {"discord_id": discord_id},
            {"$set": update_data}
        )
        return result.matched_count > 0

    @staticmethod
    async def update_player_ban(discord_id: str, baneado: bool, motivo: Optional[str]) -> bool:
        jugadores_col = get_collection("jugadores")
        agentes_col = get_collection("agentes_libres")
        
        update_data = {
            "baneado": baneado,
            "motivo_ban": motivo
        }
        
        result = await jugadores_col.update_one({"discord_id": discord_id}, {"$set": update_data})
        if result.matched_count == 0:
            result = await agentes_col.update_one({"discord_id": discord_id}, {"$set": update_data})
            
        return result.matched_count > 0

    @staticmethod
    async def get_auditoria_logs(limit: int) -> List[Dict[str, Any]]:
        auditoria_col = get_collection("transacciones_finacieras")
        cursor = auditoria_col.find({}).sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        return logs
