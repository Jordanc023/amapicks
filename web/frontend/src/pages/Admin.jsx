import React from 'react';
import { Settings, Users, Shield, RefreshCw, ShieldAlert, FileText, Trophy, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import useAdminData from '../hooks/useAdminData';

// Tab Components
import EquiposTab from '../components/admin/EquiposTab';
import JugadoresTab from '../components/admin/JugadoresTab';
import AuditoriaTab from '../components/admin/AuditoriaTab';
import SistemaTab from '../components/admin/SistemaTab';
import CompeticionTab from '../components/admin/CompeticionTab';

// External Modals
import EditStatsModal from '../components/admin/EditStatsModal';
import CreatePartidoModal from '../components/admin/CreatePartidoModal';
import ReportarPartidoModal from '../components/admin/ReportarPartidoModal';

const Admin = () => {
    const { user, loading: authLoading } = useAuth();

    // ─── Hook centralizado ───────────────────────────────────────────
    const {
        // Data
        equipos,
        jugadores,
        auditoriaLogs,
        partidosPendientes,
        loading,
        searchTerm,
        setSearchTerm,
        saving,
        presupuestos,
        preciosJugadores,
        puntuacion,
        setPuntuacion,
        resultadoForm,
        setResultadoForm,
        walkoverForm,
        setWalkoverForm,
        estadoLiga,
        partidosTodos,
        systemStatus,
        anuncioForm,
        setAnuncioForm,
        globalConfig,
        setGlobalConfig,
        loadingConfig,
        // Tabs
        activeTab,
        setActiveTab,
        activeSystemTab,
        setActiveSystemTab,
        // Modals
        isStatsModalOpen,
        setIsStatsModalOpen,
        isCreatePartidoModalOpen,
        setIsCreatePartidoModalOpen,
        isReporteModalOpen,
        setIsReporteModalOpen,
        selectedJugador,
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
        // Handlers
        loadData,
        handlePresupuestoChange,
        handlePrecioJugadorChange,
        handleUpdatePresupuesto,
        handleUpdatePrecio,
        handleUpdatePresupuestosMasivo,
        handleUpdatePreciosMasivo,
        openEditStats,
        handleStatsSave,
        handleProgramarPartido,
        handleEliminarPartido,
        handleRegistrarResultado,
        handleRegistrarResultadoManual,
        handleRegistrarWalkover,
        handleSavePuntuacion,
        handleGenerarPlayoffs,
        handleRecalcularTabla,
        handleResetearTabla,
        handleSyncCommands,
        handlePM2Action,
        handleSendAnnouncement,
        handleSaveGlobalConfig,
        handleBackup,
        handleResetSeason,
        handleNuke,
        handlePurgeLogs,
        // Utils
        formatMoney,
        filteredJugadores,
    } = useAdminData(user);

    // ─── Loading State ───────────────────────────────────────────────
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

    // ─── Unauthorized State ──────────────────────────────────────────
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

    // ─── Tab definitions ─────────────────────────────────────────────
    const tabs = [
        { key: 'liga', label: 'Liga', icon: Trophy },
        { key: 'equipos', label: 'Equipos', icon: Shield, count: equipos.length },
        { key: 'jugadores', label: 'Jugadores', icon: Users, count: jugadores.length },
        { key: 'auditoria', label: 'Auditoría', icon: FileText },
        { key: 'sistema', label: 'Sistema', icon: Settings, gold: true },
    ];

    return (
        <div className="min-h-screen bg-dark-950">
            <div className="max-w-7xl mx-auto px-8 py-12">
                {/* Page Header */}
                <div className="flex justify-between items-end mb-12 pb-8 border-b border-white/5">
                    <div>
                        <h1 className="text-6xl font-light text-white tracking-tight mb-2">Administración</h1>
                        <p className="text-gray-500 text-lg">Gestión centralizada de la liga</p>
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
                {tabs.map(({ key, label, icon: Icon, count, gold }) => (
                    <button
                        key={key}
                        onClick={() => setActiveTab(key)}
                        className={`px-8 py-4 font-medium transition-all rounded-xl flex items-center gap-3 text-sm ${activeTab === key
                            ? gold
                                ? 'bg-gold-500 text-black shadow-lg shadow-gold-500/20'
                                : 'bg-white text-black shadow-lg'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Icon size={20} className={activeTab === key ? 'text-black' : ''} />
                        <span>{label}</span>
                        {count !== undefined && (
                            <span className={`px-2 py-1 rounded-full text-xs ${activeTab === key ? 'bg-black/10 text-black' : 'bg-white/10 text-gray-400'}`}>
                                {count}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* ═══ Tab Content ═══ */}
            <div className="max-w-7xl mx-auto px-8">
                {activeTab === 'liga' && (
                    <CompeticionTab
                        onCompeticionChanged={loadData}
                        ligaTabProps={{
                            partidosPendientes,
                            partidosTodos,
                            estadoLiga,
                            saving,
                            setIsCreatePartidoModalOpen,
                            setIsReporteModalOpen,
                            setSelectedPartido,
                            setIsExpressModalOpen,
                            setIsWalkoverModalOpen,
                            setIsPuntosModalOpen,
                            handleEliminarPartido,
                            handleGenerarPlayoffs,
                            handleRecalcularTabla,
                            handleResetearTabla,
                            isDangerZoneOpen,
                            setIsDangerZoneOpen,
                        }}
                    />
                )}

                {activeTab === 'equipos' && (
                    <EquiposTab
                        equipos={equipos}
                        presupuestos={presupuestos}
                        saving={saving}
                        handlePresupuestoChange={handlePresupuestoChange}
                        handleUpdatePresupuesto={handleUpdatePresupuesto}
                        handleUpdatePresupuestosMasivo={handleUpdatePresupuestosMasivo}
                        formatMoney={formatMoney}
                    />
                )}

                {activeTab === 'jugadores' && (
                    <JugadoresTab
                        filteredJugadores={filteredJugadores}
                        jugadores={jugadores}
                        searchTerm={searchTerm}
                        setSearchTerm={setSearchTerm}
                        preciosJugadores={preciosJugadores}
                        saving={saving}
                        handlePrecioJugadorChange={handlePrecioJugadorChange}
                        handleUpdatePrecio={handleUpdatePrecio}
                        handleUpdatePreciosMasivo={handleUpdatePreciosMasivo}
                        openEditStats={openEditStats}
                        formatMoney={formatMoney}
                        totalJugadores={jugadores.length}
                    />
                )}

                {activeTab === 'auditoria' && (
                    <AuditoriaTab auditoriaLogs={auditoriaLogs} />
                )}

                {activeTab === 'sistema' && (
                    <SistemaTab
                        activeSystemTab={activeSystemTab}
                        setActiveSystemTab={setActiveSystemTab}
                        systemStatus={systemStatus}
                        saving={saving}
                        handleSyncCommands={handleSyncCommands}
                        handlePM2Action={handlePM2Action}
                        handleSendAnnouncement={handleSendAnnouncement}
                        handleSaveGlobalConfig={handleSaveGlobalConfig}
                        handleBackup={handleBackup}
                        handleResetSeason={handleResetSeason}
                        handleNuke={handleNuke}
                        handlePurgeLogs={handlePurgeLogs}
                        globalConfig={globalConfig}
                        setGlobalConfig={setGlobalConfig}
                        loadingConfig={loadingConfig}
                        anuncioForm={anuncioForm}
                        setAnuncioForm={setAnuncioForm}
                    />
                )}
            </div>

            {/* ═══ External Modals ═══ */}
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

            {/* ═══ Inline Modal: Registrar Resultado Manual ═══ */}
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

            {/* ═══ Inline Modal: Walkover ═══ */}
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

            {/* ═══ Inline Modal: Puntos ═══ */}
            <div className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 ${isPuntosModalOpen ? 'block' : 'hidden'}`}>
                <div className="bg-dark-950 border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="text-lg font-medium text-white">Ajustes de Puntos</h3>
                            <p className="text-xs text-gray-500 mt-1">
                                Liga activa:{' '}
                                <span className="text-gold-400">{puntuacion.liga_nombre || '—'}</span>
                                {puntuacion.liga_id ? (
                                    <span className="text-gray-600 ml-1">({String(puntuacion.liga_id).slice(0, 8)}…)</span>
                                ) : null}
                            </p>
                        </div>
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
                        <div className="grid grid-cols-2 gap-3">
                            <div className="text-center">
                                <label className="block text-sm font-medium text-gray-300 mb-2">W.O. a favor</label>
                                <input type="number" min="0" value={puntuacion.walkover_gf}
                                    onChange={(e) => setPuntuacion({ ...puntuacion, walkover_gf: parseInt(e.target.value, 10) || 0 })}
                                    className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-center text-lg font-bold text-white focus:border-gold-500/50 focus:outline-none" />
                            </div>
                            <div className="text-center">
                                <label className="block text-sm font-medium text-gray-300 mb-2">W.O. en contra</label>
                                <input type="number" min="0" value={puntuacion.walkover_gc}
                                    onChange={(e) => setPuntuacion({ ...puntuacion, walkover_gc: parseInt(e.target.value, 10) || 0 })}
                                    className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-center text-lg font-bold text-white focus:border-gold-500/50 focus:outline-none" />
                            </div>
                        </div>
                        <p className="text-[11px] text-gray-500">
                            Se guardan en el documento de la liga activa y se copian a la configuración del servidor (bot).
                        </p>
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
