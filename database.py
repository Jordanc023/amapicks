"""
database.py - Conexión centralizada a MongoDB (Motor Async)
Incluye funciones de auditoría, configuración por servidor y temporadas.
Todas las funciones que acceden a MongoDB son async para no bloquear el event loop.
"""
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from config import MONGO_URI, DB_NAME, DEFAULT_SERVER_CONFIG, DEFAULT_PUNTUACION
from logger import get_module_logger

logger = get_module_logger("database")

# ============================================
# SINGLETON DE CONEXIÓN (Motor Async)
# ============================================

_client = None
_db = None


def get_client():
    """Retorna la instancia única del cliente Motor (async)."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI, maxPoolSize=20, retryWrites=True)
    return _client


def get_db():
    """Retorna la instancia única de la base de datos."""
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def get_collection(name: str):
    """Retorna una colección específica de la base de datos."""
    return get_db()[name]


# ============================================
# INICIALIZACIÓN Y ÍNDICES
# ============================================

async def init_db():
    """Inicializa la base de datos con configuración por defecto e índices."""
    config = get_collection('configuracion')

    existente = await config.find_one({'clave': 'mercado_abierto'})
    if existente is None:
        await config.insert_one({'clave': 'mercado_abierto', 'valor': 'false'})

    # Crear índices para mejor rendimiento
    audit_col = get_collection('audit_logs')
    await audit_col.create_index([('guild_id', 1), ('timestamp', -1)])
    await audit_col.create_index([('action_type', 1)])
    await audit_col.create_index([('target_id', 1)])

    jugadores_col = get_collection('jugadores')
    await jugadores_col.create_index([('discord_id', 1)], unique=True)
    await jugadores_col.create_index([('equipo', 1)])

    agentes_col = get_collection('agentes_libres')
    await agentes_col.create_index([('discord_id', 1)], unique=True)

    equipos_col = get_collection('equipos')
    await equipos_col.create_index([('nombre', 1)], unique=True)

    partidos_col = get_collection('partidos')
    await partidos_col.create_index([('guild_id', 1), ('estado', 1)])
    await partidos_col.create_index([('fecha_hora', 1)])

    tabla_col = get_collection('tabla_posiciones')
    await tabla_col.create_index([('guild_id', 1), ('equipo', 1)], unique=True)

    ofertas_col = get_collection('ofertas_pendientes')
    await ofertas_col.create_index([('dt_id', 1), ('jugador_id', 1)], unique=True)
    await ofertas_col.create_index([('expira_en', 1)], expireAfterSeconds=0)

    config_col = get_collection('server_config')
    await config_col.create_index([('guild_id', 1)], unique=True)

    logger.info("📂 MongoDB conectado (Motor Async) + Índices creados.")


# ============================================
# SISTEMA DE AUDITORÍA
# ============================================

async def log_action(guild_id: str, action_type: str, actor_id: str, actor_name: str,
                     details: dict = None, target_id: str = None, target_name: str = None):
    """
    Registra una acción en el log de auditoría (async).
    """
    audit_col = get_collection('audit_logs')

    log_entry = {
        'guild_id': str(guild_id),
        'timestamp': datetime.now(),
        'action_type': action_type,
        'actor_id': str(actor_id),
        'actor_name': actor_name,
        'target_id': str(target_id) if target_id else None,
        'target_name': target_name,
        'details': details or {}
    }

    await audit_col.insert_one(log_entry)
    logger.debug(f"📝 Audit: {action_type} por {actor_name}")


async def get_audit_logs(guild_id: str, limit: int = 20, action_type: str = None):
    """Obtiene los logs de auditoría de un servidor (async)."""
    audit_col = get_collection('audit_logs')

    query = {'guild_id': str(guild_id)}
    if action_type:
        query['action_type'] = action_type

    cursor = audit_col.find(query).sort('timestamp', DESCENDING).limit(limit)
    return await cursor.to_list(length=limit)


async def get_audit_stats(guild_id: str):
    """Obtiene estadísticas de auditoría para un servidor (async)."""
    audit_col = get_collection('audit_logs')

    pipeline = [
        {'$match': {'guild_id': str(guild_id)}},
        {'$group': {'_id': '$action_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]

    cursor = audit_col.aggregate(pipeline)
    return await cursor.to_list(length=50)


# ============================================
# CONFIGURACIÓN POR SERVIDOR
# ============================================

async def get_server_config(guild_id: str) -> dict:
    """Obtiene la configuración de un servidor (async). Crea default si no existe."""
    config_col = get_collection('server_config')

    config = await config_col.find_one({'guild_id': str(guild_id)})

    if not config:
        config = DEFAULT_SERVER_CONFIG.copy()
        config['guild_id'] = str(guild_id)
        config['created_at'] = datetime.now()
        await config_col.insert_one(config)
        config = await config_col.find_one({'guild_id': str(guild_id)})

    return config


async def update_server_config(guild_id: str, key: str, value) -> bool:
    """Actualiza un valor de configuración del servidor (async)."""
    config_col = get_collection('server_config')

    await get_server_config(guild_id)

    result = await config_col.update_one(
        {'guild_id': str(guild_id)},
        {'$set': {key: value, 'updated_at': datetime.now()}}
    )
    return result.modified_count > 0


async def get_config_value(guild_id: str, key: str, default=None):
    """Obtiene un valor específico de configuración (async)."""
    config = await get_server_config(guild_id)
    return config.get(key, default)


# ============================================
# SISTEMA DE TEMPORADAS
# ============================================

async def get_current_season(guild_id: str) -> dict:
    """Obtiene la temporada actual de un servidor (async)."""
    temporadas_col = get_collection('temporadas')

    temporada = await temporadas_col.find_one(
        {'guild_id': str(guild_id), 'activa': True}
    )

    if not temporada:
        temporada = {
            'guild_id': str(guild_id),
            'numero': 1,
            'nombre': 'Temporada 1',
            'fecha_inicio': datetime.now(),
            'fecha_fin': None,
            'activa': True,
            'stats': {}
        }
        await temporadas_col.insert_one(temporada)
        temporada = await temporadas_col.find_one({'guild_id': str(guild_id), 'activa': True})

    return temporada


async def create_new_season(guild_id: str, nombre: str = None) -> dict:
    """Crea una nueva temporada y archiva la anterior (async)."""
    temporadas_col = get_collection('temporadas')
    jugadores_col = get_collection('jugadores')
    equipos_col = get_collection('equipos')

    temporada_actual = await get_current_season(guild_id)
    numero_actual = temporada_actual.get('numero', 0)

    # Snapshot
    snapshot_jugadores = await jugadores_col.find({}, {'_id': 0}).to_list(length=500)
    snapshot_equipos = await equipos_col.find({}, {'_id': 0}).to_list(length=100)

    # Cerrar temporada actual
    await temporadas_col.update_one(
        {'guild_id': str(guild_id), 'activa': True},
        {'$set': {
            'activa': False,
            'fecha_fin': datetime.now(),
            'snapshot_jugadores': snapshot_jugadores,
            'snapshot_equipos': snapshot_equipos
        }}
    )

    # Crear nueva temporada
    nuevo_numero = numero_actual + 1
    nueva_temporada = {
        'guild_id': str(guild_id),
        'numero': nuevo_numero,
        'nombre': nombre or f'Temporada {nuevo_numero}',
        'fecha_inicio': datetime.now(),
        'fecha_fin': None,
        'activa': True,
        'stats': {}
    }
    await temporadas_col.insert_one(nueva_temporada)

    await update_server_config(guild_id, 'temporada_actual', nuevo_numero)
    return nueva_temporada


async def get_all_seasons(guild_id: str) -> list:
    """Obtiene todas las temporadas de un servidor (async)."""
    temporadas_col = get_collection('temporadas')
    cursor = temporadas_col.find({'guild_id': str(guild_id)}).sort('numero', DESCENDING)
    return await cursor.to_list(length=50)


async def get_season_by_number(guild_id: str, numero: int) -> dict:
    """Obtiene una temporada específica por su número (async)."""
    temporadas_col = get_collection('temporadas')
    return await temporadas_col.find_one({
        'guild_id': str(guild_id),
        'numero': numero
    })


# ============================================
# FUNCIONES DE MERCADO
# ============================================

async def mercado_esta_abierto():
    """Verifica si el mercado de fichajes está abierto (async)."""
    config = get_collection('configuracion')
    resultado = await config.find_one({'clave': 'mercado_abierto'})

    if not resultado:
        return False

    valor = resultado.get('valor', 'false')

    if valor == 'true':
        return True
    elif valor == 'false':
        return False
    else:
        return valor


async def mercado_abierto_para(equipo: str) -> bool:
    """Verifica si el mercado está abierto para un equipo específico (async)."""
    estado = await mercado_esta_abierto()

    if estado is True:
        return True
    elif estado == equipo:
        return True
    return False


async def canal_esta_bloqueado(canal_id: int) -> bool:
    """Verifica si un canal está bloqueado para el bot (async)."""
    canales = get_collection('canales_bloqueados')
    resultado = await canales.find_one({'canal_id': str(canal_id)})
    return resultado is not None


async def abrir_mercado(valor: str = 'true'):
    """Abre el mercado de fichajes (async)."""
    config = get_collection('configuracion')
    await config.update_one(
        {'clave': 'mercado_abierto'},
        {'$set': {'valor': valor}},
        upsert=True
    )


async def cerrar_mercado():
    """Cierra el mercado de fichajes (async)."""
    config = get_collection('configuracion')
    await config.update_one(
        {'clave': 'mercado_abierto'},
        {'$set': {'valor': 'false'}},
        upsert=True
    )


async def contar_jugadores_equipo(equipo: str) -> int:
    """Cuenta los jugadores de un equipo (async). Excluye al DT principal, pero incluye SubDT y Capitan."""
    jugadores = get_collection('jugadores')
    # Solo excluir es_dt=True (DT principal), incluir SubDT y Capitan
    return await jugadores.count_documents({'equipo': equipo, 'es_dt': {'$ne': True}})


# ============================================
# OFERTAS PENDIENTES (Persistentes en MongoDB)
# ============================================

async def crear_oferta_pendiente(dt_id: str, jugador_id: str, equipo: str,
                                  expira_minutos: int = 10) -> bool:
    """Crea una oferta pendiente en MongoDB con TTL automático."""
    ofertas_col = get_collection('ofertas_pendientes')
    try:
        await ofertas_col.insert_one({
            'dt_id': str(dt_id),
            'jugador_id': str(jugador_id),
            'equipo': equipo,
            'timestamp': datetime.now(),
            'expira_en': datetime.now() + timedelta(minutes=expira_minutos)
        })
        return True
    except Exception:
        return False


async def eliminar_oferta_pendiente(dt_id: str, jugador_id: str) -> bool:
    """Elimina una oferta pendiente."""
    ofertas_col = get_collection('ofertas_pendientes')
    result = await ofertas_col.delete_one({
        'dt_id': str(dt_id),
        'jugador_id': str(jugador_id)
    })
    return result.deleted_count > 0


async def tiene_oferta_pendiente(dt_id: str, jugador_id: str) -> bool:
    """Verifica si existe una oferta pendiente de un DT a un jugador."""
    ofertas_col = get_collection('ofertas_pendientes')
    resultado = await ofertas_col.find_one({
        'dt_id': str(dt_id),
        'jugador_id': str(jugador_id)
    })
    return resultado is not None


async def tiene_oferta_de_otro_dt(jugador_id: str, dt_id_propio: str) -> str:
    """Verifica si otro DT ya tiene oferta pendiente con este jugador."""
    ofertas_col = get_collection('ofertas_pendientes')
    resultado = await ofertas_col.find_one({
        'jugador_id': str(jugador_id),
        'dt_id': {'$ne': str(dt_id_propio)}
    })
    if resultado:
        return resultado.get('equipo', 'otro equipo')
    return None


async def limpiar_ofertas_expiradas():
    """Limpia ofertas expiradas manualmente (backup del TTL index)."""
    ofertas_col = get_collection('ofertas_pendientes')
    result = await ofertas_col.delete_many({
        'expira_en': {'$lt': datetime.now()}
    })
    return result.deleted_count


# ============================================
# SISTEMA DE PARTIDOS
# ============================================

async def crear_partido(guild_id: str, equipo_local: str, equipo_visitante: str,
                         fecha_hora: datetime, creado_por: str) -> dict:
    """Crea un nuevo partido programado (async)."""
    partidos_col = get_collection('partidos')

    partido = {
        'guild_id': str(guild_id),
        'equipo_local': equipo_local,
        'equipo_visitante': equipo_visitante,
        'fecha_hora': fecha_hora,
        'estado': 'pendiente',
        'notificado': False,
        'resultado': None,
        'goles_local': None,
        'goles_visitante': None,
        'validado_local': False,
        'validado_visitante': False,
        'creado_por': str(creado_por),
        'creado_en': datetime.now()
    }

    result = await partidos_col.insert_one(partido)
    partido['_id'] = result.inserted_id
    return partido


async def get_partidos_pendientes(guild_id: str, limit: int = 10) -> list:
    """Obtiene los partidos pendientes ordenados por fecha (async)."""
    partidos_col = get_collection('partidos')

    cursor = partidos_col.find({
        'guild_id': str(guild_id),
        'estado': {'$in': ['pendiente', 'notificado']}
    }).sort('fecha_hora', 1).limit(limit)

    return await cursor.to_list(length=limit)


async def get_partidos_proximos(guild_id: str, minutos: int = 60) -> list:
    """Obtiene partidos que ocurrirán en los próximos X minutos (async)."""
    partidos_col = get_collection('partidos')

    ahora = datetime.now()
    limite = ahora + timedelta(minutes=minutos)

    cursor = partidos_col.find({
        'guild_id': str(guild_id),
        'estado': 'pendiente',
        'notificado': False,
        'fecha_hora': {'$gte': ahora, '$lte': limite}
    })

    return await cursor.to_list(length=20)


async def marcar_partido_notificado(partido_id) -> bool:
    """Marca un partido como notificado (async)."""
    from bson import ObjectId
    partidos_col = get_collection('partidos')

    result = await partidos_col.update_one(
        {'_id': ObjectId(partido_id) if isinstance(partido_id, str) else partido_id},
        {'$set': {'notificado': True, 'estado': 'notificado'}}
    )
    return result.modified_count > 0


async def get_partido_by_id(partido_id):
    """Obtiene un partido por su ID (async)."""
    from bson import ObjectId
    partidos_col = get_collection('partidos')

    return await partidos_col.find_one({
        '_id': ObjectId(partido_id) if isinstance(partido_id, str) else partido_id
    })


async def registrar_resultado(partido_id, goles_local: int, goles_visitante: int) -> bool:
    """Registra el resultado de un partido y actualiza la tabla (async)."""
    from bson import ObjectId
    partidos_col = get_collection('partidos')

    partido = await get_partido_by_id(partido_id)
    if not partido:
        return False

    await partidos_col.update_one(
        {'_id': ObjectId(partido_id) if isinstance(partido_id, str) else partido_id},
        {'$set': {
            'estado': 'jugado',
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'resultado': f"{goles_local}-{goles_visitante}",
            'fecha_resultado': datetime.now()
        }}
    )

    await actualizar_tabla_por_resultado(
        guild_id=partido['guild_id'],
        equipo_local=partido['equipo_local'],
        equipo_visitante=partido['equipo_visitante'],
        goles_local=goles_local,
        goles_visitante=goles_visitante
    )

    # Procesar cesiones: decrementar partidos de jugadores prestados
    try:
        jugadores_devueltos = await procesar_cesiones_post_partido(
            partido['equipo_local'], partido['equipo_visitante']
        )
        if jugadores_devueltos:
            logger.info(f"📋 {len(jugadores_devueltos)} cesión(es) finalizada(s) tras partido.")
    except Exception as e:
        logger.error(f"Error procesando cesiones post-partido: {e}", exc_info=True)

    return True


async def get_puntuacion_config(guild_id: str) -> dict:
    """Obtiene la configuración de puntuación de un servidor (async).
    Lee pts_victoria, pts_empate, pts_derrota desde server_config.
    """
    config = await get_server_config(guild_id)
    return {
        'pts_victoria': config.get('pts_victoria', DEFAULT_PUNTUACION['pts_victoria']),
        'pts_empate': config.get('pts_empate', DEFAULT_PUNTUACION['pts_empate']),
        'pts_derrota': config.get('pts_derrota', DEFAULT_PUNTUACION['pts_derrota']),
    }


async def set_puntuacion_config(guild_id: str, pts_victoria: int, pts_empate: int, pts_derrota: int) -> bool:
    """Actualiza la configuración de puntuación de un servidor (async)."""
    config_col = get_collection('server_config')
    await get_server_config(guild_id)
    result = await config_col.update_one(
        {'guild_id': str(guild_id)},
        {'$set': {
            'pts_victoria': pts_victoria,
            'pts_empate': pts_empate,
            'pts_derrota': pts_derrota,
            'updated_at': datetime.now()
        }}
    )
    return result.modified_count > 0


async def actualizar_tabla_por_resultado(guild_id: str, equipo_local: str, equipo_visitante: str,
                                          goles_local: int, goles_visitante: int):
    """Actualiza la tabla de posiciones basándose en un resultado (async).
    Lee la puntuación configurable del servidor para calcular PTS.
    """
    tabla_col = get_collection('tabla_posiciones')
    punt = await get_puntuacion_config(guild_id)

    if goles_local > goles_visitante:
        pts_local = punt['pts_victoria']
        pts_visitante = punt['pts_derrota']
    elif goles_local < goles_visitante:
        pts_local = punt['pts_derrota']
        pts_visitante = punt['pts_victoria']
    else:
        pts_local = punt['pts_empate']
        pts_visitante = punt['pts_empate']

    await tabla_col.update_one(
        {'guild_id': str(guild_id), 'equipo': equipo_local},
        {'$inc': {
            'pj': 1,
            'pg': 1 if goles_local > goles_visitante else 0,
            'pe': 1 if goles_local == goles_visitante else 0,
            'pp': 1 if goles_local < goles_visitante else 0,
            'gf': goles_local,
            'gc': goles_visitante,
            'dif': goles_local - goles_visitante,
            'pts': pts_local
        }},
        upsert=True
    )

    await tabla_col.update_one(
        {'guild_id': str(guild_id), 'equipo': equipo_visitante},
        {'$inc': {
            'pj': 1,
            'pg': 1 if goles_visitante > goles_local else 0,
            'pe': 1 if goles_local == goles_visitante else 0,
            'pp': 1 if goles_visitante < goles_local else 0,
            'gf': goles_visitante,
            'gc': goles_local,
            'dif': goles_visitante - goles_local,
            'pts': pts_visitante
        }},
        upsert=True
    )


async def get_tabla_posiciones(guild_id: str) -> list:
    """Obtiene la tabla de posiciones ordenada (async).
    Primero intenta calcular dinámicamente desde `partidos` usando la liga activa
    (igual que la web), y solo si no hay datos cae al legacy `tabla_posiciones`.
    """
    from bson import ObjectId
    from bson.errors import InvalidId

    # 1. Buscar la liga activa
    liga_id = None
    liga = None
    config_col = get_collection('server_config')
    config_global = await config_col.find_one({'_id': 'config_global'})
    logger.info(f"[TABLA] config_global={config_global}")
    if config_global and config_global.get('liga_activa_id'):
        liga_id = str(config_global['liga_activa_id'])
    else:
        ligas_col = get_collection('ligas')
        liga_fb = await ligas_col.find_one({'activa': True})
        if liga_fb:
            liga_id = str(liga_fb.get('_id'))
    logger.info(f"[TABLA] liga_id={liga_id}")

    if liga_id:
        ligas_col = get_collection('ligas')
        try:
            liga = await ligas_col.find_one({'_id': ObjectId(liga_id)})
        except InvalidId:
            liga = None
    logger.info(f"[TABLA] liga={liga.get('nombre') if liga else None}")

    # 2. Puntuación
    if liga:
        pts_v = liga.get('puntos_victoria', 3)
        pts_e = liga.get('puntos_empate', 1)
        pts_d = liga.get('puntos_derrota', 0)
    else:
        punt = await get_puntuacion_config(guild_id)
        pts_v = punt['pts_victoria']
        pts_e = punt['pts_empate']
        pts_d = punt['pts_derrota']

    # 3. Cargar equipos de la liga activa (siempre, aunque no haya resultados)
    equipos_col = get_collection('equipos')
    stats = {}
    if liga_id:
        equipos_liga = await equipos_col.find(
            {'liga_id': liga_id}, {'_id': 0, 'nombre': 1}
        ).to_list(100)
        if not equipos_liga:
            # Algunos equipos usan ObjectId como liga_id
            try:
                equipos_liga = await equipos_col.find(
                    {'liga_id': ObjectId(liga_id)}, {'_id': 0, 'nombre': 1}
                ).to_list(100)
            except InvalidId:
                pass
        for eq in equipos_liga:
            nombre = eq.get('nombre')
            if nombre:
                stats[nombre] = {'equipo': nombre, 'pj': 0, 'pg': 0, 'pe': 0, 'pp': 0,
                                 'gf': 0, 'gc': 0, 'dif': 0, 'pts': 0}
    logger.info(f"[TABLA] equipos en liga: {list(stats.keys())}")

    # 4. Partidos finalizados de la liga activa
    partidos_col = get_collection('partidos')
    query = {'estado': {'$in': ['finalizado', 'jugado', 'walkover']}}
    if liga_id:
        query['liga_id'] = liga_id

    partidos = await partidos_col.find(query).to_list(length=1000)
    logger.info(f"[TABLA] {len(partidos)} partidos finalizados con liga_id")

    # Si no hay resultados con liga_id, busca sin filtro de liga
    if not partidos and liga_id:
        partidos = await partidos_col.find(
            {'estado': {'$in': ['finalizado', 'jugado', 'walkover']}}
        ).to_list(length=1000)
        logger.info(f"[TABLA] sin filtro liga → {len(partidos)} partidos")

    # Si tampoco hay equipos en la liga, fallback a tabla_posiciones legacy
    if not stats and not partidos:
        tabla_col = get_collection('tabla_posiciones')
        for gid in [str(guild_id), '0']:
            cursor = tabla_col.find({'guild_id': gid}).sort([
                ('pts', DESCENDING), ('dif', DESCENDING), ('gf', DESCENDING)
            ])
            resultado = await cursor.to_list(length=50)
            if resultado:
                return resultado
        return []

    # 5. Calcular estadísticas desde partidos
    for p in partidos:
        local = p.get('equipo_local')
        visitante = p.get('equipo_visitante')
        gl = p.get('goles_local') or 0
        gv = p.get('goles_visitante') or 0

        for equipo in (local, visitante):
            if equipo and equipo not in stats:
                stats[equipo] = {'equipo': equipo, 'pj': 0, 'pg': 0, 'pe': 0, 'pp': 0,
                                 'gf': 0, 'gc': 0, 'dif': 0, 'pts': 0}

        if not local or not visitante:
            continue

        stats[local]['pj'] += 1
        stats[visitante]['pj'] += 1
        stats[local]['gf'] += gl
        stats[local]['gc'] += gv
        stats[visitante]['gf'] += gv
        stats[visitante]['gc'] += gl

        if gl > gv:
            stats[local]['pg'] += 1
            stats[local]['pts'] += pts_v
            stats[visitante]['pp'] += 1
            stats[visitante]['pts'] += pts_d
        elif gl < gv:
            stats[visitante]['pg'] += 1
            stats[visitante]['pts'] += pts_v
            stats[local]['pp'] += 1
            stats[local]['pts'] += pts_d
        else:
            stats[local]['pe'] += 1
            stats[local]['pts'] += pts_e
            stats[visitante]['pe'] += 1
            stats[visitante]['pts'] += pts_e

    for s in stats.values():
        s['dif'] = s['gf'] - s['gc']

    return sorted(stats.values(), key=lambda x: (x['pts'], x['dif'], x['gf']), reverse=True)


async def recalcular_tabla_completa(guild_id: str) -> int:
    """Recalcula toda la tabla usando Aggregation Pipelines de MongoDB.
    Útil cuando se cambia la configuración de puntuación.
    Retorna la cantidad de equipos actualizados.
    """
    tabla_col = get_collection('tabla_posiciones')
    partidos_col = get_collection('partidos')
    punt = await get_puntuacion_config(guild_id)

    # Borrar tabla actual
    await tabla_col.delete_many({'guild_id': str(guild_id)})

    pipeline = [
        {'$match': {
            'guild_id': str(guild_id),
            'estado': {'$in': ['jugado', 'finalizado', 'walkover']}
        }},
        {'$facet': {
            'locales': [
                {'$project': {
                    'equipo': '$equipo_local',
                    'gf': {'$ifNull': ['$goles_local', 0]},
                    'gc': {'$ifNull': ['$goles_visitante', 0]}
                }}
            ],
            'visitantes': [
                {'$project': {
                    'equipo': '$equipo_visitante',
                    'gf': {'$ifNull': ['$goles_visitante', 0]},
                    'gc': {'$ifNull': ['$goles_local', 0]}
                }}
            ]
        }},
        {'$project': {'todos_partidos': {'$concatArrays': ['$locales', '$visitantes']}}},
        {'$unwind': '$todos_partidos'},
        {'$replaceRoot': {'newRoot': '$todos_partidos'}},
        {'$match': {'equipo': {'$ne': None}}},
        {'$group': {
            '_id': '$equipo',
            'pj': {'$sum': 1},
            'gf': {'$sum': '$gf'},
            'gc': {'$sum': '$gc'},
            'pg': {'$sum': {'$cond': [{'$gt': ['$gf', '$gc']}, 1, 0]}},
            'pe': {'$sum': {'$cond': [{'$eq': ['$gf', '$gc']}, 1, 0]}},
            'pp': {'$sum': {'$cond': [{'$lt': ['$gf', '$gc']}, 1, 0]}},
            'dif': {'$sum': {'$subtract': ['$gf', '$gc']}}
        }},
        {'$project': {
            '_id': 0,
            'guild_id': str(guild_id),
            'equipo': '$_id',
            'pj': 1, 'pg': 1, 'pe': 1, 'pp': 1, 'gf': 1, 'gc': 1, 'dif': 1,
            'pts': {
                '$add': [
                    {'$multiply': ['$pg', punt['pts_victoria']]},
                    {'$multiply': ['$pe', punt['pts_empate']]},
                    {'$multiply': ['$pp', punt['pts_derrota']]}
                ]
            }
        }}
    ]

    # Ejecutar pipeline y guardar resultados
    resultados = await partidos_col.aggregate(pipeline).to_list(length=None)
    
    if resultados:
        await tabla_col.insert_many(resultados)

    return len(resultados)


async def cancelar_partido(partido_id) -> bool:
    """Cancela un partido programado (async)."""
    from bson import ObjectId
    partidos_col = get_collection('partidos')

    result = await partidos_col.update_one(
        {'_id': ObjectId(partido_id) if isinstance(partido_id, str) else partido_id},
        {'$set': {'estado': 'cancelado'}}
    )
    return result.modified_count > 0


async def validar_resultado_dt(partido_id, es_local: bool) -> dict:
    """Marca la validación de un DT para un resultado pendiente (async)."""
    from bson import ObjectId
    partidos_col = get_collection('partidos')

    campo = 'validado_local' if es_local else 'validado_visitante'

    await partidos_col.update_one(
        {'_id': ObjectId(partido_id) if isinstance(partido_id, str) else partido_id},
        {'$set': {campo: True}}
    )

    return await get_partido_by_id(partido_id)


async def resetear_tabla_posiciones(guild_id: str) -> int:
    """Borra toda la tabla de posiciones para nueva temporada (async)."""
    tabla_col = get_collection('tabla_posiciones')
    result = await tabla_col.delete_many({'guild_id': str(guild_id)})
    return result.deleted_count


# ============================================
# SISTEMA DE CESIONES (PRÉSTAMOS)
# ============================================

async def procesar_cesiones_post_partido(equipo_local: str, equipo_visitante: str) -> list:
    """
    Después de registrar un resultado, decrementa los partidos de cesión
    de los jugadores cedidos en ambos equipos.
    Si un jugador llegó a 0 partidos restantes, lo devuelve a su equipo de origen.
    Retorna una lista de dicts con los jugadores devueltos para anunciar.
    """
    jugadores_col = get_collection('jugadores')
    jugadores_devueltos = []

    # Buscar jugadores cedidos en ambos equipos que jugaron
    for equipo in [equipo_local, equipo_visitante]:
        cursor = jugadores_col.find({
            'equipo': equipo,
            'es_cesion': True,
            'partidos_cesion': {'$gt': 0}
        })
        cedidos = await cursor.to_list(length=50)

        for jugador in cedidos:
            nuevos_partidos = jugador['partidos_cesion'] - 1

            if nuevos_partidos <= 0:
                # Cesión terminada: devolver al equipo de origen
                equipo_origen = jugador.get('equipo_origen', None)
                if equipo_origen:
                    await jugadores_col.update_one(
                        {'discord_id': jugador['discord_id']},
                        {
                            '$set': {'equipo': equipo_origen},
                            '$unset': {
                                'es_cesion': '',
                                'partidos_cesion': '',
                                'equipo_origen': '',
                                'fecha_cesion': ''
                            }
                        }
                    )
                    jugadores_devueltos.append({
                        'discord_id': jugador['discord_id'],
                        'nombre': jugador.get('nombre', '???'),
                        'equipo_temporal': equipo,
                        'equipo_origen': equipo_origen
                    })
                    logger.info(
                        f"📋 Cesión finalizada: {jugador.get('nombre')} vuelve a {equipo_origen} "
                        f"(estaba en {equipo})"
                    )
                else:
                    # Fallback: si no hay equipo_origen, solo limpiar flags
                    await jugadores_col.update_one(
                        {'discord_id': jugador['discord_id']},
                        {'$unset': {
                            'es_cesion': '',
                            'partidos_cesion': '',
                            'equipo_origen': '',
                            'fecha_cesion': ''
                        }}
                    )
                    logger.warning(
                        f"⚠️ Cesión finalizada sin equipo_origen para {jugador.get('nombre')}"
                    )
            else:
                # Aún quedan partidos: solo decrementar
                await jugadores_col.update_one(
                    {'discord_id': jugador['discord_id']},
                    {'$set': {'partidos_cesion': nuevos_partidos}}
                )
                logger.debug(
                    f"📋 Cesión: {jugador.get('nombre')} le quedan {nuevos_partidos} partidos "
                    f"en {equipo}"
                )

    return jugadores_devueltos

