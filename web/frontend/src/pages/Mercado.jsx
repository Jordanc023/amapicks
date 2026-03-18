import React, { useState, useEffect, useMemo } from 'react';
import { Search, Shield, User, Loader2, DollarSign, Users, TrendingUp, Zap, Crown, ChevronRight, BarChart3 } from 'lucide-react';
import { ligaService } from '../services/api';
import ProfileModal from '../components/ProfileModal';

const getPosConfig = (pos) => {
    switch (pos) {
        case 'GK': return { label: 'GK', color: 'text-yellow-400', bg: 'bg-yellow-500', border: 'border-yellow-500/30', bgSoft: 'bg-yellow-500/10', gradient: 'from-yellow-500/20 via-yellow-600/5 to-transparent' };
        case 'DEF': return { label: 'DEF', color: 'text-blue-400', bg: 'bg-blue-500', border: 'border-blue-500/30', bgSoft: 'bg-blue-500/10', gradient: 'from-blue-500/20 via-blue-600/5 to-transparent' };
        case 'MC': return { label: 'MC', color: 'text-green-400', bg: 'bg-green-500', border: 'border-green-500/30', bgSoft: 'bg-green-500/10', gradient: 'from-green-500/20 via-green-600/5 to-transparent' };
        case 'DC': return { label: 'DC', color: 'text-red-400', bg: 'bg-red-500', border: 'border-red-500/30', bgSoft: 'bg-red-500/10', gradient: 'from-red-500/20 via-red-600/5 to-transparent' };
        default: return { label: '?', color: 'text-gray-400', bg: 'bg-gray-500', border: 'border-gray-500/30', bgSoft: 'bg-gray-500/10', gradient: 'from-gray-500/20 via-gray-600/5 to-transparent' };
    }
};

const PlayerCard = ({ player, onClick }) => {
    const pos = getPosConfig(player.posicion);
    const precio = player.precio || player.clausula || 0;
    const rating = player.rating || Math.min(99, Math.floor(60 + (precio / 5000)));

    return (
        <div
            onClick={onClick}
            className="group relative bg-dark-800 border border-white/[0.06] rounded-2xl overflow-hidden cursor-pointer hover:border-gold-500/30 transition-all duration-500 hover:shadow-2xl hover:shadow-gold-500/5 hover:-translate-y-1"
        >
            {/* Top gradient accent */}
            <div className={`absolute top-0 left-0 right-0 h-24 bg-gradient-to-b ${pos.gradient} opacity-60`} />

            {/* Content */}
            <div className="relative p-5">
                {/* Header: Avatar + Info */}
                <div className="flex items-start gap-4 mb-4">
                    {/* Avatar */}
                    <div className="relative flex-shrink-0">
                        <div className={`absolute -inset-1 rounded-full ${pos.bg} opacity-20 blur-lg group-hover:opacity-40 transition-opacity`} />
                        <img
                            src={player.avatar_url || "https://cdn.discordapp.com/embed/avatars/0.png"}
                            alt={player.nombre}
                            className="w-16 h-16 rounded-full object-cover border-2 border-dark-700 relative z-10 group-hover:border-gold-500/40 transition-colors"
                        />
                        {/* Rating badge */}
                        <div className="absolute -bottom-1 -right-1 z-20 w-7 h-7 rounded-full bg-dark-900 border border-white/10 flex items-center justify-center">
                            <span className="text-[10px] font-black text-gold-500">{rating}</span>
                        </div>
                    </div>

                    {/* Name & Tags */}
                    <div className="flex-1 min-w-0 pt-1">
                        <h3 className="text-white font-bold text-base truncate group-hover:text-gold-400 transition-colors">
                            {player.nombre || player.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1.5">
                            <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border uppercase tracking-widest ${pos.color} ${pos.bgSoft} ${pos.border}`}>
                                {pos.label}
                            </span>
                            {player.es_dt && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gold-500/10 border border-gold-500/30 text-gold-500 flex items-center gap-0.5">
                                    <Crown size={8} /> DT
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Team / Status */}
                <div className="flex items-center justify-between mb-4">
                    {player.equipo ? (
                        <div className="flex items-center gap-2">
                            <Shield size={12} className="text-gray-500" />
                            <span className="text-xs text-gray-400 font-medium truncate max-w-[140px]">{player.equipo}</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-xs text-green-400 font-bold uppercase tracking-wider">Agente Libre</span>
                        </div>
                    )}
                    {player.dorsal && (
                        <span className="text-xs text-gray-600 font-mono">#{player.dorsal}</span>
                    )}
                </div>

                {/* Price Bar */}
                <div className="bg-dark-900/80 border border-white/5 rounded-xl p-3 flex items-center justify-between group-hover:border-gold-500/20 transition-colors">
                    <div className="flex items-center gap-2">
                        <DollarSign size={14} className="text-gold-500" />
                        <span className="text-gold-500 font-black text-lg">
                            {precio >= 1000000 ? `${(precio / 1000000).toFixed(1)}M` :
                                precio >= 1000 ? `${(precio / 1000).toFixed(0)}K` : precio}
                        </span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-500 group-hover:text-gold-500 transition-colors">
                        <span className="text-[10px] font-bold uppercase tracking-widest">Ver perfil</span>
                        <ChevronRight size={12} />
                    </div>
                </div>
            </div>
        </div>
    );
};

const Mercado = () => {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('todos');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedPlayerId, setSelectedPlayerId] = useState(null);
    const [mercadoStatus, setMercadoStatus] = useState(null);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const [data, status] = await Promise.all([
                    ligaService.getJugadores('todos'),
                    ligaService.getMercadoStatus()
                ]);
                setPlayers(data);
                setMercadoStatus(status);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    // Map filter keys → BD values
    const posMap = { portero: 'GK', defensa: 'DEF', medio: 'MC', delantero: 'DC' };

    // Filtered + searched players
    const filteredPlayers = useMemo(() => {
        return players.filter(p => {
            const matchPos = filter === 'todos' || p.posicion === posMap[filter];
            const matchSearch = !searchQuery ||
                (p.nombre || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                (p.equipo || '').toLowerCase().includes(searchQuery.toLowerCase());
            return matchPos && matchSearch;
        });
    }, [players, filter, searchQuery]);

    // Stats
    const totalJugadores = players.length;
    const agentesLibres = players.filter(p => !p.equipo).length;
    const valorTotal = players.reduce((sum, p) => sum + (p.precio || p.clausula || 0), 0);
    const posCount = (pos) => players.filter(p => p.posicion === pos).length;

    const categories = [
        { id: 'todos', label: 'Todos', count: totalJugadores },
        { id: 'portero', label: 'GK', count: posCount('GK'), emoji: '🧤' },
        { id: 'defensa', label: 'DEF', count: posCount('DEF'), emoji: '🛡️' },
        { id: 'medio', label: 'MC', count: posCount('MC'), emoji: '⚙️' },
        { id: 'delantero', label: 'DC', count: posCount('DC'), emoji: '⚽' },
    ];

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 min-h-screen pb-20 px-4 sm:px-6 pt-6">
            {/* Modal Perfil */}
            {selectedPlayerId && (
                <ProfileModal
                    discordId={selectedPlayerId}
                    onClose={() => setSelectedPlayerId(null)}
                />
            )}

            {/* ===== HEADER ===== */}
            <div className="max-w-7xl mx-auto mb-10">
                <div className="relative">
                    {/* Background glow */}
                    <div className="absolute -inset-4 bg-gradient-to-r from-gold-500/5 via-transparent to-gold-500/5 rounded-3xl blur-2xl" />

                    <div className="relative flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-10 h-10 bg-gold-500/10 border border-gold-500/30 rounded-xl flex items-center justify-center">
                                    <BarChart3 size={20} className="text-gold-500" />
                                </div>
                                {mercadoStatus && (
                                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest border ${mercadoStatus.abierto
                                            ? 'bg-green-500/10 border-green-500/30 text-green-400'
                                            : 'bg-red-500/10 border-red-500/30 text-red-400'
                                        }`}>
                                        <div className={`w-2 h-2 rounded-full ${mercadoStatus.abierto ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                                        {mercadoStatus.abierto ? 'Mercado Abierto' : 'Mercado Cerrado'}
                                    </div>
                                )}
                            </div>
                            <h1 className="text-4xl sm:text-5xl font-display font-black text-white uppercase tracking-tight mb-2">
                                Mercado de <span className="text-gold-500">Fichajes</span>
                            </h1>
                            <p className="text-gray-400 max-w-lg text-sm sm:text-base">
                                Explora los talentos disponibles y refuerza tu plantilla. Los fichajes se realizan vía Discord.
                            </p>
                        </div>

                        {/* Search Bar */}
                        <div className="relative w-full lg:w-auto">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Buscar jugador o equipo..."
                                className="w-full lg:w-80 bg-dark-800 border border-white/10 rounded-xl py-3.5 pl-12 pr-6 text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/30 transition-all text-sm"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors text-xs font-bold"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== STATS BANNER ===== */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 group hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                            <Users size={18} className="text-blue-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{totalJugadores}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Jugadores</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 group hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                            <Zap size={18} className="text-green-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{agentesLibres}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Libres</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 group hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-gold-500/10 flex items-center justify-center">
                            <DollarSign size={18} className="text-gold-500" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">
                                ${valorTotal >= 1000000 ? `${(valorTotal / 1000000).toFixed(1)}M` :
                                    valorTotal >= 1000 ? `${(valorTotal / 1000).toFixed(0)}K` : valorTotal}
                            </span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Valor Total</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 group hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                            <TrendingUp size={18} className="text-purple-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{filteredPlayers.length}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Resultados</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== FILTERS ===== */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="flex flex-wrap gap-2">
                    {categories.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => setFilter(cat.id)}
                            className={`px-5 py-2.5 rounded-xl font-bold text-sm tracking-wide transition-all duration-300 border flex items-center gap-2 ${filter === cat.id
                                ? 'bg-gold-500 text-dark-900 border-gold-500 shadow-lg shadow-gold-500/20'
                                : 'bg-dark-800 text-gray-400 border-white/5 hover:bg-dark-700 hover:text-white hover:border-white/10'
                                }`}
                        >
                            {cat.emoji && <span className="text-sm">{cat.emoji}</span>}
                            {cat.label}
                            <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-full ${filter === cat.id ? 'bg-dark-900/30 text-dark-900' : 'bg-white/5 text-gray-500'}`}>
                                {cat.count}
                            </span>
                        </button>
                    ))}
                </div>
            </div>

            {/* ===== PLAYERS GRID ===== */}
            <div className="max-w-7xl mx-auto">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 gap-4">
                        <Loader2 className="w-10 h-10 text-gold-500 animate-spin" />
                        <span className="text-gray-500 text-sm font-medium">Cargando mercado...</span>
                    </div>
                ) : filteredPlayers.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {filteredPlayers.map((player, idx) => (
                            <PlayerCard
                                key={player.discord_id || idx}
                                player={player}
                                onClick={() => setSelectedPlayerId(player.discord_id)}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-dark-800/30 rounded-3xl border border-white/5 border-dashed">
                        <User className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-gray-400 mb-2">No se encontraron jugadores</h3>
                        <p className="text-gray-500 text-sm mb-4">
                            {searchQuery ? `Sin resultados para "${searchQuery}"` : 'Intenta cambiar los filtros.'}
                        </p>
                        {(searchQuery || filter !== 'todos') && (
                            <button
                                onClick={() => { setSearchQuery(''); setFilter('todos'); }}
                                className="px-5 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:bg-white/10 transition-all font-semibold"
                            >
                                Limpiar filtros
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Mercado;
