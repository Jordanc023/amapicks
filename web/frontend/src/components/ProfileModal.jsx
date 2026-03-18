import React, { useEffect, useState } from 'react';
import { X, TrendingUp, DollarSign } from 'lucide-react';
import { ligaService } from '../services/api';

const ProfileModal = ({ discordId, onClose }) => {
    const [player, setPlayer] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await ligaService.getJugadorDetalle(discordId);
                setPlayer(data);
            } catch (error) {
                console.error("Error loading profile:", error);
            } finally {
                setLoading(false);
            }
        };
        if (discordId) load();
    }, [discordId]);

    if (!discordId) return null;

    const getPosColor = (pos) => {
        switch (pos) {
            case 'GK': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            case 'DEF': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
            case 'MC': return 'text-green-500 bg-green-500/10 border-green-500/20';
            case 'DC': return 'text-red-500 bg-red-500/10 border-red-500/20';
            default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
        }
    };

    const precio = player?.precio || player?.clausula || 0;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

            {/* Modal Content */}
            <div className="relative w-full max-w-4xl bg-dark-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row animate-in fade-in zoom-in duration-300">

                {/* Close Button */}
                <button onClick={onClose} className="absolute top-4 right-4 z-50 p-2 rounded-full bg-black/40 text-white hover:bg-white/20 transition-colors">
                    <X size={20} />
                </button>

                {loading ? (
                    <div className="w-full h-96 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500" />
                    </div>
                ) : player ? (
                    <>
                        {/* Left Side: Player Card & Visuals */}
                        <div className="w-full md:w-1/3 bg-gradient-to-br from-dark-800 to-dark-950 p-8 flex flex-col items-center justify-center relative border-r border-white/5">
                            {/* Dorsal Background */}
                            <span className="absolute top-10 text-[12rem] font-display font-black text-white/5 leading-none select-none">
                                {player.dorsal || '??'}
                            </span>

                            {/* Avatar */}
                            <div className="relative w-48 h-48 mb-6 z-10 group">
                                <div className={`absolute inset-0 rounded-full blur-2xl opacity-50 ${getPosColor(player.posicion).split(' ')[0].replace('text-', 'bg-')}`} />
                                <img
                                    src={player.avatar_url}
                                    alt={player.nombre}
                                    className="w-full h-full object-cover rounded-full border-4 border-dark-800 shadow-xl relative z-10 group-hover:scale-105 transition-transform duration-500"
                                />
                                <div className="absolute bottom-2 right-2 z-20 px-3 py-1 bg-dark-900 rounded-full border border-white/10 flex items-center gap-2 shadow-lg">
                                    <div className={`w-2 h-2 rounded-full ${player.equipo ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                                    <span className="text-xs font-bold text-white uppercase">{player.equipo ? 'Activo' : 'Libre'}</span>
                                </div>
                            </div>

                            {/* Info */}
                            <h2 className="text-3xl font-display font-black text-white text-center uppercase tracking-tight mb-1 relative z-10">
                                {player.nombre}
                            </h2>
                            <div className={`px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest border mb-4 relative z-10 ${getPosColor(player.posicion)}`}>
                                {player.posicion || 'SIN POS'}
                            </div>

                            {/* Equipo actual */}
                            {player.equipo && (
                                <div className="bg-dark-800 border border-white/10 rounded-xl px-4 py-2 mb-4 relative z-10 text-center">
                                    <span className="text-xs text-gray-400 uppercase tracking-widest">Equipo</span>
                                    <p className="text-white font-bold">{player.equipo}</p>
                                </div>
                            )}

                            {/* Stats */}
                            <div className="grid grid-cols-2 gap-4 w-full relative z-10">
                                <div className="col-span-2 bg-gradient-to-r from-gold-500/10 to-transparent border border-gold-500/20 rounded-xl p-4 text-center">
                                    <span className="block text-gold-400 font-bold text-xs uppercase tracking-widest mb-1">Valor de Mercado</span>
                                    <div className="flex items-center justify-center gap-1 text-gold-500 font-black text-2xl">
                                        <DollarSign size={20} />
                                        {new Intl.NumberFormat('en-US').format(precio)}
                                    </div>
                                </div>
                                {player.clausula && player.clausula !== precio && (
                                    <div className="col-span-2 bg-dark-800 border border-white/10 rounded-xl p-3 text-center">
                                        <span className="block text-gray-400 text-xs uppercase tracking-widest mb-1">Cláusula</span>
                                        <span className="text-white font-bold text-lg">${new Intl.NumberFormat('en-US').format(player.clausula)}</span>
                                    </div>
                                )}
                            </div>

                            {/* Info: Fichajes por Discord */}
                            <div className="w-full mt-6 relative z-10">
                                <div className="bg-[#5865F2]/10 border border-[#5865F2]/30 rounded-xl p-3 text-center">
                                    <span className="text-[#5865F2] text-xs font-bold uppercase tracking-widest">
                                        📨 Fichajes vía Discord
                                    </span>
                                    <p className="text-gray-400 text-xs mt-1">
                                        Usa <code className="text-white bg-dark-800 px-1.5 py-0.5 rounded">/fichar</code> en el servidor
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Right Side: Details & History */}
                        <div className="w-full md:w-2/3 p-8 bg-dark-900 overflow-y-auto max-h-[80vh]">

                            {/* Section: Trayectoria */}
                            <div className="mb-8">
                                <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-lg uppercase tracking-widest mb-6">
                                    <TrendingUp size={20} /> Trayectoria Reciente
                                </h3>

                                <div className="space-y-6 relative ml-2">
                                    {/* Vertical Line */}
                                    <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-white/10" />

                                    {player.historial && player.historial.length > 0 ? (
                                        player.historial.slice().reverse().map((event, idx) => (
                                            <div key={idx} className="relative pl-8 flex flex-col">
                                                <div className={`absolute left-[5px] top-1.5 w-3 h-3 rounded-full border-2 border-dark-900 z-10 ${event.action_type === 'FICHAJE' ? 'bg-green-500' :
                                                    event.action_type === 'DESPIDO' ? 'bg-red-500' : 'bg-yellow-500'
                                                    }`} />

                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <span className={`text-xs font-bold px-2 py-0.5 rounded border mb-1 inline-block ${event.action_type === 'FICHAJE' ? 'text-green-400 border-green-500/30 bg-green-500/10' :
                                                            event.action_type === 'DESPIDO' ? 'text-red-400 border-red-500/30 bg-red-500/10' : 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                                            }`}>
                                                            {event.action_type}
                                                        </span>
                                                        <h4 className="text-white font-bold mt-1">
                                                            {event.details?.equipo_destino || event.details?.equipo || 'Agente Libre'}
                                                            {event.details?.precio && <span className="text-gold-500 ml-2 text-xs">(${new Intl.NumberFormat('en-US').format(event.details.precio)})</span>}
                                                        </h4>
                                                        <p className="text-sm text-gray-500">
                                                            {event.action_type === 'FICHAJE' ? `Fichado desde ${event.details?.equipo_origen || 'Libre'}` :
                                                                event.action_type === 'DESPIDO' ? 'Rescindido del contrato.' : 'Abandonó el equipo.'}
                                                        </p>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-xs text-gray-500 font-mono">
                                                            {new Date(event.timestamp).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="pl-8 text-gray-500 italic">Sin historial registrado recientemente.</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="w-full h-64 flex items-center justify-center text-red-500">
                        Error al cargar jugador
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProfileModal;
