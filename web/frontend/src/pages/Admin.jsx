import React, { useState, useEffect } from 'react';
import { Settings, DollarSign, Users, Shield, Save, Search, RefreshCw, ShieldAlert, Activity, Edit3, Gavel, Calendar, ArrowRightLeft, FileText, AlertTriangle, Trophy, Ban, RotateCcw, Trash2, Clock, Edit, ChevronDown, X } from 'lucide-react';
import { ligaService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import EditStatsModal from '../components/admin/EditStatsModal';
import CreatePartidoModal from '../components/admin/CreatePartidoModal';
import ReportarPartidoModal from '../components/admin/ReportarPartidoModal';

const Admin = () => {
    const { user, loading: authLoading } = useAuth();
    const [activeTab, setActiveTab] = useState('equipos'); // equipos | jugadores | auditoria | partidos | sistema
    const [activeSystemTab, setActiveSystemTab] = useState('general'); // general | config | peligro
    const [equipos, setEquipos] = useState([]);
    const [jugadores, setJugadores] = useState([]);
    const [auditoriaLogs, setAuditoriaLogs] = useState([]);
    const [partidosPendientes, setPartidosPendientes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [saving, setSaving] = useState(null);

    // Modales
    const [isStatsModalOpen, setIsStatsModalOpen] = useState(false);
    const [isCreatePartidoModalOpen, setIsCreatePartidoModalOpen] = useState(false);
    const [isReporteModalOpen, setIsReporteModalOpen] = useState(false);
    const [selectedJugador, setSelectedJugador] = useState(null);
    const [selectedPartido, setSelectedPartido] = useState(null);

    // Estados controlados
    const [presupuestos, setPresupuestos] = useState({});
    const [preciosJugadores, setPreciosJugadores] = useState({});

    // Clasificación
    const [puntuacion, setPuntuacion] = useState({ pts_victoria: 3, pts_empate: 1, pts_derrota: 0 });
    const [resultadoForm, setResultadoForm] = useState({ equipo_local: '', equipo_visitante: '', goles_local: 0, goles_visitante: 0 });
    const [walkoverForm, setWalkoverForm] = useState({ ganador: '', perdedor: '' });

    // Liga Automation
    const [estadoLiga, setEstadoLiga] = useState(null);
    const [calendarioForm, setCalendarioForm] = useState({
        dias_entre_jornadas: 3,
        fecha_inicio: '',
        hora_default: '20:00',
        playoffs_habilitados: true,
        clasificados_playoffs: 4
    });

    // System Status
    const [systemStatus, setSystemStatus] = useState(null);

    // Formulario Megáfono
    const [anuncioForm, setAnuncioForm] = useState({
        titulo: '',
        mensaje: '',
        imagen_url: '',
        color: '#9b59b6',
        canal_destino: 'anuncios'
    });

    // New Modal States
    const [isExpressModalOpen, setIsExpressModalOpen] = useState(false);
    const [isWalkoverModalOpen, setIsWalkoverModalOpen] = useState(false);
    const [isPuntosModalOpen, setIsPuntosModalOpen] = useState(false);
    const [isDangerZoneOpen, setIsDangerZoneOpen] = useState(false);

    // Global Config State
    const [globalConfig, setGlobalConfig] = useState(null);
    const [loadingConfig, setLoadingConfig] = useState(true);

    useEffect(() => {
        if (user?.admin) {
            loadData();
        }
    }, [user]);

    const loadData = async () => {
        setLoading(true);
        try {
            const eqs = await ligaService.getEquipos();
            setEquipos(eqs);

            const presupuestosInit = {};
            eqs.forEach(eq => {
                const id = eq.role_id || eq.nombre;
                presupuestosInit[id] = eq.presupuesto || 100000000;
            });
            setPresupuestos(presupuestosInit);

            const jugsData = await ligaService.getJugadores('todos');
            const listaJugadores = Array.isArray(jugsData) ? jugsData : (jugsData.jugadores || []);
            setJugadores(listaJugadores);

            const preciosInit = {};
            listaJugadores.forEach(p => {
                preciosInit[p.discord_id] = {
                    precio: p.precio || 0,
                    clausula: p.clausula || 0
                };
            });
            setPreciosJugadores(preciosInit);

            const logsData = await ligaService.getAuditoria();
            setAuditoriaLogs(logsData.logs || []);

            const pendientesData = await ligaService.getPartidos('pendiente');
            setPartidosPendientes(pendientesData || []);

            try {
                const puntData = await ligaService.getPuntuacion();
                setPuntuacion(puntData);
            } catch (e) { /* puntuacion no cargada, usa defaults */ }

            try {
                const estadoData = await ligaService.getEstadoLiga();
                setEstadoLiga(estadoData);
            } catch (e) { /* estado liga no cargado */ }

            try {
                const sysStatus = await ligaService.getSystemStatus();
                setSystemStatus(sysStatus);
            } catch (e) { /* system status no cargado */ }

            try {
                const gConfig = await ligaService.getGlobalConfig();
                setGlobalConfig(gConfig);
                setLoadingConfig(false);
            } catch (e) { console.error("Error loading global config"); setLoadingConfig(false); }

        } catch (error) {
            console.error("Error loading admin data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handlePresupuestoChange = (equipoId, valor) => {
        setPresupuestos(prev => ({ ...prev, [equipoId]: valor }));
    };

    const handlePrecioJugadorChange = (discordId, campo, valor) => {
        setPreciosJugadores(prev => ({
            ...prev,
            [discordId]: {
                ...prev[discordId],
                [campo]: valor
            }
        }));
    };

    const handleUpdatePresupuesto = async (equipoId) => {
        setSaving(equipoId);
        try {
            const nuevoPresupuesto = presupuestos[equipoId];
            await ligaService.updatePresupuesto(equipoId, parseInt(nuevoPresupuesto));
            setEquipos(prev => prev.map(eq =>
                (eq.role_id === equipoId || eq.nombre === equipoId) ? { ...eq, presupuesto: nuevoPresupuesto } : eq
            ));

            // Recargar logs para ver la auditoría nueva enseguida
            const logsData = await ligaService.getAuditoria();
            setAuditoriaLogs(logsData.logs || []);

        } catch (error) {
            console.error("Error updating budget:", error);
            alert("Error al guardar.");
        } finally {
            setSaving(null);
        }
    };

    const handleUpdatePrecio = async (discordId) => {
        setSaving(discordId);
        try {
            const { precio, clausula } = preciosJugadores[discordId];
            await ligaService.updatePrecioJugador(discordId, parseInt(precio), parseInt(clausula));
            setJugadores(prev => prev.map(p =>
                p.discord_id === discordId ? { ...p, precio: precio, clausula: clausula } : p
            ));
        } catch (error) {
            console.error("Error updating player:", error);
            alert("Error al guardar jugador.");
        } finally {
            setSaving(null);
        }
    };

    const handleRegistrarResultado = async (partidoId, reporteData) => {
        try {
            await ligaService.reportarResultadoDirecto(partidoId, reporteData);
            setPartidosPendientes(prev => prev.filter(p => p._id !== partidoId));
            alert("🏆 Resultado publicado. Tabla Actualizada Oficialmente.");
        } catch (error) {
            console.error(error);
            alert("Error al reportar el resultado.");
            throw error; // Propaga error al modal para deshabilitar loading
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

    const formatMoney = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        }).format(amount);
    };

    const filteredJugadores = jugadores.filter(j =>
        j.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (j.equipo && j.equipo.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // --- Clasificación Handlers ---
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

    // --- Liga Automation Handlers ---
    const handleGenerarCalendario = async () => {
        const { dias_entre_jornadas, fecha_inicio, hora_default, playoffs_habilitados, clasificados_playoffs } = calendarioForm;

        if (!fecha_inicio) {
            alert("❌ Debes seleccionar una fecha de inicio.");
            return;
        }

        if (!window.confirm(`¿Generar calendario completo?\n\n• ${equipos.length} equipos\n• Todos contra todos\n• ${dias_entre_jornadas} días entre jornadas\n• Playoffs: ${playoffs_habilitados ? 'Sí' : 'No'}`)) return;

        setSaving('calendario');
        try {
            const res = await ligaService.generarCalendarioLiga(
                dias_entre_jornadas,
                fecha_inicio,
                hora_default,
                playoffs_habilitados,
                clasificados_playoffs
            );
            alert(`✅ ${res.message}\n📊 ${res.equipos} equipos, ${res.jornadas} jornadas, ${res.partidos_creados} partidos creados`);

            // Reload data
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

            // Reload data
            await loadData();
        } catch (e) {
            alert("❌ Error al generar playoffs.");
            console.error(e);
        }
        finally { setSaving(null); }
    };

    const handleEliminarPartido = async (partidoId) => {
        if (!window.confirm("¿Estás seguro de que quieres eliminar este partido?\n\nEsta acción no se puede deshacer.")) return;

        try {
            await ligaService.eliminarPartido(partidoId);
            alert("✅ Partido eliminado correctamente");

            // Reload data
            await loadData();
        } catch (e) {
            alert("❌ Error al eliminar partido.");
            console.error(e);
        }
    };

    // --- System actions ---
    const handlePM2Action = async (action) => {
        const actionText = action === 'restart' ? 'Reinicio' : 'Detención';
        if (!window.confirm(`⚠️ ESTÁS A PUNTO DE EJECUTAR UN COMANDO DE SERVIDOR.\n\n¿Deseas enviar un 'PM2 ${action.toUpperCase()}' al bot de Discord?`)) return;

        setSaving(`pm2-${action}`);
        try {
            const res = await ligaService.executePM2Action(action);
            if (res.simulated) {
                alert(`ℹ️ Simulación (No estás en VPS):\n\n${res.message}`);
            } else {
                alert(`✅ ${res.message}`);
            }
            // Refrescar el estado de la API UI tras 5 segundos si fue reinicio
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

    // --- Funciones Peligrosas / Maintenance ---

    const handleBackup = async () => {
        if (!window.confirm("💾 ¿Deseas descargar un volcado completo de la base de datos en JSON localmente?")) return;
        setSaving('backup');
        try {
            const data = await ligaService.generateBackup();

            // Lógica para descargar archivo Blob desde Axios en el navegador
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
            // Recargar panel
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
            // Pánico en UI, redirigir o recargar forzosamente
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

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-dark-950 flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="animate-spin w-10 h-10 text-gold-500 mx-auto mb-4" />
                    <p className="text-gray-400 text-sm">Cargando panel...</p>
                </div>
            </div>
        );
    }

    if (!user || !user.admin) {
        return (
            <div className="min-h-screen bg-dark-950 flex flex-col items-center justify-center text-center px-6">
                <div className="w-20 h-20 rounded-2xl bg-red-500/5 border border-red-500/10 flex items-center justify-center mb-8">
                    <ShieldAlert className="w-10 h-10 text-red-400" />
                </div>
                <h1 className="text-5xl font-light text-white mb-4">Acceso Restringido</h1>
                <p className="text-gray-500 text-lg max-w-lg mb-8 leading-relaxed">
                    Esta área está reservada para administradores de la liga.
                </p>
                <a href="/" className="inline-flex items-center gap-3 px-8 py-4 bg-gold-500/10 border border-gold-500/20 text-gold-400 rounded-2xl hover:bg-gold-500/20 transition-all">
                    <ShieldAlert size={20} />
                    Volver al Portal
                </a>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-950">
            <div className="max-w-7xl mx-auto px-8 py-12">
                {/* Header */}
                <div className="flex justify-between items-end mb-12 pb-8 border-b border-white/5">
                    <div>
                        <h1 className="text-6xl font-light text-white tracking-tight mb-2">
                            Administración
                        </h1>
                        <p className="text-gray-500 text-lg">
                            Gestión centralizada de la liga
                        </p>
                    </div>
                    <button
                        onClick={loadData}
                        className="px-6 py-3 bg-white/5 border border-white/10 text-gray-300 rounded-xl hover:bg-white/10 hover:text-white transition-all flex items-center gap-3"
                    >
                        <RefreshCw size={18} className="text-gray-400" />
                        <span className="text-sm">Actualizar</span>
                    </button>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex gap-1 mb-12 p-1 bg-white/5 rounded-2xl w-fit">
                <button
                    onClick={() => setActiveTab('equipos')}
                    className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === 'equipos'
                        ? 'bg-white text-black shadow-lg'
                        : 'text-gray-400 hover:text-white'
                        }`}
                >
                    <Shield size={20} className={activeTab === 'equipos' ? 'text-black' : ''} />
                    <span>Equipos</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${activeTab === 'equipos' ? 'bg-black/10 text-black' : 'bg-white/10 text-gray-400'}`}>
                        {equipos.length}
                    </span>
                </button>
                <button
                    onClick={() => setActiveTab('jugadores')}
                    className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === 'jugadores'
                        ? 'bg-white text-black shadow-lg'
                        : 'text-gray-400 hover:text-white'
                        }`}
                >
                    <Users size={20} className={activeTab === 'jugadores' ? 'text-black' : ''} />
                    <span>Jugadores</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${activeTab === 'jugadores' ? 'bg-black/10 text-black' : 'bg-white/10 text-gray-400'}`}>
                        {jugadores.length}
                    </span>
                </button>
                <button
                    onClick={() => setActiveTab('auditoria')}
                    className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === 'auditoria'
                        ? 'bg-white text-black shadow-lg'
                        : 'text-gray-400 hover:text-white'
                        }`}
                >
                    <FileText size={20} className={activeTab === 'auditoria' ? 'text-black' : ''} />
                    <span>Auditoría</span>
                </button>
                <button
                    onClick={() => setActiveTab('partidos')}
                    className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === 'partidos'
                        ? 'bg-white text-black shadow-lg'
                        : 'text-gray-400 hover:text-white'
                        }`}
                >
                    <Trophy size={20} className={activeTab === 'partidos' ? 'text-black' : ''} />
                    <span>Liga</span>
                </button>
                <button
                    onClick={() => setActiveTab('sistema')}
                    className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === 'sistema'
                        ? 'bg-gold-500 text-black shadow-lg shadow-gold-500/20'
                        : 'text-gray-400 hover:text-white'
                        }`}
                >
                    <Settings size={20} className={activeTab === 'sistema' ? 'text-black' : ''} />
                    <span>Sistema</span>
                </button>
            </div>

            {/* Content Tab: Equipos */}
            {activeTab === 'equipos' && (
                <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                    <div className="p-6 border-b border-white/10">
                        <h2 className="text-xl font-light text-white">Gestión de Equipos</h2>
                        <p className="text-gray-500 text-sm mt-1">Administra presupuestos y plantillas</p>
                    </div>
                    <div className="divide-y divide-white/5">
                        {equipos.map(eq => {
                            const equipoId = eq.role_id || eq.nombre;
                            return (
                                <div key={equipoId} className="p-6 hover:bg-white/5 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                                                <Shield size={24} className="text-gray-400" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-medium text-white">{eq.nombre}</h3>
                                                <p className="text-gray-500 text-sm">{eq.plantilla?.length || 0} jugadores</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="flex items-center gap-2 bg-black/20 px-4 py-2 rounded-xl">
                                                <DollarSign size={16} className="text-gold-400" />
                                                <input
                                                    type="number"
                                                    value={presupuestos[equipoId] ?? ''}
                                                    onChange={(e) => handlePresupuestoChange(equipoId, e.target.value)}
                                                    className="bg-transparent border-none text-gold-400 font-mono font-bold w-32 focus:outline-none text-right"
                                                    placeholder="0"
                                                />
                                            </div>
                                            <button
                                                onClick={() => handleUpdatePresupuesto(equipoId)}
                                                disabled={saving === equipoId}
                                                className="px-6 py-2 bg-white text-black rounded-xl hover:bg-gray-200 disabled:opacity-50 transition-all font-medium text-sm"
                                            >
                                                {saving === equipoId ? '...' : 'Actualizar'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Content Tab: Jugadores */}
            {activeTab === 'jugadores' && (
                <div className="space-y-6">
                    {/* Search */}
                    <div className="relative max-w-lg">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                        <input
                            type="text"
                            placeholder="Buscar jugador..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:border-white/20 focus:outline-none placeholder-gray-500"
                        />
                    </div>

                    {/* Players Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredJugadores.slice(0, 50).map(p => (
                            <div key={p.discord_id} className={`bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all ${p.baneado ? 'opacity-50' : ''}`}>
                                <div className="flex items-start gap-4">
                                    <img src={p.avatar_url || "https://cdn.discordapp.com/embed/avatars/0.png"} alt="" className="w-14 h-14 rounded-xl bg-black/50 border border-white/10" />
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-medium text-white">{p.nombre}</h3>
                                            {p.baneado && <AlertTriangle size={14} className="text-red-400" />}
                                        </div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className="text-xs text-gray-500">{p.posicion || 'N/A'}</span>
                                            {p.equipo && (
                                                <span className="text-xs px-2 py-1 bg-white/10 rounded-full text-gray-300">
                                                    {p.equipo}
                                                </span>
                                            )}
                                            {!p.equipo && (
                                                <span className="text-xs px-2 py-1 bg-red-500/10 rounded-full text-red-400">
                                                    Libre
                                                </span>
                                            )}
                                        </div>

                                        <div className="space-y-3">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-gray-500 w-16">Precio</span>
                                                <input
                                                    type="number"
                                                    value={preciosJugadores[p.discord_id]?.precio ?? 0}
                                                    onChange={(e) => handlePrecioJugadorChange(p.discord_id, 'precio', e.target.value)}
                                                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-right text-gray-300 font-mono text-sm focus:border-white/20 focus:outline-none"
                                                />
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-gray-500 w-16">Cláusula</span>
                                                <input
                                                    type="number"
                                                    value={preciosJugadores[p.discord_id]?.clausula ?? 0}
                                                    onChange={(e) => handlePrecioJugadorChange(p.discord_id, 'clausula', e.target.value)}
                                                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-right text-red-400 font-mono text-sm focus:border-white/20 focus:outline-none"
                                                />
                                            </div>
                                        </div>

                                        <div className="flex gap-2 mt-4">
                                            <button
                                                onClick={() => handleUpdatePrecio(p.discord_id)}
                                                disabled={saving === p.discord_id}
                                                className="flex-1 px-3 py-2 bg-white text-black rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-all font-medium text-xs"
                                            >
                                                {saving === p.discord_id ? '...' : 'Guardar'}
                                            </button>
                                            <button
                                                onClick={() => openEditStats(p)}
                                                className="px-3 py-2 bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 hover:text-white transition-all"
                                            >
                                                <Edit3 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {filteredJugadores.length > 50 && (
                        <div className="text-center text-gray-500 text-sm">
                            Mostrando primeros 50 de {filteredJugadores.length} jugadores
                        </div>
                    )}
                </div>
            )}

            {/* Content Tab: Auditoria */}
            {activeTab === 'auditoria' && (
                <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                    <div className="p-6 border-b border-white/10">
                        <h2 className="text-xl font-light text-white">Auditoría Financiera</h2>
                        <p className="text-gray-500 text-sm mt-1">Historial de transacciones y movimientos</p>
                    </div>
                    {auditoriaLogs.length === 0 ? (
                        <div className="p-16 text-center">
                            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-6">
                                <FileText size={32} className="text-gray-400" />
                            </div>
                            <p className="text-gray-500">No hay registros financieros</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-white/5">
                            {auditoriaLogs.map((log, index) => {
                                const fecha = new Date(log.timestamp).toLocaleString();
                                const esTransferencia = log.tipo === "TRANSFERENCIA";
                                return (
                                    <div key={log.id || index} className="p-6 hover:bg-white/5 transition-colors">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-4">
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${esTransferencia ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                                                    {esTransferencia ? <ArrowRightLeft size={20} /> : <Settings size={20} />}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${esTransferencia ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                                                            {log.tipo}
                                                        </span>
                                                        <span className="text-gray-500 text-sm">{fecha}</span>
                                                    </div>
                                                    <p className="text-white font-medium">{log.actor}</p>
                                                    <p className="text-gray-400 text-sm mt-1 line-clamp-2">{log.detalles}</p>
                                                </div>
                                            </div>
                                            <div className={`text-right font-mono font-bold ${esTransferencia ? 'text-blue-400' : 'text-green-400'}`}>
                                                {formatMoney(log.monto)}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* Content Tab: Partidos & Liga */}
            {activeTab === 'partidos' && (
                <div className="max-w-7xl mx-auto space-y-8">
                    {/* Header */}
                    <div className="flex justify-between items-end pb-6 border-b border-white/10">
                        <div>
                            <h2 className="text-3xl font-light text-white flex items-center gap-3">
                                <span>Dashboard de Liga</span>
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-gold-500/10 text-gold-400 border border-gold-500/20 uppercase">Live</span>
                            </h2>
                            <p className="text-gray-500 mt-1">Gestión deportiva y operativa en tiempo real</p>
                        </div>
                        <button
                            onClick={() => setIsCreatePartidoModalOpen(true)}
                            className="group relative px-6 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black rounded-xl hover:from-gold-400 hover:to-gold-500 transition-all font-bold flex items-center gap-3 shadow-[0_0_20px_rgba(234,179,8,0.2)] hover:shadow-[0_0_30px_rgba(234,179,8,0.4)] hover:-translate-y-0.5 overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out"></div>
                            <Calendar size={20} className="relative z-10" />
                            <span className="relative z-10">Programar Partido</span>
                        </button>
                    </div>

                    {/* Layout Principal - Grid 2 Columnas */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                        {/* Columna Principal (8/12) */}
                        <div className="lg:col-span-8 space-y-6">

                            {/* Hero Stats - Bento Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {/* Progreso de la Liga */}
                                <div className="group relative bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.05] hover:border-gold-500/30 transition-all duration-300 overflow-hidden">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-gold-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-gold-500/20 transition-all"></div>
                                    <div className="flex items-center gap-3 mb-4 relative z-10">
                                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-500/20 to-gold-500/5 border border-gold-500/30 flex items-center justify-center shadow-inner">
                                            <Trophy size={18} className="text-gold-400 drop-shadow-md" />
                                        </div>
                                        <div>
                                            <h3 className="text-white text-sm font-semibold tracking-wide">Progreso</h3>
                                            <p className="text-gray-500 text-xs uppercase tracking-wider">Temporada actual</p>
                                        </div>
                                    </div>
                                    <div className="mt-2 relative z-10">
                                        <div className="flex items-baseline gap-2 mb-1">
                                            <span className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-yellow-200">{estadoLiga?.porcentaje_completado || 0}%</span>
                                        </div>
                                        <div className="w-full bg-black/40 rounded-full h-1.5 mt-3 mb-2 overflow-hidden border border-white/5">
                                            <div
                                                className="bg-gradient-to-r from-gold-600 via-gold-400 to-yellow-300 h-1.5 rounded-full transition-all duration-1000 relative"
                                                style={{ width: `${estadoLiga?.porcentaje_completado || 0}%` }}
                                            >
                                                <div className="absolute inset-0 bg-white/30 animate-[shimmer_2s_infinite]"></div>
                                            </div>
                                        </div>
                                        <p className="text-gray-400 text-xs font-medium">{estadoLiga?.partidos_jugados || 0} jugados de {estadoLiga?.partidos_total || 0} totales</p>
                                    </div>
                                </div>

                                {/* Próximos Encuentros */}
                                <div className="group relative bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.05] hover:border-blue-500/30 transition-all duration-300 overflow-hidden">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-blue-500/20 transition-all"></div>
                                    <div className="flex items-center gap-3 mb-4 relative z-10">
                                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-500/5 border border-blue-500/30 flex items-center justify-center shadow-inner">
                                            <Calendar size={18} className="text-blue-400 drop-shadow-md" />
                                        </div>
                                        <div>
                                            <h3 className="text-white text-sm font-semibold tracking-wide">Pendientes</h3>
                                            <p className="text-gray-500 text-xs uppercase tracking-wider">Por jugar</p>
                                        </div>
                                    </div>
                                    <div className="mt-2 relative z-10">
                                        <div className="flex items-baseline gap-2 mb-1">
                                            <span className="text-4xl font-black text-white">{partidosPendientes.length}</span>
                                        </div>
                                        <p className="text-gray-400 text-xs font-medium mt-3">Partidos activos esperando resultado</p>
                                    </div>
                                </div>

                                {/* Estado Global */}
                                <div className="group relative bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.05] hover:border-green-500/30 transition-all duration-300 overflow-hidden">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-green-500/20 transition-all"></div>
                                    <div className="flex items-center gap-3 mb-4 relative z-10">
                                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-green-500/5 border border-green-500/30 flex items-center justify-center shadow-inner">
                                            <Activity size={18} className="text-green-400 drop-shadow-md" />
                                        </div>
                                        <div>
                                            <h3 className="text-white text-sm font-semibold tracking-wide">Sistema</h3>
                                            <p className="text-gray-500 text-xs uppercase tracking-wider">Estado de Liga</p>
                                        </div>
                                    </div>
                                    <div className="mt-2 relative z-10">
                                        <div className="inline-flex items-center gap-2 mb-1 px-3 py-1.5 rounded-lg bg-black/30 border border-white/5">
                                            <div className="relative flex h-3 w-3">
                                                {estadoLiga?.estado === 'en_curso' || estadoLiga?.estado === 'playoffs' ? (
                                                    <>
                                                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${estadoLiga?.estado === 'en_curso' ? 'bg-blue-400' : 'bg-purple-400'}`}></span>
                                                        <span className={`relative inline-flex rounded-full h-3 w-3 ${estadoLiga?.estado === 'en_curso' ? 'bg-blue-500' : 'bg-purple-500'}`}></span>
                                                    </>
                                                ) : (
                                                    <span className={`relative inline-flex rounded-full h-3 w-3 ${estadoLiga?.estado === 'finalizada' ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                                                )}
                                            </div>
                                            <span className="text-white text-sm tracking-wide font-bold uppercase">
                                                {estadoLiga?.estado === 'no_iniciada' ? 'No Iniciada' :
                                                    estadoLiga?.estado === 'en_curso' ? 'En Curso' :
                                                        estadoLiga?.estado === 'playoffs' ? 'Playoffs' :
                                                            estadoLiga?.estado === 'finalizada' ? 'Finalizada' : 'Desconocido'}
                                            </span>
                                        </div>
                                        <p className="text-gray-400 text-xs font-medium mt-3">
                                            {estadoLiga?.estado === 'en_curso' && equipos.length > 1 && `Próxima: Jornada ${Math.floor((estadoLiga.partidos_jugados || 0) / (equipos.length - 1)) + 1}`}
                                            {estadoLiga?.estado === 'playoffs' && 'Fase de eliminación directa'}
                                            {estadoLiga?.estado === 'finalizada' && 'Temporada concluida'}
                                            {estadoLiga?.estado === 'no_iniciada' && 'Esperando configuración del sorteo'}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Setup Wizard (solo si no hay temporada iniciada) */}
                            {(!estadoLiga || estadoLiga.estado === 'no_iniciada') && (
                                <div className="relative bg-[#0d1017] border border-gold-500/20 rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
                                    <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-transparent via-gold-500/50 to-transparent"></div>
                                    <div className="p-8 border-b border-white/5 bg-white/[0.02]">
                                        <div className="flex flex-col md:flex-row md:items-center gap-6">
                                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold-500/20 to-gold-500/5 border border-gold-500/30 flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(234,179,8,0.15)]">
                                                <Trophy size={32} className="text-gold-400 drop-shadow-md" />
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-light text-white mb-2">Asistente de Temporada</h3>
                                                <p className="text-gray-400 text-sm max-w-xl leading-relaxed">
                                                    Configura los parámetros para generar automáticamente el fixture completo,
                                                    fechas estimadas y el sistema de playoffs al finalizar la fase regular.
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-8">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 mb-8">
                                            {/* Step 1 */}
                                            <div className="space-y-3 bg-black/20 p-5 rounded-xl border border-white/5">
                                                <label className="flex items-center gap-2 text-sm font-semibold text-gray-200">
                                                    <div className="w-6 h-6 rounded-full bg-gold-500/20 text-gold-400 flex items-center justify-center text-xs">1</div>
                                                    Fecha de Apertura
                                                </label>
                                                <input
                                                    type="date"
                                                    value={calendarioForm.fecha_inicio}
                                                    onChange={(e) => setCalendarioForm({ ...calendarioForm, fecha_inicio: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg px-4 py-3 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 shadow-inner transition-all"
                                                />
                                            </div>

                                            {/* Step 2 */}
                                            <div className="space-y-3 bg-black/20 p-5 rounded-xl border border-white/5">
                                                <label className="flex items-center gap-2 text-sm font-semibold text-gray-200">
                                                    <div className="w-6 h-6 rounded-full bg-gold-500/20 text-gold-400 flex items-center justify-center text-xs">2</div>
                                                    Hora Predeterminada
                                                </label>
                                                <input
                                                    type="time"
                                                    value={calendarioForm.hora_default}
                                                    onChange={(e) => setCalendarioForm({ ...calendarioForm, hora_default: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg px-4 py-3 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 shadow-inner transition-all"
                                                />
                                            </div>

                                            {/* Step 3 */}
                                            <div className="space-y-3 bg-black/20 p-5 rounded-xl border border-white/5">
                                                <label className="flex items-center gap-2 text-sm font-semibold text-gray-200">
                                                    <div className="w-6 h-6 rounded-full bg-gold-500/20 text-gold-400 flex items-center justify-center text-xs">3</div>
                                                    Intervalo de Días
                                                </label>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    max="14"
                                                    value={calendarioForm.dias_entre_jornadas}
                                                    onChange={(e) => setCalendarioForm({ ...calendarioForm, dias_entre_jornadas: parseInt(e.target.value) || 3 })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg px-4 py-3 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 shadow-inner transition-all"
                                                    placeholder="Días entre jornadas"
                                                />
                                            </div>

                                            {/* Step 4 */}
                                            <div className="space-y-3 bg-black/20 p-5 rounded-xl border border-white/5">
                                                <label className="flex items-center gap-2 text-sm font-semibold text-gray-200">
                                                    <div className="w-6 h-6 rounded-full bg-gold-500/20 text-gold-400 flex items-center justify-center text-xs">4</div>
                                                    Formato Semifinal / Final
                                                </label>
                                                <select
                                                    value={calendarioForm.clasificados_playoffs}
                                                    onChange={(e) => setCalendarioForm({ ...calendarioForm, clasificados_playoffs: parseInt(e.target.value) })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg px-4 py-3 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 shadow-inner transition-all appearance-none"
                                                    style={{ backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center', backgroundSize: '1em' }}
                                                >
                                                    <option value={2}>🥇 Clasifican Top 2 (Pase directo a Final)</option>
                                                    <option value={4}>🏆 Clasifican Top 4 (Semifinales)</option>
                                                    <option value={8}>🎯 Clasifican Top 8 (Cuartos de final)</option>
                                                </select>
                                                <div className="flex items-center pt-2">
                                                    <label className="relative inline-flex items-center cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            className="sr-only peer"
                                                            checked={calendarioForm.playoffs_habilitados}
                                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, playoffs_habilitados: e.target.checked })}
                                                        />
                                                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gold-500"></div>
                                                        <span className="ml-3 text-sm font-medium text-gray-300">Activar Playoffs al culminar</span>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>

                                        <button
                                            onClick={handleGenerarCalendario}
                                            disabled={saving === 'calendario'}
                                            className="w-full relative group overflow-hidden px-6 py-4 bg-gradient-to-r from-gold-500 to-yellow-400 text-black rounded-xl hover:from-gold-400 hover:to-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-lg shadow-[0_0_20px_rgba(234,179,8,0.3)] hover:shadow-[0_0_30px_rgba(234,179,8,0.5)] transform hover:-translate-y-0.5"
                                        >
                                            <div className="absolute inset-0 w-full h-full bg-white/20 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
                                            <span className="relative z-10 flex items-center justify-center gap-2">
                                                {saving === 'calendario' ? (
                                                    <><RefreshCw size={20} className="animate-spin" /> Procesando Sorteo...</>
                                                ) : (
                                                    <><Trophy size={20} /> INICIAR TEMPORADA CON {equipos.length} EQUIPOS</>
                                                )}
                                            </span>
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Marcadores Activos - Match Cards (siempre visible si hay partidos) */}
                            {partidosPendientes.length > 0 && (
                                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                                    <div className="p-4 border-b border-white/10">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                                    <Gavel size={20} className="text-blue-400" />
                                                </div>
                                                <div>
                                                    <h3 className="text-base font-medium text-white">Marcadores Activos</h3>
                                                    <p className="text-gray-500 text-xs">Partidos por registrar</p>
                                                </div>
                                            </div>
                                            <div className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
                                                <span className="text-blue-400 text-xs font-medium">{partidosPendientes.length}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                                            {partidosPendientes.map((p) => {
                                                const fechaProg = p.fecha_hora ? new Date(p.fecha_hora).toLocaleString('es', {
                                                    day: '2-digit',
                                                    month: '2-digit',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                }) : 'Por definir';
                                                return (
                                                    <div
                                                        key={p._id}
                                                        className="group bg-gradient-to-r from-white/5 to-white/[0.02] border border-white/10 rounded-lg p-4 hover:border-gold-500/30 hover:from-gold-500/5 hover:to-gold-500/[0.02] transition-all duration-300 cursor-pointer"
                                                        onClick={() => { setSelectedPartido(p); setIsReporteModalOpen(true); }}
                                                    >
                                                        {/* TV Style Scoreboard */}
                                                        <div className="bg-black/40 rounded-lg p-3 mb-3">
                                                            <div className="flex items-center justify-between">
                                                                <div className="flex-1 text-center">
                                                                    <div className="text-white font-bold text-sm truncate">{p.equipo_local}</div>
                                                                </div>
                                                                <div className="px-3 text-center">
                                                                    <div className="text-gold-400 font-black text-lg">VS</div>
                                                                    <div className="text-gray-500 text-xs">
                                                                        {p.jornada ? `J${p.jornada}` : p.fase}
                                                                    </div>
                                                                </div>
                                                                <div className="flex-1 text-center">
                                                                    <div className="text-white font-bold text-sm truncate">{p.equipo_visitante}</div>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2">
                                                                <div className="flex items-center gap-1 text-gray-500 text-xs">
                                                                    <Calendar size={12} />
                                                                    <span>{fechaProg}</span>
                                                                </div>
                                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${p.fase === 'LIGA' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                                                                    'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                                                                    }`}>
                                                                    {p.fase}
                                                                </span>
                                                            </div>

                                                            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center gap-2">
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setSelectedPartido(p);
                                                                        setIsReporteModalOpen(true);
                                                                    }}
                                                                    className="px-3 py-1 bg-green-500 text-black rounded-lg hover:bg-green-400 transition-all font-medium text-xs shadow-lg shadow-green-500/20"
                                                                >
                                                                    <Edit size={12} className="inline mr-1" />
                                                                    Registrar
                                                                </button>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleEliminarPartido(p._id);
                                                                    }}
                                                                    className="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all font-medium text-xs shadow-lg shadow-red-500/20"
                                                                >
                                                                    <Trash2 size={12} className="inline mr-1" />
                                                                    Eliminar
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Mensaje si no hay partidos */}
                            {partidosPendientes.length === 0 && (!estadoLiga || estadoLiga.estado === 'no_iniciada') && (
                                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                                    <div className="p-8 text-center">
                                        <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                                            <Calendar size={24} className="text-gray-400" />
                                        </div>
                                        <p className="text-gray-500">No hay partidos programados</p>
                                        <p className="text-gray-600 text-sm mt-2">Usa el Asistente de Configuración para crear una temporada</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Columna de Control (4/12) */}
                        <div className="lg:col-span-4 space-y-4">

                            {/* Panel de Control */}
                            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                                <div className="p-4 border-b border-white/10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-gold-500/10 border border-gold-500/20 flex items-center justify-center">
                                            <Settings size={16} className="text-gold-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-medium text-white">Panel de Control</h3>
                                            <p className="text-gray-500 text-xs">Acciones rápidas</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-4 space-y-3">
                                    {/* Estado de Liga */}
                                    {estadoLiga && estadoLiga.estado !== 'no_iniciada' && (
                                        <div className="bg-black/20 rounded-lg p-3">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-white text-sm font-medium">Temporada Activa</span>
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${estadoLiga.estado === 'en_curso' ? 'bg-blue-500/10 text-blue-400' :
                                                    estadoLiga.estado === 'playoffs' ? 'bg-purple-500/10 text-purple-400' :
                                                        'bg-green-500/10 text-green-400'
                                                    }`}>
                                                    {estadoLiga.estado === 'en_curso' ? 'En Curso' :
                                                        estadoLiga.estado === 'playoffs' ? 'Playoffs' : 'Finalizada'}
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2 text-center">
                                                <div>
                                                    <div className="text-lg font-bold text-white">{estadoLiga.partidos_jugados}</div>
                                                    <div className="text-gray-500 text-xs">Jugados</div>
                                                </div>
                                                <div>
                                                    <div className="text-lg font-bold text-gold-400">{estadoLiga.porcentaje_completado}%</div>
                                                    <div className="text-gray-500 text-xs">Progreso</div>
                                                </div>
                                            </div>
                                            <div className="w-full bg-black/40 rounded-full h-1.5 mt-2">
                                                <div
                                                    className="bg-gradient-to-r from-gold-500 to-gold-400 h-1.5 rounded-full transition-all duration-1000"
                                                    style={{ width: `${estadoLiga.porcentaje_completado}%` }}
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {/* Botones de Acciones Rápidas */}
                                    <button
                                        onClick={() => setIsExpressModalOpen(true)}
                                        className="w-full px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 text-black rounded-lg hover:from-green-400 hover:to-green-500 transition-all font-medium flex items-center justify-center gap-2 shadow-lg shadow-green-500/20"
                                    >
                                        <Activity size={16} />
                                        <span>Registrar Manual</span>
                                    </button>

                                    <button
                                        onClick={() => setIsWalkoverModalOpen(true)}
                                        className="w-full px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition-all font-medium flex items-center justify-center gap-2 shadow-lg shadow-red-500/20"
                                    >
                                        <Ban size={16} />
                                        <span>Dictar Walkover</span>
                                    </button>

                                    <button
                                        onClick={() => setIsPuntosModalOpen(true)}
                                        className="w-full px-4 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black rounded-lg hover:from-gold-400 hover:to-gold-500 transition-all font-medium flex items-center justify-center gap-2 shadow-lg shadow-gold-500/20"
                                    >
                                        <Settings size={16} />
                                        <span>Ajustes de Puntos</span>
                                    </button>

                                    {/* Herramientas Avanzadas */}
                                    <button
                                        onClick={() => setIsDangerZoneOpen(!isDangerZoneOpen)}
                                        className="w-full px-4 py-3 bg-white/5 border border-red-500/20 text-red-400 rounded-lg hover:bg-red-500/5 transition-all font-medium flex items-center justify-center gap-2"
                                    >
                                        <AlertTriangle size={16} />
                                        <span>Herramientas Avanzadas</span>
                                        <ChevronDown size={16} className={`transition-transform ${isDangerZoneOpen ? 'rotate-180' : ''}`} />
                                    </button>

                                    {/* Danger Zone Colapsable */}
                                    {isDangerZoneOpen && (
                                        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 space-y-2">
                                            <div className="flex items-start gap-2">
                                                <AlertTriangle size={14} className="text-red-400 mt-0.5" />
                                                <div>
                                                    <h4 className="text-red-400 text-xs font-medium mb-1">⚠️ Precaución</h4>
                                                    <p className="text-gray-400 text-xs">
                                                        Operaciones críticas del sistema
                                                    </p>
                                                </div>
                                            </div>

                                            <button onClick={handleRecalcularTabla} disabled={saving === 'recalcular'}
                                                className="w-full p-2 bg-white/5 border border-blue-500/20 rounded hover:bg-blue-500/5 transition-all text-left group disabled:opacity-50 text-sm">
                                                <div className="flex items-center gap-2">
                                                    <RotateCcw size={14} className="text-blue-400" />
                                                    <span className="text-white">{saving === 'recalcular' ? 'Recalculando...' : 'Recalcular Tabla'}</span>
                                                </div>
                                            </button>

                                            <button onClick={handleResetearTabla} disabled={saving === 'resetear'}
                                                className="w-full p-2 bg-red-500/5 border border-red-500/20 rounded hover:bg-red-500/10 transition-all text-left group disabled:opacity-50 text-sm">
                                                <div className="flex items-center gap-2">
                                                    <Trash2 size={14} className="text-red-400" />
                                                    <span className="text-white">{saving === 'resetear' ? 'Borrando...' : 'Resetear Tabla'}</span>
                                                </div>
                                            </button>
                                        </div>
                                    )}

                                    {/* Botón de Playoffs */}
                                    {estadoLiga?.playoffs_listos && (
                                        <button
                                            onClick={handleGenerarPlayoffs}
                                            disabled={saving === 'playoffs'}
                                            className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 transition-all font-medium flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20"
                                        >
                                            <Trophy size={16} />
                                            <span>{saving === 'playoffs' ? 'Generando...' : '🏆 Generar Playoffs'}</span>
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Content Tab: Sistema */}
            {activeTab === 'sistema' && (
                <div className="space-y-6">
                    {/* Header Pestaña */}
                    <div className="flex justify-between items-end pb-6 border-b border-white/10">
                        <div>
                            <h2 className="text-3xl font-light text-white">Centro de Sistema</h2>
                            <p className="text-gray-500 mt-1">Supervisión del Bot, Ajustes Globales y Mantenimiento Avanzado</p>
                        </div>
                    </div>

                    {/* Sub-Tabs Sistema Minimalista */}
                    <div className="flex bg-[#0d1017] p-1.5 rounded-2xl border border-white/5 mx-auto max-w-2xl mb-8">
                        <button
                            onClick={() => setActiveSystemTab('general')}
                            className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all ${activeSystemTab === 'general' ? 'bg-blue-500/20 text-blue-400 shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                        >
                            Control y Anuncios
                        </button>
                        <button
                            onClick={() => setActiveSystemTab('config')}
                            className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all ${activeSystemTab === 'config' ? 'bg-gold-500/20 text-gold-400 shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                        >
                            Ajustes Globales
                        </button>
                        <button
                            onClick={() => setActiveSystemTab('peligro')}
                            className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2 ${activeSystemTab === 'peligro' ? 'bg-red-500/20 text-red-500 shadow-lg' : 'text-red-500/50 hover:text-red-400 hover:bg-white/5'}`}
                        >
                            <AlertTriangle size={16} /> Zona Precaución
                        </button>
                    </div>

                    <div className="max-w-4xl mx-auto">

                        {/* 1. TAB GENERAL (Estado del Bot y Megáfono) */}
                        {activeSystemTab === 'general' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Bloque 1: Control del Bot */}
                                <div className="space-y-6">
                                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                                        <div className="p-5 border-b border-white/10 flex justify-between items-center">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                                    <Activity size={20} className="text-blue-400" />
                                                </div>
                                                <div>
                                                    <h3 className="text-lg font-medium text-white">Estado del Bot</h3>
                                                    <p className="text-gray-500 text-xs">Monitoreo y comandos en vivo</p>
                                                </div>
                                            </div>
                                            <span className={`px-3 py-1 border text-xs font-bold rounded-full flex items-center gap-2 uppercase tracking-widest ${systemStatus?.bot_status === 'Online'
                                                ? 'bg-green-500/10 border-green-500/30 text-green-400'
                                                : 'bg-red-500/10 border-red-500/30 text-red-400'
                                                }`}>
                                                <span className={`w-2 h-2 rounded-full ${systemStatus?.bot_status === 'Online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                                                {systemStatus?.bot_status || 'Cargando...'}
                                            </span>
                                        </div>
                                        <div className="p-6">
                                            <div className="grid grid-cols-2 pb-6 gap-4">
                                                <div className="bg-black/20 p-4 rounded-xl border border-white/5 text-center">
                                                    <p className="text-gray-500 text-xs uppercase mb-1">Uptime</p>
                                                    <p className="text-white font-bold text-lg">{systemStatus?.bot_uptime || '--'}</p>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl border border-white/5 text-center">
                                                    <p className="text-gray-500 text-xs uppercase mb-1">Latencia (Ping)</p>
                                                    <p className="text-green-400 font-bold text-lg">{systemStatus?.bot_latency || 0}ms</p>
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <button
                                                    onClick={handleSyncCommands}
                                                    disabled={saving === 'sync-cmds'}
                                                    className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors group disabled:opacity-50"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <RefreshCw size={18} className={`text-blue-400 transition-transform duration-500 ${saving === 'sync-cmds' ? 'animate-spin' : 'group-hover:rotate-180'}`} />
                                                        <span className="text-sm text-gray-200">{saving === 'sync-cmds' ? 'Solicitando...' : 'Forzar Sincronización de Comandos (Slash)'}</span>
                                                    </div>
                                                    <ChevronDown size={16} className="text-gray-500 -rotate-90" />
                                                </button>
                                                <button
                                                    onClick={() => handlePM2Action('stop')}
                                                    disabled={saving === 'pm2-stop'}
                                                    className="w-full flex items-center justify-between p-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg transition-colors group text-red-400 disabled:opacity-50"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Ban size={18} className="group-hover:scale-110 transition-transform duration-500" />
                                                        <span className="text-sm font-medium">{saving === 'pm2-stop' ? 'Deteniendo...' : 'Apagar Bot (PM2 Stop)'}</span>
                                                    </div>
                                                    <ChevronDown size={16} className="text-red-500/50 -rotate-90" />
                                                </button>
                                                <button
                                                    onClick={() => handlePM2Action('restart')}
                                                    disabled={saving === 'pm2-restart'}
                                                    className="w-full flex items-center justify-between p-3 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 rounded-lg transition-colors group text-orange-400 disabled:opacity-50"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <RotateCcw size={18} className={`transition-transform duration-500 ${saving === 'pm2-restart' ? 'animate-spin' : 'group-hover:-rotate-180'}`} />
                                                        <span className="text-sm font-medium">{saving === 'pm2-restart' ? 'Reiniciando...' : 'Reiniciar Bot (PM2 Restart)'}</span>
                                                    </div>
                                                    <ChevronDown size={16} className="text-orange-500/50 -rotate-90" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Columna Derecha (Anuncios) */}
                                <div className="space-y-6">
                                    {/* Bloque 2: Anuncios Globales (Megáfono) */}
                                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                                        <div className="p-5 border-b border-white/10">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                                                    <FileText size={20} className="text-purple-400" />
                                                </div>
                                                <div>
                                                    <h3 className="text-lg font-medium text-white">Megáfono (Anuncios)</h3>
                                                    <p className="text-gray-500 text-xs">Enviar mensajes oficiales al servidor de Discord</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="p-6 space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="text-sm text-gray-400 mb-1 block">Título</label>
                                                    <input
                                                        type="text"
                                                        value={anuncioForm.titulo}
                                                        onChange={e => setAnuncioForm({ ...anuncioForm, titulo: e.target.value })}
                                                        className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                        placeholder="Ej: Inicio de Temporada"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="text-sm text-gray-400 mb-1 block">Color (Hex)</label>
                                                    <div className="flex gap-2">
                                                        <input
                                                            type="color"
                                                            value={anuncioForm.color}
                                                            onChange={e => setAnuncioForm({ ...anuncioForm, color: e.target.value })}
                                                            className="h-10 w-12 rounded cursor-pointer bg-transparent border-none"
                                                        />
                                                        <input
                                                            type="text"
                                                            value={anuncioForm.color}
                                                            onChange={e => setAnuncioForm({ ...anuncioForm, color: e.target.value })}
                                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            <div>
                                                <label className="text-sm text-gray-400 mb-1 block">Canal Destino (Nombre)</label>
                                                <input
                                                    type="text"
                                                    value={anuncioForm.canal_destino}
                                                    onChange={e => setAnuncioForm({ ...anuncioForm, canal_destino: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                    placeholder="anuncios"
                                                />
                                                <p className="text-xs text-gray-500 mt-1">Busca cualquier canal que contenga esta palabra. Default: 'anuncios' o 'general'.</p>
                                            </div>

                                            <div>
                                                <label className="text-sm text-gray-400 mb-1 block">URL de Imagen (Opcional)</label>
                                                <input
                                                    type="text"
                                                    value={anuncioForm.imagen_url}
                                                    onChange={e => setAnuncioForm({ ...anuncioForm, imagen_url: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                    placeholder="https://imgur.com/..."
                                                />
                                            </div>

                                            <div>
                                                <label className="text-sm text-gray-400 mb-2 block">Cuerpo del Mensaje</label>
                                                <textarea
                                                    rows="4"
                                                    value={anuncioForm.mensaje}
                                                    onChange={e => setAnuncioForm({ ...anuncioForm, mensaje: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-3 text-white focus:border-purple-500/50 focus:outline-none resize-none"
                                                    placeholder="Escribe el anuncio para la liga... (Soporta Markdown de Discord)"
                                                ></textarea>
                                            </div>
                                            <button
                                                onClick={handleSendAnnouncement}
                                                disabled={saving === 'anuncio'}
                                                className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 disabled:opacity-50 text-white font-bold rounded-lg transition-all shadow-lg shadow-purple-500/20"
                                            >
                                                {saving === 'anuncio' ? 'Enviando Anuncio...' : '📢 Publicar Noticia Oficial'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 2. TAB GLOBAL CONFIG */}
                        {activeSystemTab === 'config' && (
                            <div className="bg-[#0f1219] border border-white/5 rounded-2xl overflow-hidden shadow-xl max-w-3xl mx-auto">
                                <div className="p-5 border-b border-white/10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/20 flex items-center justify-center">
                                            <Settings size={20} className="text-gold-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-medium text-white">Configuración del Juego</h3>
                                            <p className="text-gray-500 text-xs">Variables en tiempo real</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-6 space-y-6 flex-1 relative">
                                    {loadingConfig ? (
                                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                                            <div className="w-8 h-8 border-4 border-gold-500/30 border-t-gold-500 rounded-full animate-spin"></div>
                                        </div>
                                    ) : null}

                                    <div className="flex items-center justify-between p-4 bg-black/20 rounded-xl border border-white/5">
                                        <div>
                                            <h4 className="text-white text-sm font-medium">Estado del Mercado</h4>
                                            <p className="text-gray-500 text-xs mt-1">Permitir Fichajes e Intercambios</p>
                                        </div>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input
                                                type="checkbox"
                                                className="sr-only peer"
                                                checked={!!globalConfig?.mercado_abierto}
                                                onChange={(e) => setGlobalConfig({ ...globalConfig, mercado_abierto: e.target.checked })}
                                            />
                                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                                        </label>
                                    </div>

                                    <div className="space-y-4">
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2 flex justify-between">
                                                <span>Límite de Jugadores por Plantilla</span>
                                                <span className="text-gold-400 font-bold">{globalConfig?.limite_plantilla || 12}</span>
                                            </label>
                                            <input
                                                type="range"
                                                min="5" max="25"
                                                value={globalConfig?.limite_plantilla || 12}
                                                onChange={(e) => setGlobalConfig({ ...globalConfig, limite_plantilla: e.target.value })}
                                                className="w-full accent-gold-500"
                                            />
                                        </div>

                                        <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-4">
                                            <div>
                                                <label className="text-[11px] text-gray-500 mb-1 block uppercase text-center">Pts. Victoria</label>
                                                <input
                                                    type="number"
                                                    value={globalConfig?.pts_victoria ?? 3}
                                                    onChange={e => setGlobalConfig({ ...globalConfig, pts_victoria: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-green-500/20 rounded-lg p-2 text-center text-green-400 font-bold focus:outline-none focus:border-green-500" />
                                            </div>
                                            <div>
                                                <label className="text-[11px] text-gray-500 mb-1 block uppercase text-center">Pts. Empate</label>
                                                <input
                                                    type="number"
                                                    value={globalConfig?.pts_empate ?? 1}
                                                    onChange={e => setGlobalConfig({ ...globalConfig, pts_empate: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-blue-500/20 rounded-lg p-2 text-center text-blue-400 font-bold focus:outline-none focus:border-blue-500" />
                                            </div>
                                            <div>
                                                <label className="text-[11px] text-gray-500 mb-1 block uppercase text-center">Pts. Derrota</label>
                                                <input
                                                    type="number"
                                                    value={globalConfig?.pts_derrota ?? 0}
                                                    onChange={e => setGlobalConfig({ ...globalConfig, pts_derrota: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-red-500/20 rounded-lg p-2 text-center text-red-400 font-bold focus:outline-none focus:border-red-500" />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
                                            <div>
                                                <label className="text-xs text-gray-400 mb-1 block">Goles W.O. a Favor</label>
                                                <input
                                                    type="number"
                                                    value={globalConfig?.walkover_gf ?? 3}
                                                    onChange={(e) => setGlobalConfig({ ...globalConfig, walkover_gf: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2 text-center text-white focus:outline-none focus:border-gold-500/50" />
                                            </div>
                                            <div>
                                                <label className="text-xs text-gray-400 mb-1 block">Goles W.O. en Contra</label>
                                                <input
                                                    type="number"
                                                    value={globalConfig?.walkover_gc ?? 0}
                                                    onChange={(e) => setGlobalConfig({ ...globalConfig, walkover_gc: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2 text-center text-white focus:outline-none focus:border-gold-500/50" />
                                            </div>
                                        </div>

                                        <div className="border-t border-white/5 pt-2 grid gap-3">
                                            <div>
                                                <label className="text-xs text-gray-500 mb-1 block">Rutas de Texto (IDs o Nombres exactos)</label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <input type="text" value={globalConfig?.canal_ofertas_id || ''} onChange={e => setGlobalConfig({ ...globalConfig, canal_ofertas_id: e.target.value })} placeholder="ID Canal Ofertas" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                                    <input type="text" value={globalConfig?.canal_fichajes || ''} onChange={e => setGlobalConfig({ ...globalConfig, canal_fichajes: e.target.value })} placeholder="Nmbr. Canal Fichajes" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                                    <input type="text" value={globalConfig?.rol_dt || ''} onChange={e => setGlobalConfig({ ...globalConfig, rol_dt: e.target.value })} placeholder="Nmbr. Rol DT" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                                    <input type="text" value={globalConfig?.rol_agente_libre || ''} onChange={e => setGlobalConfig({ ...globalConfig, rol_agente_libre: e.target.value })} placeholder="Nmbr. Rol Agente" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                                </div>
                                            </div>
                                        </div>

                                    </div>
                                </div>
                                <div className="p-4 border-t border-white/5 bg-black/20">
                                    <button
                                        onClick={handleSaveGlobalConfig}
                                        disabled={saving === 'global-config'}
                                        className="w-full py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black hover:from-gold-400 hover:to-gold-500 font-bold rounded-lg transition-colors text-sm shadow-[0_0_15px_rgba(234,179,8,0.2)]"
                                    >
                                        {saving === 'global-config' ? 'Aplicando Reglas...' : 'Guardar y Aplicar Reglas a la Liga'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* 3. TAB ZONA DE PELIGRO */}
                        {activeSystemTab === 'peligro' && (
                            <div className="bg-[#1f0909] border border-red-500/30 rounded-2xl overflow-hidden relative max-w-3xl mx-auto shadow-2xl">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/10 rounded-full blur-3xl"></div>
                                <div className="p-6 border-b border-red-500/20 bg-black/20">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center">
                                            <AlertTriangle size={20} className="text-red-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-red-500">Zona de Peligro</h3>
                                            <p className="text-red-400/70 text-xs">Mantenimiento de Base de Datos y Limpieza</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-6 space-y-4 relative z-10">
                                    <div className="p-4 bg-black/40 border border-red-500/10 rounded-xl">
                                        <h4 className="text-white text-sm font-medium mb-1 flex items-center gap-2"><Save size={14} className="text-gray-400" /> Generar Backup</h4>
                                        <p className="text-gray-500 text-xs mb-3">Crea un volcado total de la base de datos descargable como JSON. Útil antes del cierre de liga.</p>
                                        <button
                                            onClick={handleBackup}
                                            disabled={saving === 'backup'}
                                            className="w-full py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white border border-gray-600 rounded-lg transition-colors text-sm font-medium">
                                            {saving === 'backup' ? 'Generando...' : 'Descargar Backup Completo'}
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="p-4 bg-black/40 border border-orange-500/10 rounded-xl">
                                            <h4 className="text-orange-400 text-sm font-medium mb-1">Resetear Temporada</h4>
                                            <p className="text-gray-500 text-xs mb-3">Borra partidos, tabla y estadísticas. Mantiene equipos.</p>
                                            <button
                                                onClick={handleResetSeason}
                                                disabled={saving === 'reset'}
                                                className="w-full py-2 bg-orange-600/20 hover:bg-orange-600 hover:text-white disabled:opacity-50 border border-orange-500/50 text-orange-500 rounded-lg transition-all text-xs font-bold">
                                                {saving === 'reset' ? 'Reseteando...' : 'RESET LIGA'}
                                            </button>
                                        </div>
                                        <div className="p-4 bg-black/40 border border-blue-500/10 rounded-xl">
                                            <h4 className="text-blue-400 text-sm font-medium mb-1">Purgar Registros</h4>
                                            <p className="text-gray-500 text-xs mb-3">Elimina historiales y auditoría (+60 días) para aligerar la BD.</p>
                                            <button
                                                onClick={handlePurgeLogs}
                                                disabled={saving === 'purge'}
                                                className="w-full py-2 bg-blue-600/20 hover:bg-blue-600 hover:text-white disabled:opacity-50 border border-blue-500/50 text-blue-500 rounded-lg transition-all text-xs font-bold">
                                                {saving === 'purge' ? 'Limpiando...' : 'PURGAR BD'}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-xl">
                                        <h4 className="text-red-400 text-sm font-medium mb-1 flex items-center gap-2"><Trash2 size={14} /> NUKE: Borrado Total de Base de Datos</h4>
                                        <p className="text-red-200/50 text-xs mb-3">Borra absolutamente todos los equipos, jugadores, partidos, fichajes y tabla de la BD. ¡Irreversible!</p>
                                        <button
                                            onClick={handleNuke}
                                            disabled={saving === 'nuke'}
                                            className="w-full py-2 bg-red-600/20 hover:bg-red-600 disabled:opacity-50 hover:text-white border border-red-500/50 text-red-500 rounded-lg transition-all text-sm font-bold tracking-wider">
                                            {saving === 'nuke' ? 'DETONANDO CARGAS...' : 'INICIAR NUEVA ASOCIACIÓN DE 0'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            )}

            {/* Modals */}
            <EditStatsModal
                isOpen={isStatsModalOpen}
                onClose={() => setIsStatsModalOpen(false)}
                jugador={selectedJugador}
                onSave={handleStatsSave}
            />

            <CreatePartidoModal
                isOpen={isCreatePartidoModalOpen}
                onClose={() => setIsCreatePartidoModalOpen(false)}
                equipos={equipos}
                onSave={handleProgramarPartido}
            />

            <ReportarPartidoModal
                isOpen={isReporteModalOpen}
                onClose={() => {
                    setIsReporteModalOpen(false);
                    setSelectedPartido(null);
                }}
                partido={selectedPartido}
                onSave={handleRegistrarResultado}
            />

            {/* New Modals */}
            <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 ${isExpressModalOpen ? 'block' : 'hidden'}`}>
                <div className="bg-dark-950 border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-white">Registrar Resultado Manual</h3>
                        <button onClick={() => setIsExpressModalOpen(false)} className="text-gray-400 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Equipo Local</label>
                            <select value={resultadoForm.equipo_local}
                                onChange={(e) => setResultadoForm({ ...resultadoForm, equipo_local: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-green-500/50 focus:outline-none">
                                <option value="">Seleccionar...</option>
                                {equipos.map(eq => <option key={`rl-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                        <div className="text-center">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Marcador</label>
                            <div className="flex items-center justify-center gap-2">
                                <input type="number" min="0" value={resultadoForm.goles_local}
                                    onChange={(e) => setResultadoForm({ ...resultadoForm, goles_local: e.target.value })}
                                    className="w-16 bg-white/5 border border-white/10 rounded px-2 py-1 text-center text-lg font-bold text-gold-400 focus:border-green-500/50 focus:outline-none" />
                                <span className="text-gray-400 font-bold text-xl">-</span>
                                <input type="number" min="0" value={resultadoForm.goles_visitante}
                                    onChange={(e) => setResultadoForm({ ...resultadoForm, goles_visitante: e.target.value })}
                                    className="w-16 bg-white/5 border border-white/10 rounded px-2 py-1 text-center text-lg font-bold text-gold-400 focus:border-green-500/50 focus:outline-none" />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Equipo Visitante</label>
                            <select value={resultadoForm.equipo_visitante}
                                onChange={(e) => setResultadoForm({ ...resultadoForm, equipo_visitante: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-green-500/50 focus:outline-none">
                                <option value="">Seleccionar...</option>
                                {equipos.map(eq => <option key={`rv-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                        <button onClick={handleRegistrarResultadoManual} disabled={saving === 'resultado'}
                            className="w-full px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 text-black rounded-lg hover:from-green-400 hover:to-green-500 disabled:opacity-50 transition-all font-medium">
                            {saving === 'resultado' ? 'Registrando...' : '⚽ Registrar Resultado'}
                        </button>
                    </div>
                </div>
            </div>

            <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 ${isWalkoverModalOpen ? 'block' : 'hidden'}`}>
                <div className="bg-dark-950 border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-white">Dictar Walkover</h3>
                        <button onClick={() => setIsWalkoverModalOpen(false)} className="text-gray-400 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">🏆 Ganador</label>
                            <select value={walkoverForm.ganador}
                                onChange={(e) => setWalkoverForm({ ...walkoverForm, ganador: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-red-500/50 focus:outline-none">
                                <option value="">Seleccionar...</option>
                                {equipos.map(eq => <option key={`wg-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">❌ Incomparecencia</label>
                            <select value={walkoverForm.perdedor}
                                onChange={(e) => setWalkoverForm({ ...walkoverForm, perdedor: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-red-500/50 focus:outline-none">
                                <option value="">Seleccionar...</option>
                                {equipos.map(eq => <option key={`wp-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                        <button onClick={handleRegistrarWalkover} disabled={saving === 'walkover'}
                            className="w-full px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 transition-all font-medium">
                            {saving === 'walkover' ? 'Procesando...' : '🚫 Dictar Walkover'}
                        </button>
                    </div>
                </div>
            </div>

            <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 ${isPuntosModalOpen ? 'block' : 'hidden'}`}>
                <div className="bg-dark-950 border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-white">Ajustes de Puntos</h3>
                        <button onClick={() => setIsPuntosModalOpen(false)} className="text-gray-400 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                                <label className="block text-sm font-medium text-gray-300 mb-2">🟢 Victoria</label>
                                <input type="number" min="0" value={puntuacion.pts_victoria}
                                    onChange={(e) => setPuntuacion({ ...puntuacion, pts_victoria: parseInt(e.target.value) || 0 })}
                                    className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-center text-lg font-bold text-green-400 focus:border-gold-500/50 focus:outline-none" />
                            </div>
                            <div className="text-center">
                                <label className="block text-sm font-medium text-gray-300 mb-2">🟡 Empate</label>
                                <input type="number" min="0" value={puntuacion.pts_empate}
                                    onChange={(e) => setPuntuacion({ ...puntuacion, pts_empate: parseInt(e.target.value) || 0 })}
                                    className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-center text-lg font-bold text-yellow-400 focus:border-gold-500/50 focus:outline-none" />
                            </div>
                            <div className="text-center">
                                <label className="block text-sm font-medium text-gray-300 mb-2">🔴 Derrota</label>
                                <input type="number" min="0" value={puntuacion.pts_derrota}
                                    onChange={(e) => setPuntuacion({ ...puntuacion, pts_derrota: parseInt(e.target.value) || 0 })}
                                    className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-center text-lg font-bold text-red-400 focus:border-gold-500/50 focus:outline-none" />
                            </div>
                        </div>
                        <button onClick={handleSavePuntuacion} disabled={saving === 'puntuacion'}
                            className="w-full px-4 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black rounded-lg hover:from-gold-400 hover:to-gold-500 disabled:opacity-50 transition-all font-medium">
                            {saving === 'puntuacion' ? 'Guardando...' : '💾 Guardar y Recalcular'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Admin;
