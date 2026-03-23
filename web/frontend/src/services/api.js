import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor: Agregar token JWT a cada petición si existe
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Interceptor: Manejar errores 401 (token expirado/inválido)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

export const ligaService = {
    // --- DATOS PÚBLICOS ---
    getStats: async () => {
        const response = await api.get('/stats/general');
        return response.data;
    },

    getMercadoStatus: async () => {
        const response = await api.get('/mercado/status');
        return response.data;
    },

    getEquipos: async () => {
        const response = await api.get('/equipos');
        return response.data;
    },

    getClasificacion: async (ligaId = null) => {
        const query = ligaId ? `?liga_id=${ligaId}` : '';
        const response = await api.get(`/clasificacion${query}`);
        return response.data;
    },

    getLigasDisponibles: async () => {
        const response = await api.get('/ligas-disponibles');
        return response.data;
    },

    // --- JORNADAS Y PARTIDOS ---
    getJornadas: async (ligaId, jornada = null) => {
        const query = jornada ? `?jornada=${jornada}` : '';
        const response = await api.get(`/jornadas/${ligaId}${query}`);
        return response.data;
    },

    getPartidosEquipo: async (equipoNombre, ligaId = null) => {
        const query = ligaId ? `?liga_id=${ligaId}` : '';
        const response = await api.get(`/partidos-equipo/${encodeURIComponent(equipoNombre)}${query}`);
        return response.data;
    },

    getJugadores: async (filtro = null) => {
        const query = filtro ? `?filtro=${encodeURIComponent(filtro)}` : '';
        const response = await api.get(`/mercado/jugadores${query}`);
        return response.data;
    },

    getJugadorDetalle: async (discordId) => {
        const response = await api.get(`/jugadores/${discordId}`);
        return response.data;
    },

    getEstadisticas: async () => {
        const response = await api.get('/estadisticas');
        return response.data;
    },

    // --- ADMIN ---
    updatePresupuesto: async (equipoId, presupuesto) => {
        const response = await api.patch(`/admin/equipos/${equipoId}/presupuesto`, { presupuesto });
        return response.data;
    },

    updatePrecioJugador: async (discordId, precio, clausula) => {
        const response = await api.patch(`/admin/jugadores/${discordId}/economia`, { precio, clausula });
        return response.data;
    },

    updatePresupuestosMasivo: async (equipoIds, presupuesto) => {
        const response = await api.patch('/admin/equipos/presupuesto-masivo', { equipo_ids: equipoIds, presupuesto });
        return response.data;
    },

    updatePreciosJugadoresMasivo: async (jugadorIds, precio, clausula) => {
        const response = await api.patch('/admin/jugadores/economia-masiva', { jugador_ids: jugadorIds, precio, clausula });
        return response.data;
    },

    updatePlayerStats: async (discordId, stats) => {
        const response = await api.patch(`/admin/jugadores/${discordId}/stats`, stats);
        return response.data;
    },

    updatePlayerBan: async (discordId, baneado, motivo) => {
        const response = await api.patch(`/admin/jugadores/${discordId}/ban`, { baneado, motivo });
        return response.data;
    },

    getAuditoria: async () => {
        const response = await api.get('/admin/auditoria?limit=100');
        return response.data;
    },

    getPartidosPendientes: async () => {
        const response = await api.get('/partidos?estado=pendiente');
        return response.data;
    },

    // --- PARTIDOS ---
    getPartidos: async (estado = null) => {
        const query = estado ? `?estado=${estado}` : '';
        const response = await api.get(`/partidos${query}`);
        return response.data;
    },

    programarPartido: async (datosPartido) => {
        const response = await api.post('/partidos', datosPartido);
        return response.data;
    },

    reportarResultadoDirecto: async (partidoId, dataReporte) => {
        const response = await api.post(`/partidos/${partidoId}/directo`, dataReporte);
        return response.data;
    },

    registrarResultadoPartido: async (partidoId, golesLocal, golesVisitante, mvpId = null, rojasIds = []) => {
        const dataReporte = {
            goles_local: golesLocal,
            goles_visitante: golesVisitante,
            jugadores_local: [],
            jugadores_visitante: [],
            evidencia_url: null,
            notas_admin: null,
        };

        if (mvpId) {
            dataReporte.jugadores_local.push({
                discord_id: mvpId,
                goles: 0,
                asistencias: 0,
                es_mvp: true,
            });
        }

        if (Array.isArray(rojasIds)) {
            rojasIds.forEach((discordId) => {
                dataReporte.jugadores_local.push({
                    discord_id: discordId,
                    goles: 0,
                    asistencias: 0,
                    es_mvp: false,
                });
            });
        }

        const response = await api.post(`/partidos/${partidoId}/directo`, dataReporte);
        return response.data;
    },

    // --- CLASIFICACIÓN (Admin) ---
    getPuntuacion: async () => {
        const response = await api.get('/admin/puntuacion');
        return response.data;
    },

    updatePuntuacion: async (payload) => {
        const response = await api.patch('/admin/puntuacion', payload);
        return response.data;
    },

    getGlobalConfig: async () => {
        const response = await api.get('/admin/system/config');
        return response.data;
    },

    updateGlobalConfig: async (payload) => {
        const response = await api.post('/admin/system/config', payload);
        return response.data;
    },

    registrarResultado: async (equipo_local, equipo_visitante, goles_local, goles_visitante) => {
        const response = await api.post('/admin/resultado', { equipo_local, equipo_visitante, goles_local, goles_visitante });
        return response.data;
    },

    registrarWalkover: async (ganador, perdedor) => {
        const response = await api.post('/admin/walkover', { ganador, perdedor });
        return response.data;
    },

    recalcularTabla: async () => {
        const response = await api.post('/admin/recalcular_tabla');
        return response.data;
    },

    resetearTabla: async () => {
        const response = await api.post('/admin/resetear_tabla');
        return response.data;
    },

    getEstadoLiga: async () => {
        const response = await api.get('/admin/estado_liga');
        return response.data;
    },

    generarPlayoffs: async () => {
        const response = await api.post('/admin/generar_playoffs');
        return response.data;
    },

    eliminarPartido: async (partidoId) => {
        const response = await api.delete(`/partidos/${partidoId}`);
        return response.data;
    },

    // --- SISTEMA ---
    getSystemStatus: async () => {
        const response = await api.get('/admin/system/status');
        return response.data;
    },

    executePM2Action: async (action, appName = "amapicks-bot") => {
        const response = await api.post('/admin/system/pm2', { action, app_name: appName });
        return response.data;
    },

    triggerSyncCommands: async () => {
        const response = await api.post('/admin/system/sync');
        return response.data;
    },

    sendGlobalAnnouncement: async (announcementData) => {
        const response = await api.post('/admin/system/announce', announcementData);
        return response.data;
    },

    getGlobalConfig: async () => {
        const response = await api.get('/admin/system/config');
        return response.data;
    },

    updateGlobalConfig: async (configData) => {
        const response = await api.post('/admin/system/config', configData);
        return response.data;
    },

    // --- ZONA DE PELIGRO ---

    generateBackup: async () => {
        const response = await api.post('/admin/system/backup', {}, { responseType: 'blob' });
        return response.data;
    },

    resetSeason: async () => {
        const response = await api.post('/admin/system/reset-season');
        return response.data;
    },

    nukeDatabase: async (confirmationText) => {
        const response = await api.post('/admin/system/nuke', { confirmation_text: confirmationText });
        return response.data;
    },

    purgeLogs: async () => {
        const response = await api.post('/admin/system/purge-logs');
        return response.data;
    },

// --- LIGAS MANAGER (Múltiples Ligas D1, D2, etc.) ---

    getLigas: async (activasOnly = false) => {
        const response = await api.get(`/admin/ligas${activasOnly ? '?activas_only=true' : ''}`);
        return response.data;
    },

    getLigaById: async (ligaId) => {
        const response = await api.get(`/admin/ligas/${ligaId}`);
        return response.data;
    },

    crearLiga: async (ligaData) => {
        const response = await api.post('/admin/ligas', ligaData);
        return response.data;
    },

    actualizarLiga: async (ligaId, updateData) => {
        const response = await api.patch(`/admin/ligas/${ligaId}`, updateData);
        return response.data;
    },

    eliminarLiga: async (ligaId) => {
        const response = await api.delete(`/admin/ligas/${ligaId}`);
        return response.data;
    },

    getLigaActiva: async () => {
        const response = await api.get('/admin/liga-activa');
        return response.data;
    },

    establecerLigaActiva: async (ligaId) => {
        const response = await api.post('/admin/liga-activa', { liga_id: ligaId });
        return response.data;
    },

    getEquiposLiga: async (ligaId) => {
        const response = await api.get(`/admin/ligas/${ligaId}/equipos`);
        return response.data;
    },

    agregarEquipoALiga: async (ligaId, equipoId) => {
        const response = await api.post(`/admin/ligas/${ligaId}/equipos`, {
            equipo_id: equipoId,
            liga_id: ligaId
        });
        return response.data;
    },

    removerEquipoDeLiga: async (ligaId, equipoId) => {
        const response = await api.delete(`/admin/ligas/${ligaId}/equipos/${equipoId}`);
        return response.data;
    },

    /**
     * Genera fixture (ida/vuelta o D1). Unifica el antiguo asistente de temporada.
     * @param {object} payload - fecha_inicio, dias_entre_jornadas, hora_default, playoffs_habilitados, clasificados_playoffs, tipo_liga, dias_pausa_copa
     */
    generarFixtureLiga: async (ligaId, payload) => {
        const response = await api.post(`/admin/ligas/${ligaId}/generar-fixture`, payload);
        return response.data;
    },

    avanzarJornadaLiga: async (ligaId) => {
        const response = await api.post(`/admin/ligas/${ligaId}/avanzar-jornada`);
        return response.data;
    },

    getEstadoDetalladoLiga: async (ligaId) => {
        const response = await api.get(`/admin/ligas/${ligaId}/estado`);
        return response.data;
    },

    // --- COPA (24 EQUIPOS) ---
    inscribirEquipoCopa: async (ligaId, equipoId, ligaOrigenId = null) => {
        const response = await api.post(`/admin/ligas/${ligaId}/copa/inscribir`, {
            equipo_id: equipoId,
            liga_origen_id: ligaOrigenId
        });
        return response.data;
    },

    getInscripcionesCopa: async (ligaId) => {
        const response = await api.get(`/admin/ligas/${ligaId}/copa/inscripciones`);
        return response.data;
    },

    sembrarEquiposCopa: async (ligaId) => {
        const response = await api.post(`/admin/ligas/${ligaId}/copa/sembrar`);
        return response.data;
    },

    generarBracketCopa: async (ligaId, fechaInicio, diasEntreRondas = 3, horaDefault = '20:00') => {
        const response = await api.post(`/admin/ligas/${ligaId}/copa/generar-bracket`, {
            fecha_inicio: fechaInicio,
            dias_entre_rondas: diasEntreRondas,
            hora_default: horaDefault
        });
        return response.data;
    },

    // --- FACTOR RIVAL ---
    calcularFactorRival: async (ligaId, equipoGanador, equipoPerdedor) => {
        const response = await api.get(`/admin/ligas/${ligaId}/factor-rival/calcular?equipo_ganador=${equipoGanador}&equipo_perdedor=${equipoPerdedor}`);
        return response.data;
    },

    getTablaFactorRival: async (ligaId) => {
        const response = await api.get(`/admin/ligas/${ligaId}/factor-rival/tabla`);
        return response.data;
    },
};

export default api;
