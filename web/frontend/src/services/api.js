import axios from 'axios';

const api = axios.create({
    baseURL: 'http://104.243.47.46/api',
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

    getClasificacion: async () => {
        const response = await api.get('/clasificacion');
        return response.data;
    },

    getJugadores: async (filtro) => {
        const response = await api.get(`/mercado/jugadores?filtro=${filtro}`);
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

    // --- CLASIFICACIÓN (Admin) ---
    getPuntuacion: async () => {
        const response = await api.get('/admin/puntuacion');
        return response.data;
    },

    updatePuntuacion: async (pts_victoria, pts_empate, pts_derrota) => {
        const response = await api.patch('/admin/puntuacion', { pts_victoria, pts_empate, pts_derrota });
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

    // --- LIGA AUTOMATION ---
    generarCalendarioLiga: async (diasEntreJornadas, fechaInicio, horaDefault = '20:00', playoffsHabilitados = true, clasificadosPlayoffs = 4) => {
        const response = await api.post('/admin/generar_calendario_liga', {
            dias_entre_jornadas: diasEntreJornadas,
            fecha_inicio: fechaInicio,
            hora_default: horaDefault,
            playoffs_habilitados: playoffsHabilitados,
            clasificados_playoffs: clasificadosPlayoffs
        });
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
    }
};

export default api;
