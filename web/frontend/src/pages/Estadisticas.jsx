import React, { useState, useEffect } from 'react';
import {
    Trophy, Users, DollarSign, Zap, Target, TrendingUp, Calendar,
    Shield, Activity, Crown, Loader2, ChevronUp, ChevronDown, Minus
} from 'lucide-react';
import { ligaService } from '../services/api';

const getPosConfig = (pos) => {
    switch (pos) {
        case 'GK': return { color: 'text-yellow-400', bg: 'bg-yellow-500', bgSoft: 'bg-yellow-500/10', border: 'border-yellow-500/30' };
        case 'DEF': return { color: 'text-blue-400', bg: 'bg-blue-500', bgSoft: 'bg-blue-500/10', border: 'border-blue-500/30' };
        case 'MC': return { color: 'text-green-400', bg: 'bg-green-500', bgSoft: 'bg-green-500/10', border: 'border-green-500/30' };
        case 'DC': return { color: 'text-red-400', bg: 'bg-red-500', bgSoft: 'bg-red-500/10', border: 'border-red-500/30' };
        default: return { color: 'text-gray-400', bg: 'bg-gray-500', bgSoft: 'bg-gray-500/10', border: 'border-gray-500/30' };
    }
};

const getActionConfig = (type) => {
    switch (type) {
        case 'FICHAJE': return { icon: '⚽', label: 'Fichaje', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' };
        case 'DESPIDO': return { icon: '🔴', label: 'Despido', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
        case 'DT_ASIGNADO': return { icon: '👔', label: 'Nuevo DT', color: 'text-gold-400', bg: 'bg-gold-500/10', border: 'border-gold-500/20' };
        case 'DT_RENUNCIA': return { icon: '👋', label: 'Renuncia DT', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' };
        case 'MERCADO_ABIERTO': return { icon: '🟢', label: 'Mercado Abierto', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' };
        case 'MERCADO_CERRADO': return { icon: '🔒', label: 'Mercado Cerrado', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
        case 'RESULTADO_REGISTRADO': return { icon: '📋', label: 'Resultado', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' };
        default: return { icon: '📝', label: type, color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/20' };
    }
};

const Estadisticas = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const result = await ligaService.getEstadisticas();
                setData(result);
            } catch (error) {
                console.error("Error cargando estadísticas:", error);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center gap-4">
                <Loader2 className="w-10 h-10 text-gold-500 animate-spin" />
                <span className="text-gray-500 text-sm font-medium uppercase tracking-widest">Cargando estadísticas...</span>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <p className="text-gray-500">Error al cargar estadísticas</p>
            </div>
        );
    }

    const { tabla_posiciones, ultimos_resultados, partidos_pendientes,
        actividad_reciente, top_jugadores, equipos_ranking, stats_generales } = data;

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 min-h-screen pb-20 px-4 sm:px-6 pt-6">
            <div className="max-w-7xl mx-auto">

                {/* ===== HEADER ===== */}
                <div className="mb-10">
                    <div className="relative">
                        <div className="absolute -inset-4 bg-gradient-to-r from-gold-500/5 via-transparent to-gold-500/5 rounded-3xl blur-2xl" />
                        <div className="relative">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-10 h-10 bg-gold-500/10 border border-gold-500/30 rounded-xl flex items-center justify-center">
                                    <Trophy size={20} className="text-gold-500" />
                                </div>
                            </div>
                            <h1 className="text-4xl sm:text-5xl font-display font-black text-white uppercase tracking-tight mb-2">
                                Estadísticas <span className="text-gold-500">de la Liga</span>
                            </h1>
                            <p className="text-gray-400 max-w-lg text-sm sm:text-base">
                                Tabla de posiciones, resultados, rankings y actividad en tiempo real.
                            </p>
                        </div>
                    </div>
                </div>

                {/* ===== STATS GENERALES ===== */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                            <Target size={18} className="text-blue-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{stats_generales.total_partidos_jugados}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Partidos</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                            <Zap size={18} className="text-green-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{stats_generales.total_goles}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Goles</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-gold-500/10 flex items-center justify-center">
                            <TrendingUp size={18} className="text-gold-500" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{stats_generales.promedio_goles}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Goles/P</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                            <Users size={18} className="text-purple-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{stats_generales.total_fichajes}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Fichajes</span>
                        </div>
                    </div>
                </div>

                {/* ===== MAIN GRID: Tabla + Side Panel ===== */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">

                    {/* ===== TABLA DE POSICIONES (2/3) ===== */}
                    <div className="lg:col-span-2">
                        <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                            <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-gold-600" />
                            <div className="p-6 pb-4 border-b border-white/5">
                                <h2 className="flex items-center gap-2 text-gold-500 font-display font-bold text-lg uppercase tracking-widest">
                                    <Trophy size={20} /> Tabla de Posiciones
                                </h2>
                            </div>

                            {tabla_posiciones.length > 0 ? (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-gray-500 text-[10px] uppercase tracking-widest border-b border-white/5">
                                                <th className="text-center py-3 px-3 w-10">#</th>
                                                <th className="text-left py-3 px-3">Equipo</th>
                                                <th className="text-center py-3 px-2 hidden sm:table-cell">PJ</th>
                                                <th className="text-center py-3 px-2 hidden sm:table-cell">PG</th>
                                                <th className="text-center py-3 px-2 hidden sm:table-cell">PE</th>
                                                <th className="text-center py-3 px-2 hidden sm:table-cell">PP</th>
                                                <th className="text-center py-3 px-2 hidden md:table-cell">GF</th>
                                                <th className="text-center py-3 px-2 hidden md:table-cell">GC</th>
                                                <th className="text-center py-3 px-2">DIF</th>
                                                <th className="text-center py-3 px-3 font-black">PTS</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {tabla_posiciones.map((equipo, idx) => {
                                                const pos = idx + 1;
                                                const isTop = pos <= 2;
                                                const isBottom = pos >= tabla_posiciones.length - 1 && tabla_posiciones.length > 3;
                                                return (
                                                    <tr
                                                        key={idx}
                                                        className={`border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors ${isTop ? 'bg-green-500/[0.03]' : isBottom ? 'bg-red-500/[0.03]' : ''}`}
                                                    >
                                                        <td className="text-center py-3.5 px-3">
                                                            <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-black ${pos === 1 ? 'bg-gold-500 text-dark-900' :
                                                                    pos === 2 ? 'bg-gray-400 text-dark-900' :
                                                                        pos === 3 ? 'bg-amber-700 text-white' :
                                                                            'bg-dark-800 text-gray-400'
                                                                }`}>
                                                                {pos}
                                                            </span>
                                                        </td>
                                                        <td className="py-3.5 px-3">
                                                            <div className="flex items-center gap-2.5">
                                                                <Shield size={14} className={`flex-shrink-0 ${isTop ? 'text-green-400' : isBottom ? 'text-red-400' : 'text-gray-600'}`} />
                                                                <span className="text-white font-bold text-sm truncate">{equipo.equipo}</span>
                                                            </div>
                                                        </td>
                                                        <td className="text-center py-3.5 px-2 text-gray-400 hidden sm:table-cell">{equipo.pj || 0}</td>
                                                        <td className="text-center py-3.5 px-2 text-green-400 font-semibold hidden sm:table-cell">{equipo.pg || 0}</td>
                                                        <td className="text-center py-3.5 px-2 text-yellow-400 hidden sm:table-cell">{equipo.pe || 0}</td>
                                                        <td className="text-center py-3.5 px-2 text-red-400 hidden sm:table-cell">{equipo.pp || 0}</td>
                                                        <td className="text-center py-3.5 px-2 text-gray-400 hidden md:table-cell">{equipo.gf || 0}</td>
                                                        <td className="text-center py-3.5 px-2 text-gray-400 hidden md:table-cell">{equipo.gc || 0}</td>
                                                        <td className="text-center py-3.5 px-2">
                                                            <span className={`font-bold ${(equipo.dif || 0) > 0 ? 'text-green-400' :
                                                                    (equipo.dif || 0) < 0 ? 'text-red-400' : 'text-gray-500'
                                                                }`}>
                                                                {(equipo.dif || 0) > 0 ? '+' : ''}{equipo.dif || 0}
                                                            </span>
                                                        </td>
                                                        <td className="text-center py-3.5 px-3">
                                                            <span className="text-white font-black text-base">{equipo.pts || 0}</span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="p-10 text-center">
                                    <Trophy className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                                    <p className="text-gray-500">Aún no hay partidos registrados.</p>
                                    <p className="text-gray-600 text-sm mt-1">La tabla se llenará cuando se jueguen partidos.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ===== SIDE PANEL (1/3) ===== */}
                    <div className="space-y-6">

                        {/* Últimos Resultados */}
                        <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                            <div className="p-5 pb-3 border-b border-white/5">
                                <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-sm uppercase tracking-widest">
                                    <Target size={16} /> Últimos Resultados
                                </h3>
                            </div>
                            <div className="p-4">
                                {ultimos_resultados.length > 0 ? (
                                    <div className="space-y-2.5">
                                        {ultimos_resultados.map((r, idx) => (
                                            <div key={idx} className="bg-dark-800/60 border border-white/[0.04] rounded-xl p-3 flex items-center justify-between hover:border-white/10 transition-all">
                                                <div className="flex-1 text-right">
                                                    <span className="text-white font-bold text-xs truncate">{r.equipo_local}</span>
                                                </div>
                                                <div className="px-3 flex items-center gap-1.5">
                                                    <span className={`text-base font-black ${(r.goles_local || 0) > (r.goles_visitante || 0) ? 'text-green-400' : (r.goles_local || 0) < (r.goles_visitante || 0) ? 'text-red-400' : 'text-gray-400'}`}>
                                                        {r.goles_local}
                                                    </span>
                                                    <span className="text-gray-600 text-xs">-</span>
                                                    <span className={`text-base font-black ${(r.goles_visitante || 0) > (r.goles_local || 0) ? 'text-green-400' : (r.goles_visitante || 0) < (r.goles_local || 0) ? 'text-red-400' : 'text-gray-400'}`}>
                                                        {r.goles_visitante}
                                                    </span>
                                                </div>
                                                <div className="flex-1 text-left">
                                                    <span className="text-white font-bold text-xs truncate">{r.equipo_visitante}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-600 text-sm text-center py-4">Sin resultados aún</p>
                                )}
                            </div>
                        </div>

                        {/* Próximos Partidos */}
                        {partidos_pendientes.length > 0 && (
                            <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                                <div className="p-5 pb-3 border-b border-white/5">
                                    <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-sm uppercase tracking-widest">
                                        <Calendar size={16} /> Próximos Partidos
                                    </h3>
                                </div>
                                <div className="p-4 space-y-2.5">
                                    {partidos_pendientes.map((p, idx) => (
                                        <div key={idx} className="bg-dark-800/60 border border-white/[0.04] rounded-xl p-3">
                                            <div className="flex items-center justify-between mb-1.5">
                                                <span className="text-white font-bold text-xs">{p.equipo_local}</span>
                                                <span className="text-gray-500 text-[10px] font-bold uppercase">vs</span>
                                                <span className="text-white font-bold text-xs">{p.equipo_visitante}</span>
                                            </div>
                                            <div className="text-center">
                                                <span className="text-[10px] text-gray-600 font-mono">
                                                    {p.fecha_hora ? new Date(p.fecha_hora).toLocaleDateString() : 'TBD'}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Top Jugadores */}
                        <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                            <div className="p-5 pb-3 border-b border-white/5">
                                <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-sm uppercase tracking-widest">
                                    <DollarSign size={16} /> Jugadores Más Caros
                                </h3>
                            </div>
                            <div className="p-4">
                                {top_jugadores.length > 0 ? (
                                    <div className="space-y-2">
                                        {top_jugadores.map((j, idx) => {
                                            const pos = getPosConfig(j.posicion);
                                            const precio = j.precio || j.clausula || 0;
                                            return (
                                                <div key={idx} className="flex items-center gap-3 p-2.5 rounded-xl bg-dark-800/40 hover:bg-dark-800 transition-all group">
                                                    <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-black ${idx === 0 ? 'bg-gold-500 text-dark-900' :
                                                            idx === 1 ? 'bg-gray-400 text-dark-900' :
                                                                idx === 2 ? 'bg-amber-700 text-white' :
                                                                    'bg-dark-800 text-gray-500'
                                                        }`}>
                                                        {idx + 1}
                                                    </span>
                                                    <img
                                                        src={j.avatar_url || `https://cdn.discordapp.com/embed/avatars/${idx % 5}.png`}
                                                        alt={j.nombre}
                                                        className="w-8 h-8 rounded-full border border-dark-700 object-cover"
                                                    />
                                                    <div className="flex-1 min-w-0">
                                                        <span className="text-white font-bold text-xs truncate block">{j.nombre}</span>
                                                        <div className="flex items-center gap-1.5">
                                                            <span className={`text-[9px] font-bold ${pos.color}`}>{j.posicion || '?'}</span>
                                                            {j.equipo && (
                                                                <>
                                                                    <span className="text-gray-700">•</span>
                                                                    <span className="text-[9px] text-gray-500 truncate">{j.equipo}</span>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <span className="text-gold-500 font-black text-xs">
                                                        ${precio >= 1000 ? `${(precio / 1000).toFixed(0)}K` : precio}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="text-gray-600 text-sm text-center py-4">Sin datos</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ===== BOTTOM SECTION: Rankings + Actividad ===== */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* Ranking de Equipos */}
                    <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                        <div className="p-6 pb-4 border-b border-white/5">
                            <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-sm uppercase tracking-widest">
                                <Shield size={16} /> Ranking de Equipos
                            </h3>
                        </div>
                        <div className="p-5">
                            {equipos_ranking.length > 0 ? (
                                <div className="space-y-3">
                                    {equipos_ranking.map((eq, idx) => (
                                        <div key={idx} className="flex items-center gap-4 p-3 rounded-xl bg-dark-800/40 hover:bg-dark-800 transition-all">
                                            <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-black ${idx === 0 ? 'bg-gold-500 text-dark-900' :
                                                    idx === 1 ? 'bg-gray-400 text-dark-900' :
                                                        idx === 2 ? 'bg-amber-700 text-white' :
                                                            'bg-dark-800 text-gray-500'
                                                }`}>
                                                {idx + 1}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <span className="text-white font-bold text-sm truncate block">{eq.nombre}</span>
                                                <div className="flex items-center gap-3 mt-0.5">
                                                    <span className="text-[10px] text-gray-500">
                                                        <Users size={10} className="inline mr-1" />{eq.total_jugadores}
                                                    </span>
                                                    <span className="text-[10px] text-gray-500">
                                                        💰 ${eq.presupuesto >= 1000 ? `${(eq.presupuesto / 1000).toFixed(0)}K` : eq.presupuesto}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-gold-500 font-black text-sm block">
                                                    ${eq.valor_plantilla >= 1000 ? `${(eq.valor_plantilla / 1000).toFixed(0)}K` : eq.valor_plantilla}
                                                </span>
                                                <span className="text-[9px] text-gray-600 uppercase tracking-widest">Valor</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-600 text-sm text-center py-4">Sin equipos registrados</p>
                            )}
                        </div>
                    </div>

                    {/* Feed de Actividad */}
                    <div className="bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden">
                        <div className="p-6 pb-4 border-b border-white/5">
                            <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-sm uppercase tracking-widest">
                                <Activity size={16} /> Actividad Reciente
                            </h3>
                        </div>
                        <div className="p-5">
                            {actividad_reciente.length > 0 ? (
                                <div className="space-y-2.5 relative">
                                    <div className="absolute left-[15px] top-4 bottom-4 w-0.5 bg-gradient-to-b from-gold-500/20 via-white/5 to-transparent" />

                                    {actividad_reciente.map((event, idx) => {
                                        const cfg = getActionConfig(event.action_type);
                                        return (
                                            <div key={idx} className="relative pl-10 group">
                                                <div className={`absolute left-[9px] top-2.5 w-3.5 h-3.5 rounded-full border-2 border-dark-900 z-10 ${cfg.bg} flex items-center justify-center`}>
                                                    <span className="text-[8px]">{cfg.icon}</span>
                                                </div>

                                                <div className={`p-3 rounded-xl border ${cfg.border} ${cfg.bg} hover:bg-opacity-20 transition-all`}>
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="min-w-0">
                                                            <span className={`text-xs font-bold ${cfg.color}`}>{cfg.label}</span>
                                                            <p className="text-white text-xs font-medium mt-0.5 truncate">
                                                                {event.target_name || event.actor_name}
                                                                {event.details?.equipo && (
                                                                    <span className="text-gray-400"> → {event.details.equipo}</span>
                                                                )}
                                                            </p>
                                                        </div>
                                                        <span className="text-[9px] text-gray-600 font-mono flex-shrink-0">
                                                            {event.timestamp ? new Date(event.timestamp).toLocaleDateString() : ''}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="py-8 text-center">
                                    <Activity className="w-10 h-10 text-gray-700 mx-auto mb-3" />
                                    <p className="text-gray-500 text-sm">Sin actividad registrada aún.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Estadisticas;
