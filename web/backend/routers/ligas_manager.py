from fastapi import APIRouter, HTTPException, Depends
from database import get_collection
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

router = APIRouter()

# ============================================================
# MODELOS
# ============================================================

class LigaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""
    division: str  # "D1", "D2", etc.
    max_equipos: int = 12
    formato: str = "todos_contra_todos"  # round_robin, eliminatoria, etc.
    jornadas_ida: int = 11  # (max_equipos - 1)
    jornadas_vuelta: int = 11  # igual a ida para round robin
    puntos_victoria: int = 3
    puntos_empate: int = 1
    puntos_derrota: int = 0
    playoffs_habilitados: bool = True
    clasificados_playoffs: int = 4
    jornada_paron_copa: int = 11  # Jornada donde se detiene la liga para copa
    activa: bool = True
    color_identificacion: str = "#FFD700"  # Color para UI
    # NUEVO: Configuración de Copa
    copa_habilitada: bool = True
    equipos_copa_total: int = 24  # Total de equipos en copa
    equipos_sembrados: int = 8  # Top 8 van directo a octavos
    ronda_preliminar: bool = True  # 16 equipos juegan preliminar
    factor_rival_habilitado: bool = True  # Sistema de bono por dificultad

class LigaCreate(LigaBase):
    pass

class LigaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    max_equipos: Optional[int] = None
    formato: Optional[str] = None
    jornadas_ida: Optional[int] = None
    jornadas_vuelta: Optional[int] = None
    puntos_victoria: Optional[int] = None
    puntos_empate: Optional[int] = None
    puntos_derrota: Optional[int] = None
    playoffs_habilitados: Optional[bool] = None
    clasificados_playoffs: Optional[int] = None
    jornada_paron_copa: Optional[int] = None
    activa: Optional[bool] = None
    color_identificacion: Optional[str] = None
    # NUEVO: Configuración Copa
    copa_habilitada: Optional[bool] = None
    equipos_copa_total: Optional[int] = None
    equipos_sembrados: Optional[int] = None
    ronda_preliminar: Optional[bool] = None
    factor_rival_habilitado: Optional[bool] = None

class LigaResponse(LigaBase):
    id: str
    created_at: datetime
    updated_at: datetime
    total_equipos: int = 0
    jornada_actual: int = 1
    estado: str = "configuracion"  # configuracion, en_curso, paron_copa, finalizada

class AsignarEquipoLiga(BaseModel):
    equipo_id: str  # puede ser nombre o _id
    liga_id: str

class CambiarLigaActiva(BaseModel):
    liga_id: str

# ============================================================
# HELPERS
# ============================================================

def serialize_liga(liga_doc) -> dict:
    """Convierte un documento de liga a formato serializable."""
    return {
        "id": str(liga_doc.get("_id")),
        "nombre": liga_doc.get("nombre"),
        "descripcion": liga_doc.get("descripcion", ""),
        "division": liga_doc.get("division", "D1"),
        "max_equipos": liga_doc.get("max_equipos", 12),
        "formato": liga_doc.get("formato", "todos_contra_todos"),
        "jornadas_ida": liga_doc.get("jornadas_ida", 11),
        "jornadas_vuelta": liga_doc.get("jornadas_vuelta", 11),
        "puntos_victoria": liga_doc.get("puntos_victoria", 3),
        "puntos_empate": liga_doc.get("puntos_empate", 1),
        "puntos_derrota": liga_doc.get("puntos_derrota", 0),
        "playoffs_habilitados": liga_doc.get("playoffs_habilitados", True),
        "clasificados_playoffs": liga_doc.get("clasificados_playoffs", 4),
        "jornada_paron_copa": liga_doc.get("jornada_paron_copa", 11),
        "activa": liga_doc.get("activa", True),
        "color_identificacion": liga_doc.get("color_identificacion", "#FFD700"),
        "created_at": liga_doc.get("created_at", datetime.utcnow()),
        "updated_at": liga_doc.get("updated_at", datetime.utcnow()),
        "total_equipos": liga_doc.get("total_equipos", 0),
        "jornada_actual": liga_doc.get("jornada_actual", 1),
        "estado": liga_doc.get("estado", "configuracion")
    }

# ============================================================
# ENDPOINTS CRUD LIGAS
# ============================================================

@router.post("/ligas", response_model=LigaResponse)
async def crear_liga(liga: LigaCreate):
    """
    Crea una nueva liga (D1, D2, etc.) con configuración personalizada.
    """
    ligas_col = get_collection("ligas")
    
    # Verificar si ya existe una liga con el mismo nombre/division
    existente = await ligas_col.find_one({
        "$or": [
            {"nombre": liga.nombre},
            {"division": liga.division}
        ]
    })
    
    if existente:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe una liga con nombre '{liga.nombre}' o división '{liga.division}'"
        )
    
    # Calcular jornadas automáticamente si es round robin
    if liga.formato == "todos_contra_todos":
        liga.jornadas_ida = liga.max_equipos - 1
        liga.jornadas_vuelta = liga.max_equipos - 1
    
    liga_doc = {
        **liga.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "total_equipos": 0,
        "jornada_actual": 1,
        "estado": "configuracion"
    }
    
    result = await ligas_col.insert_one(liga_doc)
    
    # Crear configuración inicial de temporada para esta liga
    config_liga_col = get_collection("config_liga")
    await config_liga_col.update_one(
        {"liga_id": str(result.inserted_id)},
        {"$set": {
            "liga_id": str(result.inserted_id),
            "nombre_liga": liga.nombre,
            "division": liga.division,
            "temporada": datetime.now().year,
            "mercado_abierto": False,
            "inscripcion_copa_abierta": False,
            "created_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {
        **liga_doc,
        "id": str(result.inserted_id)
    }

@router.get("/ligas", response_model=List[LigaResponse])
async def listar_ligas(activas_only: bool = False):
    """
    Lista todas las ligas disponibles.
    Si activas_only=True, solo devuelve ligas activas.
    """
    ligas_col = get_collection("ligas")
    
    query = {"activa": True} if activas_only else {}
    
    ligas_cursor = ligas_col.find(query).sort("created_at", -1)
    ligas = await ligas_cursor.to_list(length=100)
    
    return [serialize_liga(l) for l in ligas]

@router.get("/ligas/{liga_id}", response_model=LigaResponse)
async def obtener_liga(liga_id: str):
    """
    Obtiene detalles de una liga específica.
    """
    ligas_col = get_collection("ligas")
    
    try:
        liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    except:
        # Si no es un ObjectId válido, buscar por otros campos
        liga = await ligas_col.find_one({"division": liga_id})
    
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    return serialize_liga(liga)

@router.patch("/ligas/{liga_id}", response_model=LigaResponse)
async def actualizar_liga(liga_id: str, update: LigaUpdate):
    """
    Actualiza configuración de una liga.
    """
    ligas_col = get_collection("ligas")
    
    # Construir update dict solo con campos proporcionados
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    # Recalcular jornadas si cambió max_equipos
    if "max_equipos" in update_data and update_data.get("formato", "") == "todos_contra_todos":
        max_eq = update_data["max_equipos"]
        update_data["jornadas_ida"] = max_eq - 1
        update_data["jornadas_vuelta"] = max_eq - 1
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Retornar liga actualizada
    liga_actualizada = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    return serialize_liga(liga_actualizada)

@router.delete("/ligas/{liga_id}")
async def eliminar_liga(liga_id: str):
    """
    Elimina una liga y todos sus datos asociados (⚠️ Peligroso).
    """
    ligas_col = get_collection("ligas")
    partidos_col = get_collection("partidos")
    tabla_col = get_collection("tabla_posiciones")
    config_liga_col = get_collection("config_liga")
    
    # Verificar que existe
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Eliminar datos asociados
    await partidos_col.delete_many({"liga_id": liga_id})
    await tabla_col.delete_many({"liga_id": liga_id})
    await config_liga_col.delete_one({"liga_id": liga_id})
    
    # Desasignar equipos de esta liga
    equipos_col = get_collection("equipos")
    await equipos_col.update_many(
        {"liga_id": liga_id},
        {"$unset": {"liga_id": "", "liga_nombre": ""}}
    )
    
    # Eliminar la liga
    await ligas_col.delete_one({"_id": ObjectId(liga_id)})
    
    return {
        "message": f"Liga '{liga.get('nombre')}' eliminada exitosamente",
        "liga_id": liga_id,
        "eliminados": {
            "partidos": True,
            "tabla": True,
            "config": True
        }
    }

# ============================================================
# GESTIÓN DE EQUIPOS EN LIGAS
# ============================================================

@router.post("/ligas/{liga_id}/equipos")
async def agregar_equipo_a_liga(liga_id: str, equipo_data: AsignarEquipoLiga):
    """
    Asigna un equipo a una liga específica.
    Si al agregar el equipo la liga queda completa, genera el fixture automáticamente.
    """
    ligas_col = get_collection("ligas")
    equipos_col = get_collection("equipos")
    partidos_col = get_collection("partidos")
    
    # Verificar liga
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Verificar capacidad
    equipos_actuales = await equipos_col.count_documents({"liga_id": liga_id})
    max_equipos = liga.get("max_equipos", 12)
    
    if equipos_actuales >= max_equipos:
        raise HTTPException(
            status_code=400, 
            detail=f"La liga ya tiene el máximo de {max_equipos} equipos"
        )
    
    # Buscar equipo (por nombre o _id)
    equipo = None
    
    # Primero intentar buscar por _id si parece un ObjectId válido (24 chars hex)
    if len(equipo_data.equipo_id) == 24:
        try:
            equipo = await equipos_col.find_one({"_id": ObjectId(equipo_data.equipo_id)})
        except:
            pass  # No es un ObjectId válido, continuar con búsqueda por nombre
    
    # Si no se encontró por _id, buscar por nombre o role_name
    if not equipo:
        equipo = await equipos_col.find_one({
            "$or": [
                {"nombre": equipo_data.equipo_id},
                {"role_name": equipo_data.equipo_id}
            ]
        })
    
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    # Verificar si ya está en otra liga
    if equipo.get("liga_id") and equipo.get("liga_id") != liga_id:
        raise HTTPException(
            status_code=400,
            detail=f"El equipo '{equipo.get('nombre')}' ya está asignado a otra liga"
        )
    
    # Asignar a liga
    await equipos_col.update_one(
        {"_id": equipo.get("_id")},
        {"$set": {
            "liga_id": liga_id,
            "liga_nombre": liga.get("nombre"),
            "liga_division": liga.get("division")
        }}
    )
    
    # Calcular nuevo conteo
    nuevo_conteo = equipos_actuales + 1
    
    # Actualizar contador en liga
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": {"total_equipos": nuevo_conteo, "updated_at": datetime.utcnow()}}
    )
    
    # Verificar si la liga está completa y generar fixture automáticamente
    fixture_generado = None
    if nuevo_conteo == max_equipos and liga.get("estado") == "configuracion":
        # Liga completa - generar fixture automáticamente
        try:
            fixture_generado = await _generar_fixture_automatico(liga_id, ligas_col, equipos_col, partidos_col)
        except Exception as e:
            print(f"Error generando fixture automático: {e}")
            fixture_generado = {"error": str(e)}
    
    respuesta = {
        "message": f"Equipo '{equipo.get('nombre')}' asignado a '{liga.get('nombre')}'",
        "equipo": equipo.get("nombre"),
        "liga": liga.get("nombre"),
        "total_equipos_liga": nuevo_conteo,
        "liga_completa": nuevo_conteo == max_equipos
    }
    
    if fixture_generado:
        respuesta["fixture_generado"] = fixture_generado
    
    return respuesta


async def _generar_fixture_automatico(liga_id: str, ligas_col, equipos_col, partidos_col):
    """
    Genera automáticamente el fixture cuando la liga está completa.
    Usa la fecha actual + 7 días como fecha de inicio por defecto.
    """
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        return {"error": "Liga no encontrada"}
    
    # Obtener equipos de la liga
    equipos_cursor = equipos_col.find({"liga_id": liga_id})
    equipos_docs = await equipos_cursor.to_list(length=50)
    
    if len(equipos_docs) < 2:
        return {"error": "Se necesitan al menos 2 equipos"}
    
    equipos_nombres = [eq["nombre"] for eq in equipos_docs]
    
    # Generar fixture
    fixture = _generar_fixture_round_robin_liga(equipos_nombres, liga_id)
    
    # Fecha de inicio: hoy + 7 días por defecto
    from datetime import timedelta
    fecha_base = datetime.utcnow() + timedelta(days=7)
    dias_entre_jornadas = 3
    hora_default = "20:00"
    
    # Crear partidos en BD
    partidos_creados = 0
    for jornada_data in fixture:
        jornada_num = jornada_data["jornada"]
        fecha_jornada = fecha_base + timedelta(days=(jornada_num - 1) * dias_entre_jornadas)
        
        for partido in jornada_data["partidos"]:
            fecha_hora = datetime.combine(
                fecha_jornada.date(), 
                datetime.strptime(hora_default, "%H:%M").time()
            )
            
            await partidos_col.insert_one({
                "guild_id": "0",
                "liga_id": liga_id,
                "liga_nombre": liga.get("nombre"),
                "equipo_local": partido["equipo_local"],
                "equipo_visitante": partido["equipo_visitante"],
                "fecha_hora": fecha_hora.isoformat(),
                "jornada": jornada_num,
                "fase": "Liga Regular",
                "sub_fase": partido.get("fase", "ida"),
                "estado": "pendiente",
                "auto_generado": True,
                "creado_en": datetime.utcnow()
            })
            partidos_creados += 1
    
    # Actualizar estado de la liga a "en_curso"
    total_jornadas = len(fixture)
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": {
            "estado": "en_curso",
            "jornada_actual": 1,
            "total_jornadas": total_jornadas,
            "jornadas_ida": total_jornadas // 2,
            "jornadas_vuelta": total_jornadas // 2,
            "updated_at": datetime.utcnow(),
            "fixture_generado_en": datetime.utcnow(),
            "fecha_inicio": fecha_base.strftime("%Y-%m-%d"),
            "partidos_generados": partidos_creados
        }}
    )
    
    return {
        "message": f"Fixture generado automáticamente para '{liga.get('nombre')}'",
        "equipos": len(equipos_nombres),
        "jornadas_total": total_jornadas,
        "partidos_creados": partidos_creados,
        "fecha_inicio": fecha_base.strftime("%Y-%m-%d"),
        "estado_liga": "en_curso"
    }

@router.delete("/ligas/{liga_id}/equipos/{equipo_id}")
async def remover_equipo_de_liga(liga_id: str, equipo_id: str):
    """
    Remueve un equipo de una liga.
    """
    ligas_col = get_collection("ligas")
    equipos_col = get_collection("equipos")
    
    # Buscar equipo
    equipo = await equipos_col.find_one({
        "$or": [
            {"_id": ObjectId(equipo_id) if len(equipo_id) == 24 else {"$ne": None}},
            {"nombre": equipo_id},
            {"role_name": equipo_id}
        ]
    })
    
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    if equipo.get("liga_id") != liga_id:
        raise HTTPException(status_code=400, detail="El equipo no está en esta liga")
    
    # Remover de liga
    await equipos_col.update_one(
        {"_id": equipo.get("_id")},
        {"$unset": {"liga_id": "", "liga_nombre": "", "liga_division": ""}}
    )
    
    # Actualizar contador
    equipos_actuales = await equipos_col.count_documents({"liga_id": liga_id})
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": {"total_equipos": max(0, equipos_actuales), "updated_at": datetime.utcnow()}}
    )
    
    return {
        "message": f"Equipo '{equipo.get('nombre')}' removido de la liga",
        "liga_id": liga_id
    }

@router.get("/ligas/{liga_id}/equipos")
async def listar_equipos_liga(liga_id: str):
    """
    Lista todos los equipos asignados a una liga.
    """
    equipos_col = get_collection("equipos")
    
    equipos_cursor = equipos_col.find({"liga_id": liga_id})
    equipos = await equipos_cursor.to_list(length=100)
    
    return [
        {
            "id": str(eq.get("_id")),
            "nombre": eq.get("nombre"),
            "role_name": eq.get("role_name"),
            "logo_url": eq.get("logo_url"),
            "dt_nombre": eq.get("dt_nombre"),
            "presupuesto": eq.get("presupuesto", 0)
        }
        for eq in equipos
    ]

# ============================================================
# LIGA ACTIVA (GLOBAL)
# ============================================================

@router.get("/liga-activa")
async def obtener_liga_activa():
    """
    Obtiene la liga actualmente activa para el sistema.
    """
    config_global = get_collection("server_config")
    ligas_col = get_collection("ligas")
    
    config = await config_global.find_one({"_id": "config_global"})
    liga_activa_id = config.get("liga_activa_id") if config else None
    
    if liga_activa_id:
        liga = await ligas_col.find_one({"_id": ObjectId(liga_activa_id)})
        if liga:
            return {
                "liga_activa": serialize_liga(liga),
                "configurada": True
            }
    
    # Si no hay liga activa configurada, devolver la primera activa
    liga = await ligas_col.find_one({"activa": True})
    if liga:
        return {
            "liga_activa": serialize_liga(liga),
            "configurada": False,
            "message": "No hay liga activa configurada. Usando primera liga disponible."
        }
    
    return {
        "liga_activa": None,
        "configurada": False,
        "message": "No hay ligas disponibles"
    }

@router.post("/liga-activa")
async def establecer_liga_activa(data: CambiarLigaActiva):
    """
    Establece la liga activa para todo el sistema.
    """
    ligas_col = get_collection("ligas")
    config_global = get_collection("server_config")
    
    # Verificar que la liga existe
    liga = await ligas_col.find_one({"_id": ObjectId(data.liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Desactivar todas las demás ligas como "activas en sistema"
    await ligas_col.update_many(
        {"_id": {"$ne": ObjectId(data.liga_id)}},
        {"$set": {"es_liga_activa_sistema": False}}
    )
    
    # Marcar esta como la activa
    await ligas_col.update_one(
        {"_id": ObjectId(data.liga_id)},
        {"$set": {"es_liga_activa_sistema": True, "updated_at": datetime.utcnow()}}
    )
    
    # Guardar en config global
    await config_global.update_one(
        {"_id": "config_global"},
        {"$set": {
            "liga_activa_id": data.liga_id,
            "liga_activa_nombre": liga.get("nombre"),
            "liga_activa_division": liga.get("division"),
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {
        "message": f"Liga activa cambiada a '{liga.get('nombre')}'",
        "liga_activa": serialize_liga(liga)
    }

# ============================================================
# SISTEMA DE COPA INTERDIVISIONAL AUTOMÁTICA
# ============================================================

async def _generar_copa_interdivisional_automatica(liga_d1_id: str, liga_d2_id: str, fecha_inicio: str = None):
    """
    Genera automáticamente la Copa AMAPICKS al llegar a la jornada 11.
    
    FASE 1 - Sembrados (8 equipos directo a octavos):
        - Top 4 de D1
        - Top 4 de D2
    
    FASE 2 - Ronda Preliminar (16 equipos):
        - Puestos 5-12 de D1 (8 equipos)
        - Puestos 5-12 de D2 (8 equipos)
        - Cruces: 5D1 vs 12D2, 6D1 vs 11D2, etc.
    
    FASE 3 - Octavos en adelante:
        - 8 sembrados + 8 ganadores preliminar
    """
    ligas_col = get_collection("ligas")
    partidos_col = get_collection("partidos")
    copa_col = get_collection("copa_inscripciones")
    equipos_col = get_collection("equipos")
    
    # Obtener datos de ambas ligas
    liga_d1 = await ligas_col.find_one({"_id": ObjectId(liga_d1_id)})
    liga_d2 = await ligas_col.find_one({"_id": ObjectId(liga_d2_id)})
    
    if not liga_d1 or not liga_d2:
        return {"error": "No se encontraron ambas ligas (D1 y D2)"}
    
    # Función para calcular tabla de una liga
    async def calcular_tabla_liga(liga_id):
        equipos_cursor = equipos_col.find({"liga_id": liga_id})
        equipos = await equipos_cursor.to_list(length=50)
        
        # Obtener partidos finalizados
        partidos_cursor = partidos_col.find({
            "liga_id": liga_id,
            "estado": {"$in": ["finalizado", "walkover", "jugado"]},
            "jornada": {"$lte": 11}  # Solo hasta jornada 11
        })
        partidos = await partidos_cursor.to_list(length=500)
        
        # Calcular stats
        stats = {}
        for eq in equipos:
            stats[eq["nombre"]] = {
                "equipo": eq["nombre"],
                "pj": 0, "pg": 0, "pe": 0, "pp": 0,
                "gf": 0, "gc": 0, "pts": 0
            }
        
        for p in partidos:
            local = p.get("equipo_local")
            visitante = p.get("equipo_visitante")
            gl = p.get("goles_local", 0)
            gv = p.get("goles_visitante", 0)
            
            if local in stats:
                stats[local]["pj"] += 1
                stats[local]["gf"] += gl
                stats[local]["gc"] += gv
            if visitante in stats:
                stats[visitante]["pj"] += 1
                stats[visitante]["gf"] += gv
                stats[visitante]["gc"] += gl
            
            if gl > gv:
                if local in stats:
                    stats[local]["pg"] += 1
                    stats[local]["pts"] += 3
                if visitante in stats:
                    stats[visitante]["pp"] += 1
            elif gl < gv:
                if visitante in stats:
                    stats[visitante]["pg"] += 1
                    stats[visitante]["pts"] += 3
                if local in stats:
                    stats[local]["pp"] += 1
            else:
                if local in stats:
                    stats[local]["pe"] += 1
                    stats[local]["pts"] += 1
                if visitante in stats:
                    stats[visitante]["pe"] += 1
                    stats[visitante]["pts"] += 1
        
        # Calcular diferencia de goles y ordenar
        tabla = []
        for nombre, s in stats.items():
            s["dg"] = s["gf"] - s["gc"]
            tabla.append(s)
        
        tabla.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
        
        # Asignar posiciones
        for i, t in enumerate(tabla, 1):
            t["pos"] = i
        
        return tabla
    
    # Calcular tablas
    tabla_d1 = await calcular_tabla_liga(liga_d1_id)
    tabla_d2 = await calcular_tabla_liga(liga_d2_id)
    
    # FASE 1: Sembrados (Top 4 de cada división)
    sembrados_d1 = tabla_d1[:4]  # 1°, 2°, 3°, 4°
    sembrados_d2 = tabla_d2[:4]  # 1°, 2°, 3°, 4°
    
    # FASE 2: Preliminar (Puestos 5-12 de cada división)
    preliminar_d1 = tabla_d1[4:12]  # 5° al 12° (8 equipos)
    preliminar_d2 = tabla_d2[4:12]  # 5° al 12° (8 equipos)
    
    # Verificar que tengamos suficientes equipos
    if len(preliminar_d1) < 8 or len(preliminar_d2) < 8:
        return {
            "error": "No hay suficientes equipos para la copa",
            "equipos_d1": len(tabla_d1),
            "equipos_d2": len(tabla_d2),
            "necesarios": "Mínimo 12 equipos en cada división"
        }
    
    # Limpiar inscripciones anteriores
    await copa_col.delete_many({"copa_amapicks": True})
    
    # Inscribir sembrados
    inscripciones = []
    for i, eq in enumerate(sembrados_d1, 1):
        inscripciones.append({
            "equipo_id": eq["equipo"],
            "equipo_nombre": eq["equipo"],
            "liga_origen": "D1",
            "posicion_tabla_origen": i,
            "es_sembrado": True,
            "ronda_actual": "octavos",
            "copa_amapicks": True,
            "created_at": datetime.utcnow()
        })
    
    for i, eq in enumerate(sembrados_d2, 1):
        inscripciones.append({
            "equipo_id": eq["equipo"],
            "equipo_nombre": eq["equipo"],
            "liga_origen": "D2",
            "posicion_tabla_origen": i,
            "es_sembrado": True,
            "ronda_actual": "octavos",
            "copa_amapicks": True,
            "created_at": datetime.utcnow()
        })
    
    # Inscribir preliminar
    for eq in preliminar_d1:
        inscripciones.append({
            "equipo_id": eq["equipo"],
            "equipo_nombre": eq["equipo"],
            "liga_origen": "D1",
            "posicion_tabla_origen": eq["pos"],
            "es_sembrado": False,
            "ronda_actual": "preliminar",
            "copa_amapicks": True,
            "created_at": datetime.utcnow()
        })
    
    for eq in preliminar_d2:
        inscripciones.append({
            "equipo_id": eq["equipo"],
            "equipo_nombre": eq["equipo"],
            "liga_origen": "D2",
            "posicion_tabla_origen": eq["pos"],
            "es_sembrado": False,
            "ronda_actual": "preliminar",
            "copa_amapicks": True,
            "created_at": datetime.utcnow()
        })
    
    # Guardar inscripciones
    if inscripciones:
        await copa_col.insert_many(inscripciones)
    
    # Generar partidos de RONDA PRELIMINAR
    # Cruces: 5D1 vs 12D2, 6D1 vs 11D2, 7D1 vs 10D2, 8D1 vs 9D2
    #         9D1 vs 8D2, 10D1 vs 7D2, 11D1 vs 6D2, 12D1 vs 5D2
    
    fecha_base = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else datetime.utcnow()
    
    partidos_preliminar = []
    cruces_preliminar = [
        (0, 7),   # 5° D1 vs 12° D2 (índices 0 y 7 en listas preliminar)
        (1, 6),   # 6° D1 vs 11° D2
        (2, 5),   # 7° D1 vs 10° D2
        (3, 4),   # 8° D1 vs 9° D2
        (4, 3),   # 9° D1 vs 8° D2
        (5, 2),   # 10° D1 vs 7° D2
        (6, 1),   # 11° D1 vs 6° D2
        (7, 0),   # 12° D1 vs 5° D2
    ]
    
    for idx_d1, idx_d2 in cruces_preliminar:
        if idx_d1 < len(preliminar_d1) and idx_d2 < len(preliminar_d2):
            eq_d1 = preliminar_d1[idx_d1]
            eq_d2 = preliminar_d2[idx_d2]
            
            partido = {
                "guild_id": "0",
                "copa": True,
                "copa_amapicks": True,
                "ronda": "Preliminar",
                "fase": "Copa AMAPICKS - Preliminar",
                "equipo_local": eq_d1["equipo"],
                "liga_local": "D1",
                "pos_local": eq_d1["pos"],
                "equipo_visitante": eq_d2["equipo"],
                "liga_visitante": "D2",
                "pos_visitante": eq_d2["pos"],
                "fecha_hora": (fecha_base).isoformat(),
                "estado": "pendiente",
                "auto_generado": True,
                "creado_en": datetime.utcnow()
            }
            partidos_preliminar.append(partido)
    
    # Insertar partidos preliminar
    if partidos_preliminar:
        await partidos_col.insert_many(partidos_preliminar)
    
    # Marcar ligas como en parón de copa
    await ligas_col.update_one(
        {"_id": ObjectId(liga_d1_id)},
        {"$set": {
            "estado": "paron_copa",
            "copa_generada": True,
            "updated_at": datetime.utcnow()
        }}
    )
    await ligas_col.update_one(
        {"_id": ObjectId(liga_d2_id)},
        {"$set": {
            "estado": "paron_copa",
            "copa_generada": True,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Copa AMAPICKS generada automáticamente",
        "sembrados": {
            "total": 8,
            "d1": [eq["equipo"] for eq in sembrados_d1],
            "d2": [eq["equipo"] for eq in sembrados_d2]
        },
        "preliminar": {
            "total": 16,
            "partidos": len(partidos_preliminar),
            "d1": [eq["equipo"] for eq in preliminar_d1],
            "d2": [eq["equipo"] for eq in preliminar_d2]
        },
        "partidos_preliminar_creados": len(partidos_preliminar),
        "total_inscritos": len(inscripciones)
    }

# ============================================================
# FIXTURE GENERATION PARA LIGAS
# ============================================================

def _generar_fixture_round_robin_liga(equipos: List[str], liga_id: str):
    """
    Genera fixture round-robin (ida y vuelta) para una liga específica.
    Retorna lista de jornadas con partidos.
    """
    n = len(equipos)
    if n % 2 == 1:
        equipos = equipos + ["BYE"]
        n = len(equipos)
    
    fixture_ida = []
    equipos_rotacion = equipos.copy()
    
    # Jornadas de IDA
    for jornada_num in range(n - 1):
        partidos_jornada = []
        for i in range(n // 2):
            local = equipos_rotacion[i]
            visitante = equipos_rotacion[n - 1 - i]
            
            if local != "BYE" and visitante != "BYE":
                partidos_jornada.append({
                    "equipo_local": local,
                    "equipo_visitante": visitante,
                    "liga_id": liga_id,
                    "jornada": jornada_num + 1,
                    "fase": "ida"
                })
        
        # Rotación circular
        equipos_rotacion = [equipos_rotacion[0]] + equipos_rotacion[-1:] + equipos_rotacion[1:-1]
        fixture_ida.append({
            "jornada": jornada_num + 1,
            "fase": "ida",
            "partidos": partidos_jornada
        })
    
    # Jornadas de VUELTA (invertir localías)
    fixture_vuelta = []
    for jornada_data in fixture_ida:
        partidos_vuelta = []
        for p in jornada_data["partidos"]:
            partidos_vuelta.append({
                "equipo_local": p["equipo_visitante"],
                "equipo_visitante": p["equipo_local"],
                "liga_id": liga_id,
                "jornada": jornada_data["jornada"] + len(fixture_ida),
                "fase": "vuelta"
            })
        
        fixture_vuelta.append({
            "jornada": jornada_data["jornada"] + len(fixture_ida),
            "fase": "vuelta",
            "partidos": partidos_vuelta
        })
    
    return fixture_ida + fixture_vuelta

@router.post("/ligas/{liga_id}/generar-fixture")
async def generar_fixture_liga(
    liga_id: str, 
    fecha_inicio: str,
    dias_entre_jornadas: int = 3,
    hora_default: str = "20:00"
):
    """
    Genera el fixture completo (ida y vuelta) para una liga.
    """
    ligas_col = get_collection("ligas")
    equipos_col = get_collection("equipos")
    partidos_col = get_collection("partidos")
    
    # Verificar liga
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Obtener equipos de la liga
    equipos_cursor = equipos_col.find({"liga_id": liga_id})
    equipos_docs = await equipos_cursor.to_list(length=50)
    
    if len(equipos_docs) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Se necesitan al menos 2 equipos en la liga para generar fixture"
        )
    
    equipos_nombres = [eq["nombre"] for eq in equipos_docs]
    
    # Generar fixture
    fixture = _generar_fixture_round_robin_liga(equipos_nombres, liga_id)
    
    # Parse fecha inicio
    try:
        from datetime import datetime as dt
        fecha_base = dt.strptime(fecha_inicio, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Crear partidos en BD
    partidos_creados = 0
    for jornada_data in fixture:
        jornada_num = jornada_data["jornada"]
        fecha_jornada = fecha_base + __import__('datetime').timedelta(days=(jornada_num - 1) * dias_entre_jornadas)
        
        for partido in jornada_data["partidos"]:
            fecha_hora = datetime.combine(
                fecha_jornada.date(), 
                datetime.strptime(hora_default, "%H:%M").time()
            )
            
            await partidos_col.insert_one({
                "guild_id": "0",
                "liga_id": liga_id,
                "liga_nombre": liga.get("nombre"),
                "equipo_local": partido["equipo_local"],
                "equipo_visitante": partido["equipo_visitante"],
                "fecha_hora": fecha_hora.isoformat(),
                "jornada": jornada_num,
                "fase": "Liga Regular",
                "sub_fase": partido.get("fase", "ida"),
                "estado": "pendiente",
                "auto_generado": True,
                "creado_en": datetime.utcnow()
            })
            partidos_creados += 1
    
    # Actualizar estado de la liga
    total_jornadas = len(fixture)
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": {
            "estado": "en_curso",
            "jornada_actual": 1,
            "total_jornadas": total_jornadas,
            "jornadas_ida": total_jornadas // 2,
            "jornadas_vuelta": total_jornadas // 2,
            "updated_at": datetime.utcnow(),
            "fixture_generado_en": datetime.utcnow(),
            "fecha_inicio": fecha_inicio,
            "partidos_generados": partidos_creados
        }}
    )
    
    return {
        "message": f"Fixture generado exitosamente para '{liga.get('nombre')}'",
        "liga_id": liga_id,
        "equipos": len(equipos_nombres),
        "jornadas_total": total_jornadas,
        "jornadas_ida": total_jornadas // 2,
        "jornadas_vuelta": total_jornadas // 2,
        "partidos_creados": partidos_creados,
        "fixture_preview": fixture[:2]  # Primeras 2 jornadas como preview
    }

@router.post("/ligas/{liga_id}/avanzar-jornada")
async def avanzar_jornada_liga(liga_id: str):
    """
    Avanza a la siguiente jornada de la liga.
    Verifica si se debe activar el parón de copa.
    Si es jornada 11, genera automáticamente la Copa AMAPICKS interdivisional.
    """
    ligas_col = get_collection("ligas")
    partidos_col = get_collection("partidos")
    config_liga_col = get_collection("config_liga")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    jornada_actual = liga.get("jornada_actual", 1)
    jornada_paron = liga.get("jornada_paron_copa", 11)
    
    # Verificar si todos los partidos de la jornada actual están finalizados
    partidos_pendientes = await partidos_col.count_documents({
        "liga_id": liga_id,
        "jornada": jornada_actual,
        "estado": {"$nin": ["finalizado", "walkover"]}
    })
    
    if partidos_pendientes > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede avanzar. Hay {partidos_pendientes} partidos pendientes en la jornada {jornada_actual}"
        )
    
    nueva_jornada = jornada_actual + 1
    
    # Verificar si es el parón de copa (jornada 11)
    es_paron_copa = nueva_jornada > jornada_paron and jornada_actual <= jornada_paron
    
    update_data = {
        "jornada_actual": nueva_jornada,
        "updated_at": datetime.utcnow()
    }
    
    resultado_copa = None
    
    if es_paron_copa:
        update_data["estado"] = "paron_copa"
        
        # Abrir mercado e inscripción a copa
        await config_liga_col.update_one(
            {"liga_id": liga_id},
            {"$set": {
                "mercado_abierto": True,
                "inscripcion_copa_abierta": True,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        # Generar Copa AMAPICKS automáticamente
        # Buscar ligas D1 y D2
        liga_d1 = await ligas_col.find_one({"division": "D1", "activa": True})
        liga_d2 = await ligas_col.find_one({"division": "D2", "activa": True})
        
        if liga_d1 and liga_d2:
            try:
                resultado_copa = await _generar_copa_interdivisional_automatica(
                    str(liga_d1["_id"]),
                    str(liga_d2["_id"])
                )
            except Exception as e:
                print(f"Error generando copa automática: {e}")
                resultado_copa = {"error": str(e)}
    
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": update_data}
    )
    
    respuesta = {
        "message": f"Jornada avanzada a {nueva_jornada}",
        "jornada_anterior": jornada_actual,
        "jornada_actual": nueva_jornada,
        "paron_copa_activado": es_paron_copa,
        "mercado_abierto": es_paron_copa,
        "inscripcion_copa_abierta": es_paron_copa
    }
    
    if resultado_copa:
        respuesta["copa_generada"] = resultado_copa
    
    return respuesta

@router.get("/ligas/{liga_id}/estado")
async def obtener_estado_liga_detallado(liga_id: str):
    """
    Obtiene el estado detallado de una liga incluyendo progreso.
    """
    ligas_col = get_collection("ligas")
    partidos_col = get_collection("partidos")
    equipos_col = get_collection("equipos")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Conteos
    total_equipos = await equipos_col.count_documents({"liga_id": liga_id})
    total_partidos = await partidos_col.count_documents({"liga_id": liga_id})
    partidos_jugados = await partidos_col.count_documents({
        "liga_id": liga_id,
        "estado": {"$in": ["finalizado", "walkover"]}
    })
    
    # Partidos por jornada actual
    partidos_jornada_actual = await partidos_col.count_documents({
        "liga_id": liga_id,
        "jornada": liga.get("jornada_actual", 1)
    })
    
    partidos_jugados_jornada_actual = await partidos_col.count_documents({
        "liga_id": liga_id,
        "jornada": liga.get("jornada_actual", 1),
        "estado": {"$in": ["finalizado", "walkover"]}
    })
    
    total_jornadas = liga.get("jornadas_ida", 0) + liga.get("jornadas_vuelta", 0)
    progreso = round((liga.get("jornada_actual", 1) / total_jornadas) * 100, 1) if total_jornadas > 0 else 0
    
    return {
        "liga": serialize_liga(liga),
        "equipos": {
            "total": total_equipos,
            "max_permitido": liga.get("max_equipos", 12),
            "cupos_disponibles": max(0, liga.get("max_equipos", 12) - total_equipos)
        },
        "partidos": {
            "total": total_partidos,
            "jugados": partidos_jugados,
            "pendientes": total_partidos - partidos_jugados
        },
        "jornada": {
            "actual": liga.get("jornada_actual", 1),
            "total": total_jornadas,
            "progreso_porcentaje": progreso,
            "partidos_en_jornada": partidos_jornada_actual,
            "partidos_jugados_jornada": partidos_jugados_jornada_actual,
            "partidos_pendientes_jornada": partidos_jornada_actual - partidos_jugados_jornada_actual
        },
        "paron_copa": {
            "jornada_paron": liga.get("jornada_paron_copa", 11),
            "activo": liga.get("estado") == "paron_copa",
            "proximo": liga.get("jornada_actual", 1) == liga.get("jornada_paron_copa", 11)
        }
    }

# ============================================================
# SISTEMA DE COPA (24 EQUIPOS)
# ============================================================

class InscribirEquipoCopa(BaseModel):
    equipo_id: str
    liga_origen_id: Optional[str] = None  # Para equipos invitados de otras ligas

class GenerarBracketCopa(BaseModel):
    fecha_inicio: str
    dias_entre_rondas: int = 3
    hora_default: str = "20:00"

@router.post("/ligas/{liga_id}/copa/inscribir")
async def inscribir_equipo_copa(liga_id: str, data: InscribirEquipoCopa):
    """
    Inscribe un equipo a la copa de la liga.
    """
    ligas_col = get_collection("ligas")
    equipos_col = get_collection("equipos")
    copa_col = get_collection("copa_inscripciones")
    
    # Verificar liga
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    if not liga.get("copa_habilitada", True):
        raise HTTPException(status_code=400, detail="La copa no está habilitada para esta liga")
    
    # Buscar equipo
    equipo = await equipos_col.find_one({
        "$or": [
            {"_id": ObjectId(data.equipo_id) if len(data.equipo_id) == 24 else {"$ne": None}},
            {"nombre": data.equipo_id}
        ]
    })
    
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    # Verificar si ya está inscrito
    existente = await copa_col.find_one({
        "liga_id": liga_id,
        "equipo_id": str(equipo.get("_id"))
    })
    
    if existente:
        raise HTTPException(status_code=400, detail="El equipo ya está inscrito en la copa")
    
    # Contar inscripciones actuales
    total_inscritos = await copa_col.count_documents({"liga_id": liga_id})
    max_equipos = liga.get("equipos_copa_total", 24)
    
    if total_inscritos >= max_equipos:
        raise HTTPException(status_code=400, detail=f"La copa ya tiene {max_equipos} equipos inscritos")
    
    # Inscribir equipo
    inscripcion = {
        "liga_id": liga_id,
        "equipo_id": str(equipo.get("_id")),
        "equipo_nombre": equipo.get("nombre"),
        "liga_origen_id": data.liga_origen_id or liga_id,
        "posicion_tabla_origen": None,  # Se actualiza al generar bracket
        "es_sembrado": False,
        "ronda_actual": None,
        "orden_sorteo": total_inscritos + 1,
        "created_at": datetime.utcnow()
    }
    
    await copa_col.insert_one(inscripcion)
    
    return {
        "message": f"Equipo '{equipo.get('nombre')}' inscrito en la copa",
        "equipo": equipo.get("nombre"),
        "total_inscritos": total_inscritos + 1,
        "cupo_disponible": max_equipos - (total_inscritos + 1)
    }

@router.get("/ligas/{liga_id}/copa/inscripciones")
async def listar_inscripciones_copa(liga_id: str):
    """
    Lista todos los equipos inscritos en la copa.
    """
    copa_col = get_collection("copa_inscripciones")
    
    inscripciones_cursor = copa_col.find({"liga_id": liga_id}).sort("orden_sorteo", 1)
    inscripciones = await inscripciones_cursor.to_list(length=50)
    
    return [
        {
            "id": str(insc.get("_id")),
            "equipo_id": insc.get("equipo_id"),
            "equipo_nombre": insc.get("equipo_nombre"),
            "es_sembrado": insc.get("es_sembrado", False),
            "posicion_tabla_origen": insc.get("posicion_tabla_origen"),
            "ronda_actual": insc.get("ronda_actual"),
            "orden_sorteo": insc.get("orden_sorteo")
        }
        for insc in inscripciones
    ]

@router.post("/ligas/{liga_id}/copa/sembrar")
async def sembrar_equipos_copa(liga_id: str):
    """
    Marca los top N equipos como sembrados para ir directo a octavos.
    Por defecto: top 8 de la tabla.
    """
    ligas_col = get_collection("ligas")
    copa_col = get_collection("copa_inscripciones")
    tabla_col = get_collection("tabla_posiciones")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    equipos_sembrados = liga.get("equipos_sembrados", 8)
    
    # Obtener tabla de posiciones
    tabla_cursor = tabla_col.find({"liga_id": liga_id}).sort([
        ("pts", -1),
        ("dif", -1),
        ("gf", -1)
    ]).limit(equipos_sembrados)
    
    tabla = await tabla_cursor.to_list(length=equipos_sembrados)
    
    sembrados = []
    for i, equipo_tabla in enumerate(tabla, 1):
        equipo_nombre = equipo_tabla.get("equipo")
        
        # Actualizar inscripción
        result = await copa_col.update_one(
            {"liga_id": liga_id, "equipo_nombre": equipo_nombre},
            {"$set": {
                "es_sembrado": True,
                "posicion_tabla_origen": i,
                "ronda_actual": "octavos",
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.matched_count > 0:
            sembrados.append({
                "posicion": i,
                "equipo": equipo_nombre
            })
    
    return {
        "message": f"{len(sembrados)} equipos marcados como sembrados",
        "sembrados": sembrados,
        "total_sembrados": equipos_sembrados
    }

@router.post("/ligas/{liga_id}/copa/generar-bracket")
async def generar_bracket_copa(liga_id: str, data: GenerarBracketCopa):
    """
    Genera el bracket completo de la copa incluyendo:
    - Ronda Preliminar (16 equipos no sembrados)
    - Octavos de Final (8 sembrados + 8 ganadores preliminar)
    - Cuartos, Semifinal, Final
    """
    ligas_col = get_collection("ligas")
    copa_col = get_collection("copa_inscripciones")
    partidos_col = get_collection("partidos")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Obtener equipos inscritos
    inscripciones_cursor = copa_col.find({"liga_id": liga_id})
    inscripciones = await inscripciones_cursor.to_list(length=50)
    
    if len(inscripciones) < 16:
        raise HTTPException(
            status_code=400, 
            detail=f"Se necesitan al menos 16 equipos inscritos. Actualmente: {len(inscripciones)}"
        )
    
    # Separar sembrados y no sembrados
    sembrados = [i for i in inscripciones if i.get("es_sembrado", False)]
    no_sembrados = [i for i in inscripciones if not i.get("es_sembrado", False)]
    
    # Parse fecha inicio
    try:
        from datetime import datetime as dt, timedelta
        fecha_base = dt.strptime(data.fecha_inicio, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    partidos_creados = []
    
    # Generar Ronda Preliminar si está habilitada
    if liga.get("ronda_preliminar", True) and len(no_sembrados) >= 16:
        # Emparejar no sembrados aleatoriamente
        import random
        random.shuffle(no_sembrados)
        
        for i in range(0, min(16, len(no_sembrados)), 2):
            if i + 1 < len(no_sembrados):
                fecha_partido = fecha_base + timedelta(days=0)  # Mismo día
                
                partido = {
                    "guild_id": "0",
                    "liga_id": liga_id,
                    "copa": True,
                    "ronda": "Preliminar",
                    "equipo_local": no_sembrados[i]["equipo_nombre"],
                    "equipo_visitante": no_sembrados[i+1]["equipo_nombre"],
                    "fecha_hora": datetime.combine(
                        fecha_partido.date(),
                        datetime.strptime(data.hora_default, "%H:%M").time()
                    ).isoformat(),
                    "estado": "pendiente",
                    "fase": "Copa - Preliminar",
                    "auto_generado": True,
                    "creado_en": datetime.utcnow()
                }
                
                await partidos_col.insert_one(partido)
                partidos_creados.append(partido)
    
    # Actualizar estado de la liga
    await ligas_col.update_one(
        {"_id": ObjectId(liga_id)},
        {"$set": {
            "copa_bracket_generado": True,
            "copa_fecha_inicio": data.fecha_inicio,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Bracket de copa generado exitosamente",
        "partidos_preliminar_creados": len(partidos_creados),
        "equipos_sembrados": len(sembrados),
        "equipos_preliminar": len(no_sembrados),
        "fecha_inicio": data.fecha_inicio
    }

# ============================================================
# SISTEMA DE FACTOR RIVAL (BONO POR DIFICULTAD)
# ============================================================

@router.get("/ligas/{liga_id}/factor-rival/calcular")
async def calcular_factor_rival(liga_id: str, equipo_ganador: str, equipo_perdedor: str):
    """
    Calcula el bono de Factor Rival para un partido.
    Ganar al 1° siendo el 12° otorga bono máximo.
    Formula: bono = (posicion_rival - posicion_ganador) * factor_base
    """
    tabla_col = get_collection("tabla_posiciones")
    ligas_col = get_collection("ligas")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    if not liga.get("factor_rival_habilitado", True):
        return {
            "factor_rival_activo": False,
            "message": "Factor Rival no está habilitado en esta liga"
        }
    
    # Obtener posiciones actuales
    tabla_cursor = tabla_col.find({"liga_id": liga_id}).sort([
        ("pts", -1),
        ("dif", -1),
        ("gf", -1)
    ])
    
    tabla = await tabla_cursor.to_list(length=50)
    
    # Crear mapa de posiciones
    posiciones = {}
    for i, equipo_tabla in enumerate(tabla, 1):
        posiciones[equipo_tabla.get("equipo")] = i
    
    pos_ganador = posiciones.get(equipo_ganador)
    pos_perdedor = posiciones.get(equipo_perdedor)
    
    if not pos_ganador or not pos_perdedor:
        return {
            "factor_rival_activo": True,
            "error": "No se encontraron posiciones para uno o ambos equipos",
            "bono_valor_mercado": 0
        }
    
    # Calcular diferencia de posiciones
    diferencia = pos_perdedor - pos_ganador
    
    # Factor base: cada posición de diferencia = 5% de bono
    # Ganar al 1° siendo el 12° = (12-1) * 5% = 55% bono máximo (con tope en 50%)
    factor_base = 0.05  # 5% por posición
    bono_porcentaje = min(diferencia * factor_base, 0.50)  # Tope 50%
    
    # Solo aplicar si el ganador está por debajo del perdedor en la tabla
    if pos_ganador >= pos_perdedor:
        bono_porcentaje = 0
    
    return {
        "factor_rival_activo": True,
        "equipo_ganador": equipo_ganador,
        "equipo_perdedor": equipo_perdedor,
        "posicion_ganador": pos_ganador,
        "posicion_perdedor": pos_perdedor,
        "diferencia_posiciones": diferencia if pos_ganador < pos_perdedor else 0,
        "bono_porcentaje": round(bono_porcentaje * 100, 1),
        "formula": f"min(({pos_perdedor} - {pos_ganador}) × 5%, 50%)" if pos_ganador < pos_perdedor else "Sin bono (ganador está arriba en la tabla)"
    }

@router.get("/ligas/{liga_id}/factor-rival/tabla")
async def obtener_tabla_con_factor_rival(liga_id: str):
    """
    Obtiene la tabla de posiciones con valores de mercado ajustados
    por el Factor Rival acumulado.
    """
    tabla_col = get_collection("tabla_posiciones")
    ligas_col = get_collection("ligas")
    
    liga = await ligas_col.find_one({"_id": ObjectId(liga_id)})
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")
    
    # Obtener tabla ordenada
    tabla_cursor = tabla_col.find({"liga_id": liga_id}).sort([
        ("pts", -1),
        ("dif", -1),
        ("gf", -1)
    ])
    
    tabla = await tabla_cursor.to_list(length=50)
    
    # Enriquecer con factor rival
    tabla_enriquecida = []
    for i, equipo in enumerate(tabla, 1):
        equipo_data = {
            "posicion": i,
            "equipo": equipo.get("equipo"),
            "pj": equipo.get("pj", 0),
            "pg": equipo.get("pg", 0),
            "pe": equipo.get("pe", 0),
            "pp": equipo.get("pp", 0),
            "gf": equipo.get("gf", 0),
            "gc": equipo.get("gc", 0),
            "dg": equipo.get("dif", 0),
            "pts": equipo.get("pts", 0),
            "factor_rival_activo": liga.get("factor_rival_habilitado", True)
        }
        tabla_enriquecida.append(equipo_data)
    
    return {
        "liga": liga.get("nombre"),
        "division": liga.get("division"),
        "factor_rival_habilitado": liga.get("factor_rival_habilitado", True),
        "tabla": tabla_enriquecida,
        "nota": "El Factor Rival otorga bonificación de valor de mercado al ganar a equipos por encima en la tabla"
    }

