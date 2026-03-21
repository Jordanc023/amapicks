import React, { useMemo, useState } from 'react';
import {
    Calendar, Edit, Trash2, Plus, Activity, Ban, Settings,
    ChevronDown, AlertTriangle, RotateCcw, Trophy, LayoutList
} from 'lucide-react';

/**
 * Tab Liga — Partidos del fixture, panel de control y nuevo partido.
 * La generación del calendario vive en Admin → Ligas (unificado).
 */
const LigaTab = ({
    partidosPendientes,
    partidosTodos = [],
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
}) => {
    const [filtroFixture, setFiltroFixture] = useState('todos'); // todos | pendientes

    const partidosFiltrados = useMemo(() => {
        if (filtroFixture === 'pendientes') {
            return partidosTodos.filter((p) => p.estado === 'pendiente' || p.estado === 'auditoria');
        }
        return partidosTodos;
    }, [partidosTodos, filtroFixture]);

    const partidosPorJornada = useMemo(() => {
        const map = new Map();
        partidosFiltrados.forEach((p) => {
            const j = p.jornada ?? 0;
            if (!map.has(j)) map.set(j, []);
            map.get(j).push(p);
        });
        return [...map.entries()].sort((a, b) => a[0] - b[0]);
    }, [partidosFiltrados]);

    const formatFechaPartido = (p) => {
        const raw = p.fecha_hora || p.fecha_programada;
        if (!raw) return 'Sin fecha';
        try {
            const d = new Date(raw);
            if (Number.isNaN(d.getTime())) return String(raw);
            return d.toLocaleDateString('es', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return String(raw);
        }
    };

    const badgeEstado = (estado) => {
        const e = (estado || 'pendiente').toLowerCase();
        if (e === 'finalizado' || e === 'jugado') {
            return 'bg-green-500/10 text-green-400 border border-green-500/20';
        }
        if (e === 'walkover') {
            return 'bg-orange-500/10 text-orange-400 border border-orange-500/20';
        }
        if (e === 'auditoria') {
            return 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20';
        }
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Centro de Liga</h2>
                    <p className="text-gray-500 mt-1">Fixture, partidos y resultados</p>
                </div>
                <button
                    onClick={() => setIsCreatePartidoModalOpen(true)}
                    className="px-4 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 transition-all font-medium flex items-center gap-2 shadow-lg shadow-gold-500/20"
                >
                    <Plus size={16} />
                    <span>Nuevo Partido</span>
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-8 space-y-6">
                    {/* Generar calendario: en pestaña Ligas */}
                    <div className="bg-dark-900/40 border border-white/10 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gold-500/15 border border-gold-500/30 flex items-center justify-center shrink-0">
                                <LayoutList size={20} className="text-gold-400" />
                            </div>
                            <div>
                                <h3 className="text-sm font-semibold text-white">Calendario / temporada</h3>
                                <p className="text-gray-500 text-xs mt-0.5">
                                    Genera el fixture en la sección superior de esta misma pestaña: elige la liga, asigna equipos y usa{' '}
                                    <span className="text-gold-400 font-medium">Generar Fixture</span>.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Fixture completo */}
                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                        <div className="p-4 border-b border-white/10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                    <Calendar size={16} className="text-blue-400" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-medium text-white">Calendario del fixture</h3>
                                    <p className="text-gray-500 text-xs">
                                        {partidosTodos.length} partidos de liga regular
                                        {partidosPendientes.length > 0 ? ` · ${partidosPendientes.length} pendientes` : ''}
                                    </p>
                                </div>
                            </div>
                            <div className="flex rounded-lg border border-white/10 overflow-hidden text-xs font-medium">
                                <button
                                    type="button"
                                    onClick={() => setFiltroFixture('todos')}
                                    className={`px-3 py-2 ${filtroFixture === 'todos' ? 'bg-white text-black' : 'bg-dark-900 text-gray-400 hover:text-white'}`}
                                >
                                    Todos
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setFiltroFixture('pendientes')}
                                    className={`px-3 py-2 border-l border-white/10 ${filtroFixture === 'pendientes' ? 'bg-white text-black' : 'bg-dark-900 text-gray-400 hover:text-white'}`}
                                >
                                    Solo pendientes
                                </button>
                            </div>
                        </div>

                        {partidosPorJornada.length === 0 ? (
                            <div className="p-8 text-center">
                                <Calendar size={40} className="text-gray-600 mx-auto mb-3" />
                                <p className="text-gray-500">No hay partidos de liga regular</p>
                                <p className="text-gray-600 text-sm mt-2">
                                    Crea el fixture en la parte superior de <span className="text-gold-500">Admin → Liga</span>
                                </p>
                            </div>
                        ) : (
                            <div className="p-3 max-h-[min(70vh,900px)] overflow-y-auto space-y-4">
                                {partidosPorJornada.map(([jornada, lista]) => (
                                    <div key={jornada} className="rounded-xl border border-white/5 bg-[#0d1017]/80 overflow-hidden">
                                        <div className="px-3 py-2 bg-white/[0.03] border-b border-white/5 flex items-center justify-between">
                                            <span className="text-gold-400 text-xs font-bold uppercase tracking-wider">
                                                Jornada {jornada}
                                            </span>
                                            <span className="text-gray-500 text-xs">{lista.length} partidos</span>
                                        </div>
                                        <div className="p-2 grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {lista.map((p) => {
                                                const pendiente = p.estado === 'pendiente' || p.estado === 'auditoria';
                                                return (
                                                    <div
                                                        key={p._id}
                                                        className="group bg-[#0d1017] border border-white/5 rounded-xl p-3 hover:border-white/15 transition-colors"
                                                    >
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <div className="flex-1 text-center min-w-0">
                                                                <div className="text-white font-bold text-sm truncate">{p.equipo_local}</div>
                                                            </div>
                                                            <div className="flex flex-col items-center flex-shrink-0 px-1">
                                                                <span className="text-gray-500 text-[10px] font-bold">VS</span>
                                                            </div>
                                                            <div className="flex-1 text-center min-w-0">
                                                                <div className="text-white font-bold text-sm truncate">{p.equipo_visitante}</div>
                                                            </div>
                                                        </div>
                                                        <div className="flex flex-wrap items-center gap-2 justify-between">
                                                            <div className="flex items-center gap-2 text-gray-500 text-xs">
                                                                <Calendar size={12} />
                                                                <span>{formatFechaPartido(p)}</span>
                                                                {p.sub_fase && (
                                                                    <span className="text-gray-600">· {p.sub_fase}</span>
                                                                )}
                                                            </div>
                                                            <span
                                                                className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${badgeEstado(p.estado)}`}
                                                            >
                                                                {p.estado || 'pendiente'}
                                                            </span>
                                                        </div>
                                                        {pendiente && (
                                                            <div className="mt-2 flex gap-2 opacity-90 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                                                                <button
                                                                    type="button"
                                                                    onClick={() => {
                                                                        setSelectedPartido(p);
                                                                        setIsReporteModalOpen(true);
                                                                    }}
                                                                    className="flex-1 px-2 py-1.5 bg-green-500/90 text-black rounded-lg text-xs font-medium hover:bg-green-400"
                                                                >
                                                                    <Edit size={12} className="inline mr-1" />
                                                                    Registrar
                                                                </button>
                                                                <button
                                                                    type="button"
                                                                    onClick={() => handleEliminarPartido(p._id)}
                                                                    className="px-2 py-1.5 bg-red-500/80 text-white rounded-lg text-xs font-medium hover:bg-red-600"
                                                                >
                                                                    <Trash2 size={12} className="inline" />
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="lg:col-span-4 space-y-4">
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
                            {estadoLiga && estadoLiga.estado !== 'no_iniciada' && (
                                <div className="bg-black/20 rounded-lg p-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-white text-sm font-medium">Temporada Activa</span>
                                        <span
                                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                estadoLiga.estado === 'en_curso'
                                                    ? 'bg-blue-500/10 text-blue-400'
                                                    : estadoLiga.estado === 'playoffs'
                                                      ? 'bg-purple-500/10 text-purple-400'
                                                      : 'bg-green-500/10 text-green-400'
                                            }`}
                                        >
                                            {estadoLiga.estado === 'en_curso'
                                                ? 'En Curso'
                                                : estadoLiga.estado === 'playoffs'
                                                  ? 'Playoffs'
                                                  : 'Finalizada'}
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

                            <button
                                onClick={() => setIsDangerZoneOpen(!isDangerZoneOpen)}
                                className="w-full px-4 py-3 bg-white/5 border border-red-500/20 text-red-400 rounded-lg hover:bg-red-500/5 transition-all font-medium flex items-center justify-center gap-2"
                            >
                                <AlertTriangle size={16} />
                                <span>Herramientas Avanzadas</span>
                                <ChevronDown size={16} className={`transition-transform ${isDangerZoneOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {isDangerZoneOpen && (
                                <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 space-y-2">
                                    <div className="flex items-start gap-2">
                                        <AlertTriangle size={14} className="text-red-400 mt-0.5" />
                                        <div>
                                            <h4 className="text-red-400 text-xs font-medium mb-1">⚠️ Precaución</h4>
                                            <p className="text-gray-400 text-xs">Operaciones críticas del sistema</p>
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleRecalcularTabla}
                                        disabled={saving === 'recalcular'}
                                        className="w-full p-2 bg-white/5 border border-blue-500/20 rounded hover:bg-blue-500/5 transition-all text-left group disabled:opacity-50 text-sm"
                                    >
                                        <div className="flex items-center gap-2">
                                            <RotateCcw size={14} className="text-blue-400" />
                                            <span className="text-white">
                                                {saving === 'recalcular' ? 'Recalculando...' : 'Recalcular Tabla'}
                                            </span>
                                        </div>
                                    </button>

                                    <button
                                        onClick={handleResetearTabla}
                                        disabled={saving === 'resetear'}
                                        className="w-full p-2 bg-red-500/5 border border-red-500/20 rounded hover:bg-red-500/10 transition-all text-left group disabled:opacity-50 text-sm"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Trash2 size={14} className="text-red-400" />
                                            <span className="text-white">
                                                {saving === 'resetear' ? 'Borrando...' : 'Resetear Tabla'}
                                            </span>
                                        </div>
                                    </button>
                                </div>
                            )}

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
    );
};

export default LigaTab;
