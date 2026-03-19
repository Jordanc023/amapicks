import { useState, useEffect, useCallback } from 'react';
import { ligaService } from '../services/api';
import { useAuth } from '../context/AuthContext';

/**
 * Hook centralizado para el estado y lógica del panel Admin.
 * Extrae TODO el state + handlers de Admin.jsx para mantener el componente principal limpio.
 */
export default function useAdminData() {
    const { user, loading: authLoading } = useAuth();

    // --- Data State ---
    const [loading, setLoading] = useState(true);
    const [equipos, setEquipos] = useState([]);
    const [jugadores, setJugadores] = useState([]);
    const [auditoriaLogs, setAuditoriaLogs] = useState([]);
    const [systemStatus, setSystemStatus] = useState(null);
    const [estadoLiga, setEstadoLiga] = useState(null);
    const [partidosPendientes, setPartidosPendientes] = useState([]);
    const [globalConfig, setGlobalConfig] = useState(null);
    const [loadingConfig, setLoadingConfig] = useState(false);

    // --- UI State ---
    const [activeTab, setActiveTab] = useState('equipos');
    const [activeSystemTab, setActiveSystemTab] = useState('general');
    const [saving, setSaving] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    // --- Form States ---
    const [presupuestos, setPresupuestos] = useState({});
    const [preciosJugadores, setPreciosJugadores] = useState({});
    const [puntuacion, setPuntuacion] = useState({ pts_victoria: 3, pts_empate: 1, pts_derrota: 0 });
    const [resultadoForm, setResultadoForm] = useState({ equipo_local: '', equipo_visitante: '', goles_local: 0, goles_visitante: 0 });
    const [walkoverForm, setWalkoverForm] = useState({ ganador: '', perdedor: '' });
    const [calendarioForm, setCalendarioForm] = useState({
        dias_entre_jornadas: 3,
        fecha_inicio: '',
        hora_default: '20:00',
        playoffs_habilitados: true,
        clasificados_playoffs: 4,
        tipo_liga: 'estandar',
        dias_pausa_copa: 7
    });
    const [anuncioForm, setAnuncioForm] = useState({ titulo: '', mensaje: '', imagen_url: '', color: '#9b59b6', canal_destino: 'anuncios' });

    // --- Modal State ---
    const [isStatsModalOpen, setIsStatsModalOpen] = useState(false);
    const [selectedJugador, setSelectedJugador] = useState(null);
    const [isCreatePartidoModalOpen, setIsCreatePartidoModalOpen] = useState(false);
    const [isReporteModalOpen, setIsReporteModalOpen] = useState(false);
    const [selectedPartido, setSelectedPartido] = useState(null);
    const [isExpressModalOpen, setIsExpressModalOpen] = useState(false);
    const [isWalkoverModalOpen, setIsWalkoverModalOpen] = useState(false);
    const [isPuntosModalOpen, setIsPuntosModalOpen] = useState(false);
    const [isDangerZoneOpen, setIsDangerZoneOpen] = useState(false);

    // ========================================================================
    //  DATA LOADING
    // ========================================================================
    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const [eqRes, jRes, auditRes, statusRes, ligaEstado, pendientes] = await Promise.all([
                ligaService.getEquipos().catch(() => []),
                ligaService.getJugadores().catch(() => []),
                ligaService.getAuditoria().catch(() => []),
                ligaService.getSystemStatus().catch(() => null),
                ligaService.getEstadoLiga().catch(() => null),
                ligaService.getPartidosPendientes().catch(() => [])
            ]);

            setEquipos(eqRes);
            setJugadores(jRes);
            setAuditoriaLogs(auditRes);
            setSystemStatus(statusRes);
            setEstadoLiga(ligaEstado);
            setPartidosPendientes(pendientes);

            // Inicializar presupuestos
            const budgets = {};
            eqRes.forEach(eq => {
                const id = eq.role_id || eq.nombre;
                budgets[id] = eq.presupuesto || 0;
            });
            setPresupuestos(budgets);

            // Inicializar precios de jugadores
            const precios = {};
            jRes.forEach(j => {
                precios[j.discord_id] = {
                    precio: j.precio || 0,
                    clausula: j.clausula || 0
                };
            });
            setPreciosJugadores(precios);
        } catch (error) {
            console.error('Error cargando datos admin:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Cargar config global cuando se cambia al subtab 'config'
    useEffect(() => {
        if (activeSystemTab === 'config' && !globalConfig) {
            setLoadingConfig(true);
            ligaService.getGlobalConfig()
                .then(cfg => setGlobalConfig(cfg))
                .catch(() => setGlobalConfig({}))
                .finally(() => setLoadingConfig(false));
        }
    }, [activeSystemTab, globalConfig]);

    useEffect(() => {
        if (user?.admin) {
            loadData();
        }
    }, [user, loadData]);

    // ========================================================================
    //  EQUIPOS HANDLERS
    // ========================================================================
    const handlePresupuestoChange = (equipoId, value) => {
        setPresupuestos(prev => ({ ...prev, [equipoId]: parseInt(value) || 0 }));
    };

    const handleUpdatePresupuesto = async (equipoId) => {
        setSaving(equipoId);
        try {
            await ligaService.updatePresupuesto(equipoId, presupuestos[equipoId]);
            alert("✅ Presupuesto actualizado correctamente.");
        } catch (error) {
            console.error(error);
            alert("❌ Error al actualizar presupuesto.");
        } finally {
            setSaving(null);
        }
    };

    // ========================================================================
    //  JUGADORES HANDLERS
    // ========================================================================
    const handlePrecioJugadorChange = (discordId, field, value) => {
        setPreciosJugadores(prev => ({
            ...prev,
            [discordId]: { ...prev[discordId], [field]: parseInt(value) || 0 }
        }));
    };

    const handleUpdatePrecio = async (discordId) => {
        setSaving(discordId);
        try {
            const { precio, clausula } = preciosJugadores[discordId];
            await ligaService.updatePrecioJugador(discordId, precio, clausula);
            alert("✅ Valor del jugador actualizado.");
        } catch (error) {
            console.error(error);
            alert("❌ Error al actualizar precio.");
        } finally {
            setSaving(null);
        }
    };

    const openEditStats = (jugador) => {
        setSelectedJugador(jugador);
        setIsStatsModalOpen(true);
    };

    const handleStatsSave = (discordId, stats, baneado) => {
        setJugadores(prev => prev.map(p =>
            p.discord_id === discordId ? {
                ...p,
                estadisticas_temporada: { ...p.estadisticas_temporada, ...stats },
                baneado: baneado
            } : p
        ));
    };

    const filteredJugadores = jugadores.filter(j =>
        j.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (j.equipo && j.equipo.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // ========================================================================
    //  PARTIDOS HANDLERS
    // ========================================================================
    const handleRegistrarResultado = async (partidoId, golesLocal, golesVisitante, mvpId, rojasIds) => {
        try {
            await ligaService.registrarResultadoPartido(partidoId, golesLocal, golesVisitante, mvpId, rojasIds);
            alert("✅ Resultado registrado con éxito.");
            setIsReporteModalOpen(false);
            setSelectedPartido(null);
            await loadData();
        } catch (error) {
            console.error(error);
            alert("❌ Error al registrar resultado.");
        }
    };

    const handleProgramarPartido = async (datos) => {
        try {
            await ligaService.programarPartido(datos);
            alert("✅ Partido programado con éxito. Los DTs han sido anexados a la agenda de la liga.");
        } catch (error) {
            console.error(error);
            alert("❌ Ocurrió un error al programar el partido.");
        }
    };

    const handleEliminarPartido = async (partidoId) => {
        if (!window.confirm("¿Estás seguro de que quieres eliminar este partido?\n\nEsta acción no se puede deshacer.")) return;
        try {
            await ligaService.eliminarPartido(partidoId);
            alert("✅ Partido eliminado correctamente");
            await loadData();
        } catch (error) {
            alert("❌ Error al eliminar partido.");
            console.error(error);
        }
    };

    // ========================================================================
    //  CLASIFICACIÓN HANDLERS
    // ========================================================================
    const handleSavePuntuacion = async () => {
        setSaving('puntuacion');
        try {
            await ligaService.updatePuntuacion(puntuacion.pts_victoria, puntuacion.pts_empate, puntuacion.pts_derrota);
            alert("✅ Puntuación actualizada y tabla recalculada.");
        } catch (e) { alert("❌ Error al guardar puntuación."); }
        finally { setSaving(null); }
    };

    const handleRegistrarResultadoManual = async () => {
        const { equipo_local, equipo_visitante, goles_local, goles_visitante } = resultadoForm;
        if (!equipo_local || !equipo_visitante) return alert("Selecciona ambos equipos.");
        if (equipo_local === equipo_visitante) return alert("Un equipo no puede jugar contra sí mismo.");
        setSaving('resultado');
        try {
            const res = await ligaService.registrarResultado(equipo_local, equipo_visitante, parseInt(goles_local), parseInt(goles_visitante));
            alert(`⚽ ${res.message}`);
            setResultadoForm({ equipo_local: '', equipo_visitante: '', goles_local: 0, goles_visitante: 0 });
        } catch (e) { alert("❌ Error al registrar resultado."); }
        finally { setSaving(null); }
    };

    const handleRegistrarWalkover = async () => {
        const { ganador, perdedor } = walkoverForm;
        if (!ganador || !perdedor) return alert("Selecciona ambos equipos.");
        if (ganador === perdedor) return alert("No puedes dictar W.O. contra el mismo equipo.");
        if (!window.confirm(`¿Dictar W.O. a favor de ${ganador} contra ${perdedor}? (3-0 automático)`)) return;
        setSaving('walkover');
        try {
            const res = await ligaService.registrarWalkover(ganador, perdedor);
            alert(`🚫 ${res.message}`);
            setWalkoverForm({ ganador: '', perdedor: '' });
        } catch (e) { alert("❌ Error al registrar walkover."); }
        finally { setSaving(null); }
    };

    const handleRecalcularTabla = async () => {
        if (!window.confirm("¿Recalcular toda la tabla desde el historial de partidos?")) return;
        setSaving('recalcular');
        try {
            const res = await ligaService.recalcularTabla();
            alert(`🔄 ${res.message} (${res.equipos_procesados} equipos)`);
        } catch (e) { alert("❌ Error."); }
        finally { setSaving(null); }
    };

    const handleResetearTabla = async () => {
        if (!window.confirm("⚠️ PELIGRO: Esto borrará TODA la tabla de posiciones. ¿Continuar?")) return;
        if (!window.confirm("¿Estás REALMENTE seguro? Esta acción no se puede deshacer.")) return;
        setSaving('resetear');
        try {
            const res = await ligaService.resetearTabla();
            alert(`🗑️ ${res.message} (${res.registros_eliminados} eliminados)`);
        } catch (e) { alert("❌ Error."); }
        finally { setSaving(null); }
    };

    // ========================================================================
    //  LIGA AUTOMATION HANDLERS
    // ========================================================================
    const handleGenerarCalendario = async () => {
        const { dias_entre_jornadas, fecha_inicio, hora_default, playoffs_habilitados, clasificados_playoffs, tipo_liga, dias_pausa_copa } = calendarioForm;
        if (!fecha_inicio) {
            alert("❌ Debes seleccionar una fecha de inicio.");
            return;
        }
        if (!window.confirm(`¿Generar calendario completo?\n\n• ${equipos.length} equipos\n• Formato: ${tipo_liga === 'd1' ? 'Liga D1 (Ida y Vuelta con Pausa)' : 'Todos contra todos'}\n• ${dias_entre_jornadas} días entre jornadas\n• Playoffs: ${playoffs_habilitados ? 'Sí' : 'No'}`)) return;

        setSaving('calendario');
        try {
            const res = await ligaService.generarCalendarioLiga(
                dias_entre_jornadas,
                fecha_inicio,
                hora_default,
                playoffs_habilitados,
                clasificados_playoffs,
                tipo_liga,
                dias_pausa_copa
            );
            alert(`✅ ${res.message}\n📊 ${res.equipos} equipos, ${res.jornadas} jornadas, ${res.partidos_creados} partidos creados`);
            await loadData();
        } catch (e) {
            alert("❌ Error al generar calendario.");
            console.error(e);
        }
        finally { setSaving(null); }
    };

    const handleGenerarPlayoffs = async () => {
        if (!window.confirm("¿Generar playoffs automáticamente basados en la tabla de posiciones actual?\n\nSe crearán semifinales: 1° vs 4°, 2° vs 3°")) return;
        setSaving('playoffs');
        try {
            const res = await ligaService.generarPlayoffs();
            alert(`🏆 ${res.message}\n⚽ ${res.semirfinales_creadas} semifinales creadas\n🏅 Clasificados: ${res.equipos_clasificados.join(', ')}`);
            await loadData();
        } catch (e) {
            alert("❌ Error al generar playoffs.");
            console.error(e);
        }
        finally { setSaving(null); }
    };

    // ========================================================================
    //  SYSTEM HANDLERS
    // ========================================================================
    const handlePM2Action = async (action) => {
        if (!window.confirm(`⚠️ ESTÁS A PUNTO DE EJECUTAR UN COMANDO DE SERVIDOR.\n\n¿Deseas enviar un 'PM2 ${action.toUpperCase()}' al bot de Discord?`)) return;
        setSaving(`pm2-${action}`);
        try {
            const res = await ligaService.executePM2Action(action);
            if (res.simulated) {
                alert(`ℹ️ Simulación (No estás en VPS):\n\n${res.message}`);
            } else {
                alert(`✅ ${res.message}`);
            }
            if (action === 'restart') {
                setTimeout(loadData, 5000);
            }
        } catch (error) {
            const errorMsg = error.response?.data?.detail || "Error desconocido";
            alert(`❌ Acción PM2 Fallida:\n\n${errorMsg}`);
        } finally {
            setSaving(null);
        }
    };

    const handleSyncCommands = async () => {
        if (!window.confirm("¿Deseas enviar la orden de Sincronización de Slash Commands al Bot? Esto podría tardar hasta 1 minuto en reflejarse.")) return;
        setSaving('sync-cmds');
        try {
            const res = await ligaService.triggerSyncCommands();
            alert(`✅ ${res.message}`);
        } catch (error) {
            alert("❌ Error al solicitar sincronización de comandos.");
        } finally {
            setSaving(null);
        }
    };

    const handleSendAnnouncement = async () => {
        if (!anuncioForm.titulo || !anuncioForm.mensaje) {
            alert("⚠️ El título y el mensaje son obligatorios.");
            return;
        }
        if (!window.confirm("¿Estás seguro de enviar este Anuncio Oficial al Discord?\nSe publicará de inmediato en el canal destino.")) return;
        setSaving('anuncio');
        try {
            const res = await ligaService.sendGlobalAnnouncement(anuncioForm);
            alert(`✅ ${res.message}`);
            setAnuncioForm({ titulo: '', mensaje: '', imagen_url: '', color: '#9b59b6', canal_destino: 'anuncios' });
        } catch (error) {
            const errorMsg = error.response?.data?.detail || "Error al enviar el anuncio";
            alert(`❌ Fallo: ${errorMsg}`);
        } finally {
            setSaving(null);
        }
    };

    // ========================================================================
    //  MAINTENANCE / DANGER HANDLERS
    // ========================================================================
    const handleBackup = async () => {
        if (!window.confirm("💾 ¿Deseas descargar un volcado completo de la base de datos en JSON localmente?")) return;
        setSaving('backup');
        try {
            const data = await ligaService.generateBackup();
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `amapicks_backup_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            alert("✅ Volcado BSON descargado correctamente. Guárdalo en un lugar seguro.");
        } catch (error) {
            alert(`❌ Error al crear volcado: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(null);
        }
    };

    const handleResetSeason = async () => {
        if (!window.confirm("🔪 ADVERTENCIA: Esta acción eliminará toda la historia de esta edición (Partidos, Tabla de posiciones, MVP/Rojas per capita en Jugadores).\n\n¿Estás SEGURO de que deseas Iniciar Nueva Temporada?")) return;
        let pass = window.prompt("Por favor, escribe 'RESETEAR' para confirmar esta acción irreversible:");
        if (pass !== "RESETEAR") {
            alert("❌ Acción cancelada: Texto de seguridad incorrecto.");
            return;
        }
        setSaving('reset');
        try {
            const res = await ligaService.resetSeason();
            alert(`✅ ${res.message}`);
            await loadData();
        } catch (error) {
            alert(`❌ Error: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(null);
        }
    };

    const handleNuke = async () => {
        let confirmacion = window.prompt(
            "☢️ ALERTA NUCLEAR MÁXIMA ☢️\n" +
            "Estás a punto de borrar ABSOLUTAMENTE TODO.\n" +
            "Se eliminarán:\n\n" +
            "❌ Partidos\n❌ Clasificación\n❌ Fichajes/Jugadores\n❌ Agentes Libres\n❌ Equipos\n❌ Economía\n\n" +
            "Para confirmar el inicio de 0 absoluto, escribe EXACTAMENTE:\n" +
            "\"CONFIRMAR BORRADO TOTAL Y COMENZAR DE CERO\""
        );
        if (confirmacion !== "CONFIRMAR BORRADO TOTAL Y COMENZAR DE CERO") {
            return alert("❌ Catástrofe evitada: Código de confirmación incorrecto.");
        }
        setSaving('nuke');
        try {
            const res = await ligaService.nukeDatabase(confirmacion);
            alert(`🔥💥 NUCLEAR LAUNCH SUCCESSFUL: ${res.message}`);
            window.location.reload();
        } catch (error) {
            alert(`❌ Fallo crítico de misil: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(null);
        }
    };

    const handlePurgeLogs = async () => {
        if (!window.confirm("🧹 ¿Deseas limpiar las transacciones bancarias y acciones de auditoría mayores a 60 días para alivianar el tamaño de la BD?")) return;
        setSaving('purge');
        try {
            const res = await ligaService.purgeLogs();
            alert(`✅ ${res.message}`);
        } catch (error) {
            alert(`❌ Error al purgar logs: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(null);
        }
    };

    const handleSaveGlobalConfig = async () => {
        if (!globalConfig) return;
        setSaving('global-config');
        try {
            const res = await ligaService.updateGlobalConfig({
                ...globalConfig,
                limite_plantilla: parseInt(globalConfig.limite_plantilla) || 12,
                pts_victoria: parseInt(globalConfig.pts_victoria) || 3,
                pts_empate: parseInt(globalConfig.pts_empate) || 1,
                pts_derrota: parseInt(globalConfig.pts_derrota) || 0,
                walkover_gf: parseInt(globalConfig.walkover_gf) || 3,
                walkover_gc: parseInt(globalConfig.walkover_gc) || 0
            });
            alert(`✅ ${res.message}`);
        } catch (error) {
            alert(`❌ Error al guardar la configuración: ${error.response?.data?.detail || error.message}`);
        } finally {
            setSaving(null);
        }
    };

    // ========================================================================
    //  UTILS
    // ========================================================================
    const formatMoney = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        }).format(amount);
    };

    // ========================================================================
    //  RETURN
    // ========================================================================
    return {
        // Auth
        user,
        authLoading,

        // Data
        loading,
        equipos,
        jugadores,
        filteredJugadores,
        auditoriaLogs,
        systemStatus,
        estadoLiga,
        partidosPendientes,
        globalConfig,
        loadingConfig,

        // UI state
        activeTab,
        setActiveTab,
        activeSystemTab,
        setActiveSystemTab,
        saving,
        searchTerm,
        setSearchTerm,

        // Forms
        presupuestos,
        preciosJugadores,
        puntuacion,
        setPuntuacion,
        resultadoForm,
        setResultadoForm,
        walkoverForm,
        setWalkoverForm,
        calendarioForm,
        setCalendarioForm,
        anuncioForm,
        setAnuncioForm,
        setGlobalConfig,

        // Modals
        isStatsModalOpen,
        setIsStatsModalOpen,
        selectedJugador,
        isCreatePartidoModalOpen,
        setIsCreatePartidoModalOpen,
        isReporteModalOpen,
        setIsReporteModalOpen,
        selectedPartido,
        setSelectedPartido,
        isExpressModalOpen,
        setIsExpressModalOpen,
        isWalkoverModalOpen,
        setIsWalkoverModalOpen,
        isPuntosModalOpen,
        setIsPuntosModalOpen,
        isDangerZoneOpen,
        setIsDangerZoneOpen,

        // Data actions
        loadData,

        // Equipos handlers
        handlePresupuestoChange,
        handleUpdatePresupuesto,

        // Jugadores handlers
        handlePrecioJugadorChange,
        handleUpdatePrecio,
        openEditStats,
        handleStatsSave,

        // Partidos handlers
        handleRegistrarResultado,
        handleProgramarPartido,
        handleEliminarPartido,

        // Clasificación handlers
        handleSavePuntuacion,
        handleRegistrarResultadoManual,
        handleRegistrarWalkover,
        handleRecalcularTabla,
        handleResetearTabla,

        // Liga automation handlers
        handleGenerarCalendario,
        handleGenerarPlayoffs,

        // System handlers
        handlePM2Action,
        handleSyncCommands,
        handleSendAnnouncement,

        // Maintenance handlers
        handleBackup,
        handleResetSeason,
        handleNuke,
        handlePurgeLogs,
        handleSaveGlobalConfig,

        // Utils
        formatMoney,
    };
}
