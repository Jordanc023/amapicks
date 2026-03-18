import React from 'react';
import { X, Shield, Users, DollarSign, Crown, ChevronRight, Zap } from 'lucide-react';

const getPosConfig = (pos) => {
    switch (pos) {
        case 'GK': return { label: 'Portero', short: 'GK', color: 'text-yellow-400', bg: 'bg-yellow-500', bgSoft: 'bg-yellow-500/10', border: 'border-yellow-500/30' };
        case 'DEF': return { label: 'Defensa', short: 'DEF', color: 'text-blue-400', bg: 'bg-blue-500', bgSoft: 'bg-blue-500/10', border: 'border-blue-500/30' };
        case 'MC': return { label: 'Medio', short: 'MC', color: 'text-green-400', bg: 'bg-green-500', bgSoft: 'bg-green-500/10', border: 'border-green-500/30' };
        case 'DC': return { label: 'Delantero', short: 'DC', color: 'text-red-400', bg: 'bg-red-500', bgSoft: 'bg-red-500/10', border: 'border-red-500/30' };
        default: return { label: 'Jugador', short: '?', color: 'text-gray-400', bg: 'bg-gray-500', bgSoft: 'bg-gray-500/10', border: 'border-gray-500/30' };
    }
};

const TeamModal = ({ team, onClose, onPlayerClick }) => {
    if (!team) return null;

    const plantilla = team.plantilla || [];
    const totalJugadores = plantilla.length;
    const rawName = team.nombre || team.role_name || 'Equipo';
    const teamName = rawName.replace(/^-+\s*/, '');
    const presupuesto = team.presupuesto || 0;
    const valorPlantilla = plantilla.reduce((sum, j) => sum + (j.precio || 0), 0);

    // Group by position
    const posGroups = [
        { pos: 'GK', label: '🧤 Porteros', players: plantilla.filter(p => p.posicion === 'GK') },
        { pos: 'DEF', label: '🛡️ Defensas', players: plantilla.filter(p => p.posicion === 'DEF') },
        { pos: 'MC', label: '⚙️ Mediocampistas', players: plantilla.filter(p => p.posicion === 'MC') },
        { pos: 'DC', label: '⚽ Delanteros', players: plantilla.filter(p => p.posicion === 'DC') },
        { pos: null, label: '❓ Sin posición', players: plantilla.filter(p => !p.posicion || !['GK', 'DEF', 'MC', 'DC'].includes(p.posicion)) },
    ].filter(g => g.players.length > 0);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/85 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative w-full max-w-5xl bg-dark-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row animate-in fade-in zoom-in duration-300 max-h-[90vh]">

                {/* Close */}
                <button onClick={onClose} className="absolute top-4 right-4 z-50 p-2.5 rounded-full bg-dark-800 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                    <X size={18} />
                </button>

                {/* ===== LEFT: Team Identity ===== */}
                <div className="w-full md:w-[320px] flex-shrink-0 p-8 flex flex-col items-center justify-center relative overflow-hidden border-b md:border-b-0 md:border-r border-white/5">
                    {/* Background */}
                    <div className="absolute inset-0 opacity-[0.03]" style={{
                        backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 30px, rgba(212,175,55,0.3) 30px, rgba(212,175,55,0.3) 31px)`
                    }} />
                    <div className="absolute inset-0 bg-gradient-to-b from-gold-500/5 via-transparent to-dark-950" />

                    {/* Shield */}
                    <div className="relative w-32 h-32 mb-6 z-10">
                        <div className="absolute inset-0 bg-gold-500/20 blur-3xl rounded-full animate-pulse" />
                        <div className="w-full h-full rounded-2xl bg-gradient-to-br from-dark-800 to-dark-950 flex items-center justify-center border border-white/10 shadow-2xl relative z-10">
                            <Shield className="w-16 h-16 text-gold-500" />
                        </div>
                    </div>

                    {/* Name */}
                    <h2 className="text-2xl sm:text-3xl font-display font-black text-white text-center uppercase tracking-tight mb-1 relative z-10">
                        {teamName}
                    </h2>
                    <div className="flex items-center gap-2 text-gray-500 text-sm mb-6 relative z-10">
                        <Users size={14} />
                        <span>{totalJugadores}/12 Jugadores</span>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-3 w-full relative z-10 mb-6">
                        <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 text-center hover:border-gold-500/20 transition-colors">
                            <DollarSign size={14} className="text-gold-500 mx-auto mb-1" />
                            <span className="block text-gold-500 font-black text-lg leading-none">
                                {presupuesto >= 1000 ? `${(presupuesto / 1000).toFixed(0)}K` : presupuesto}
                            </span>
                            <span className="block text-[9px] text-gray-500 uppercase tracking-widest mt-1">Presupuesto</span>
                        </div>
                        <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 text-center hover:border-gold-500/20 transition-colors">
                            <Zap size={14} className="text-purple-400 mx-auto mb-1" />
                            <span className="block text-white font-black text-lg leading-none">
                                {valorPlantilla >= 1000 ? `${(valorPlantilla / 1000).toFixed(0)}K` : valorPlantilla}
                            </span>
                            <span className="block text-[9px] text-gray-500 uppercase tracking-widest mt-1">Val. Plantilla</span>
                        </div>
                    </div>

                    {/* Position Breakdown */}
                    <div className="w-full relative z-10">
                        <div className="bg-dark-800/60 border border-white/5 rounded-xl p-3">
                            <span className="block text-[9px] text-gray-500 uppercase tracking-widest mb-2 text-center">Distribución</span>
                            <div className="flex items-center gap-1">
                                {['GK', 'DEF', 'MC', 'DC'].map(pos => {
                                    const count = plantilla.filter(p => p.posicion === pos).length;
                                    const cfg = getPosConfig(pos);
                                    return (
                                        <div key={pos} className="flex-1 text-center">
                                            <div className={`w-full h-1.5 rounded-full mb-1.5 ${count > 0 ? cfg.bg : 'bg-dark-700'} transition-colors`}
                                                style={{ opacity: count > 0 ? Math.min(1, 0.3 + (count * 0.25)) : 0.2 }}
                                            />
                                            <span className={`text-[10px] font-black ${count > 0 ? cfg.color : 'text-gray-700'}`}>
                                                {count}
                                            </span>
                                            <span className="block text-[8px] text-gray-600 uppercase">{pos}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ===== RIGHT: Squad List ===== */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {/* Sticky header */}
                    <div className="sticky top-0 bg-dark-900/95 backdrop-blur-xl z-20 px-8 pt-8 pb-4 border-b border-white/5">
                        <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-lg uppercase tracking-widest">
                            <Users size={20} /> Plantilla Oficial
                        </h3>
                    </div>

                    <div className="p-8 pt-4">
                        {plantilla.length > 0 ? (
                            <div className="space-y-6">
                                {posGroups.map((group) => (
                                    <div key={group.pos || 'none'}>
                                        {/* Section header */}
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className="text-sm font-bold text-gray-400">{group.label}</span>
                                            <div className="flex-1 h-px bg-white/5" />
                                            <span className="text-xs text-gray-600 font-mono">{group.players.length}</span>
                                        </div>

                                        {/* Player cards */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
                                            {group.players.map((jugador, idx) => {
                                                const posConf = getPosConfig(jugador.posicion);
                                                const precio = jugador.precio || jugador.clausula || 0;
                                                return (
                                                    <div
                                                        key={idx}
                                                        className="flex items-center gap-3.5 p-3.5 rounded-xl bg-dark-800/60 border border-white/[0.04] hover:bg-dark-800 hover:border-gold-500/20 cursor-pointer transition-all group"
                                                        onClick={() => onPlayerClick(jugador.discord_id)}
                                                    >
                                                        {/* Avatar */}
                                                        <div className="relative flex-shrink-0">
                                                            <img
                                                                src={jugador.avatar_url || `https://cdn.discordapp.com/embed/avatars/${idx % 5}.png`}
                                                                alt={jugador.nombre}
                                                                className="w-11 h-11 rounded-full border-2 border-dark-700 object-cover group-hover:border-gold-500/40 transition-colors"
                                                            />
                                                            <div className={`absolute -bottom-0.5 -right-0.5 w-4.5 h-4.5 rounded-full flex items-center justify-center text-[7px] font-black border-2 border-dark-800 ${posConf.bg} text-white`}>
                                                                {posConf.short[0]}
                                                            </div>
                                                            {jugador.es_dt && (
                                                                <div className="absolute -top-1 -left-1 w-4 h-4 bg-gold-500 rounded-full flex items-center justify-center border border-dark-800">
                                                                    <Crown size={8} className="text-black" />
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Info */}
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-white font-bold text-sm truncate group-hover:text-gold-400 transition-colors">
                                                                    {jugador.nombre}
                                                                </span>
                                                                {jugador.dorsal && (
                                                                    <span className="text-[10px] text-gray-600 font-mono">#{jugador.dorsal}</span>
                                                                )}
                                                            </div>
                                                            <div className="flex items-center gap-2 mt-0.5">
                                                                <span className={`text-[10px] font-bold ${posConf.color}`}>{posConf.label}</span>
                                                                {precio > 0 && (
                                                                    <>
                                                                        <span className="text-gray-700">•</span>
                                                                        <span className="text-[10px] text-gold-500/70 font-bold">
                                                                            ${precio >= 1000 ? `${(precio / 1000).toFixed(0)}K` : precio}
                                                                        </span>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Arrow */}
                                                        <ChevronRight size={14} className="text-gray-700 group-hover:text-gold-500 transition-colors flex-shrink-0" />
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="py-16 text-center">
                                <Users className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                                <p className="text-gray-500 mb-1">Plantilla vacía</p>
                                <p className="text-gray-600 text-sm">
                                    Este equipo aún no tiene jugadores fichados.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TeamModal;
