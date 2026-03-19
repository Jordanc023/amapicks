import React from 'react';
import {
    Calendar, Edit, Trash2, Plus, Activity, Ban, Settings,
    ChevronDown, AlertTriangle, RotateCcw, Trophy
} from 'lucide-react';

/**
 * Tab de Liga/Partidos – Calendario, asistente de temporada, partidos pendientes,
 * panel de control con acciones rápidas y herramientas avanzadas.
 */
const LigaTab = ({
    equipos,
    partidosPendientes,
    estadoLiga,
    saving,
    // Modals
    setIsCreatePartidoModalOpen,
    setIsReporteModalOpen,
    setSelectedPartido,
    setIsExpressModalOpen,
    setIsWalkoverModalOpen,
    setIsPuntosModalOpen,
    // Handlers
    handleEliminarPartido,
    handleGenerarCalendario,
    handleGenerarPlayoffs,
    handleRecalcularTabla,
    handleResetearTabla,
    // Calendario form
    calendarioForm,
    setCalendarioForm,
    // Danger zone
    isDangerZoneOpen,
    setIsDangerZoneOpen,
}) => {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-end pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Centro de Liga</h2>
                    <p className="text-gray-500 mt-1">Gestión de partidos, calendario y resultados</p>
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
                {/* Columna Principal (8/12) */}
                <div className="lg:col-span-8 space-y-6">

                    {/* Asistente de Configuración (solo si no hay liga o no_iniciada) */}
                    {(!estadoLiga || estadoLiga.estado === 'no_iniciada') && equipos.length >= 2 && (
                        <div className="bg-gradient-to-br from-gold-500/10 to-gold-500/5 border border-gold-500/20 rounded-2xl overflow-hidden">
                            <div className="p-5 border-b border-gold-500/10">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-gold-500/20 border border-gold-500/30 flex items-center justify-center">
                                        <Settings size={20} className="text-gold-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-medium text-gold-400">⚡ Asistente de Configuración de Temporada</h3>
                                        <p className="text-gray-500 text-xs">Genera un calendario ALL vs ALL automáticamente</p>
                                    </div>
                                </div>
                            </div>
                            <div className="p-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-gray-400 block mb-1">Fecha de Inicio</label>
                                        <input
                                            type="date"
                                            value={calendarioForm.fecha_inicio}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, fecha_inicio: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-400 block mb-1">Hora por Defecto</label>
                                        <input
                                            type="time"
                                            value={calendarioForm.hora_default}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, hora_default: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-gray-400 block mb-1">Días entre Jornadas</label>
                                        <input
                                            type="number" min="1"
                                            value={calendarioForm.dias_entre_jornadas}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, dias_entre_jornadas: parseInt(e.target.value) || 1 })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-400 block mb-1">Clasificados a Playoffs</label>
                                        <input
                                            type="number" min="2"
                                            value={calendarioForm.clasificados_playoffs}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, clasificados_playoffs: parseInt(e.target.value) || 4 })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs text-gray-400 block mb-1">Tipo de Liga</label>
                                        <select
                                            value={calendarioForm.tipo_liga}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, tipo_liga: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                        >
                                            <option value="estandar">Todos contra Todos (Normal)</option>
                                            <option value="d1">Liga D1 (Ida/Vuelta + Copa)</option>
                                        </select>
                                    </div>
                                    {calendarioForm.tipo_liga === 'd1' && (
                                        <div>
                                            <label className="text-xs text-gray-400 block mb-1">Días de Pausa para Copa</label>
                                            <input
                                                type="number" min="0"
                                                value={calendarioForm.dias_pausa_copa}
                                                onChange={(e) => setCalendarioForm({ ...calendarioForm, dias_pausa_copa: parseInt(e.target.value) || 0 })}
                                                className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-gold-500/50 focus:outline-none"
                                            />
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-3 bg-black/20 p-3 rounded-lg">
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="sr-only peer"
                                            checked={calendarioForm.playoffs_habilitados}
                                            onChange={(e) => setCalendarioForm({ ...calendarioForm, playoffs_habilitados: e.target.checked })}
                                        />
                                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gold-500"></div>
                                    </label>
                                    <span className="text-sm text-gray-300">Habilitar Playoffs</span>
                                </div>

                                <button
                                    onClick={handleGenerarCalendario}
                                    disabled={saving === 'calendario'}
                                    className="w-full py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black rounded-lg hover:from-gold-400 hover:to-gold-500 disabled:opacity-50 transition-all font-bold text-sm shadow-lg shadow-gold-500/20"
                                >
                                    {saving === 'calendario' ? 'Generando Calendario...' : `⚡ Generar Temporada (${equipos.length} equipos)`}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Lista de Partidos Pendientes */}
                    {partidosPendientes.length > 0 && (
                        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                            <div className="p-4 border-b border-white/10">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                            <Calendar size={16} className="text-blue-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-medium text-white">Partidos Pendientes</h3>
                                            <p className="text-gray-500 text-xs">{partidosPendientes.length} por jugar</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-2 max-h-[500px] overflow-y-auto">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {partidosPendientes.map((p) => {
                                        const fechaProg = p.fecha_programada
                                            ? new Date(p.fecha_programada).toLocaleDateString('es', { day: '2-digit', month: 'short', hour: '2-digit', minute:'2-digit' })
                                            : 'Sin fecha';

                                        return (
                                            <div
                                                key={p._id}
                                                className="group bg-[#0d1017] border border-white/5 rounded-xl p-3 hover:border-white/20 transition-all cursor-pointer"
                                            >
                                                {/* Match Info */}
                                                <div className="flex items-center gap-2 mb-2">
                                                    <div className="flex-1 text-center">
                                                        <div className="text-white font-bold text-sm truncate">{p.equipo_local}</div>
                                                    </div>
                                                    <div className="flex flex-col items-center flex-shrink-0">
                                                        <span className="text-gray-500 text-xs font-bold">VS</span>
                                                        <div className="text-gray-500 text-xs">
                                                            {p.jornada ? `J${p.jornada}` : p.fase}
                                                        </div>
                                                    </div>
                                                    <div className="flex-1 text-center">
                                                        <div className="text-white font-bold text-sm truncate">{p.equipo_visitante}</div>
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
    );
};

export default LigaTab;
