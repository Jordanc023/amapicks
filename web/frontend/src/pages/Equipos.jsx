import React, { useState, useEffect } from 'react';
import { Shield, Users, DollarSign, TrendingUp, Crown, Loader2, BarChart3 } from 'lucide-react';
import { ligaService } from '../services/api';
import ProfileModal from '../components/ProfileModal';
import TeamModal from '../components/TeamModal';

const getPosConfig = (pos) => {
    switch (pos) {
        case 'GK': return { color: 'bg-yellow-500', text: 'text-yellow-400' };
        case 'DEF': return { color: 'bg-blue-500', text: 'text-blue-400' };
        case 'MC': return { color: 'bg-green-500', text: 'text-green-400' };
        case 'DC': return { color: 'bg-red-500', text: 'text-red-400' };
        default: return { color: 'bg-gray-500', text: 'text-gray-400' };
    }
};

const TeamCard = ({ equipo, onClick }) => {
    const totalJugadores = equipo.plantilla?.length || 0;
    const rawName = equipo.nombre || equipo.role_name || 'Equipo';
    const teamName = rawName.replace(/^-+\s*/, '');
    const presupuesto = equipo.presupuesto || 0;
    const valorPlantilla = equipo.plantilla?.reduce((sum, j) => sum + (j.precio || 0), 0) || 0;

    // Mini position breakdown bar
    const posBreakdown = [
        { pos: 'GK', count: equipo.plantilla?.filter(p => p.posicion === 'GK').length || 0 },
        { pos: 'DEF', count: equipo.plantilla?.filter(p => p.posicion === 'DEF').length || 0 },
        { pos: 'MC', count: equipo.plantilla?.filter(p => p.posicion === 'MC').length || 0 },
        { pos: 'DC', count: equipo.plantilla?.filter(p => p.posicion === 'DC').length || 0 },
    ];

    // Avatar stack (max 5)
    const avatares = (equipo.plantilla || []).slice(0, 5);

    return (
        <div
            onClick={onClick}
            className="group relative bg-dark-900 border border-white/[0.06] rounded-2xl overflow-hidden cursor-pointer hover:border-gold-500/30 transition-all duration-500 hover:shadow-2xl hover:shadow-gold-500/5 hover:-translate-y-1"
        >
            {/* Top gradient accent */}
            <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-gold-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Background pattern */}
            <div className="absolute inset-0 opacity-[0.02] group-hover:opacity-[0.04] transition-opacity" style={{
                backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 30px, rgba(212,175,55,0.3) 30px, rgba(212,175,55,0.3) 31px)`
            }} />

            <div className="relative p-6">
                {/* Header: Shield + Name */}
                <div className="flex items-center gap-4 mb-5">
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-dark-800 to-dark-950 flex items-center justify-center border border-white/10 shadow-xl group-hover:border-gold-500/30 group-hover:shadow-gold-500/10 transition-all duration-500 flex-shrink-0">
                        <Shield className="w-7 h-7 text-gray-500 group-hover:text-gold-500 transition-colors duration-500" />
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-xl font-display font-black text-white uppercase tracking-tight truncate group-hover:text-gold-100 transition-colors">
                            {teamName}
                        </h3>
                        <div className="flex items-center gap-3 mt-1">
                            <span className="text-xs text-gray-500 font-medium flex items-center gap-1">
                                <Users size={12} className="text-gray-600" /> {totalJugadores}/12
                            </span>
                            {presupuesto > 0 && (
                                <span className="text-xs text-gold-500/70 font-bold flex items-center gap-0.5">
                                    <DollarSign size={11} />{presupuesto >= 1000 ? `${(presupuesto / 1000).toFixed(0)}K` : presupuesto}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Avatar Stack */}
                {avatares.length > 0 && (
                    <div className="flex items-center mb-5">
                        <div className="flex -space-x-2.5">
                            {avatares.map((j, idx) => (
                                <img
                                    key={idx}
                                    src={j.avatar_url || `https://cdn.discordapp.com/embed/avatars/${idx % 5}.png`}
                                    alt={j.nombre}
                                    className="w-9 h-9 rounded-full border-2 border-dark-900 object-cover hover:z-10 hover:scale-110 transition-transform"
                                    title={j.nombre}
                                />
                            ))}
                            {totalJugadores > 5 && (
                                <div className="w-9 h-9 rounded-full border-2 border-dark-900 bg-dark-800 flex items-center justify-center">
                                    <span className="text-[10px] font-bold text-gray-400">+{totalJugadores - 5}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Position Breakdown Mini Bar */}
                <div className="flex items-center gap-1 mb-4">
                    {posBreakdown.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 flex-1">
                            <div className={`w-2 h-2 rounded-full ${getPosConfig(item.pos).color} ${item.count === 0 ? 'opacity-20' : 'opacity-100'}`} />
                            <span className="text-[10px] text-gray-600 font-bold uppercase">{item.pos}</span>
                            <span className={`text-[10px] font-black ${item.count > 0 ? 'text-white' : 'text-gray-700'}`}>{item.count}</span>
                        </div>
                    ))}
                </div>

                {/* Footer: Value + CTA */}
                <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 flex items-center justify-between group-hover:border-gold-500/20 transition-colors">
                    <div>
                        <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Valor Plantilla</span>
                        <span className="text-gold-500 font-black text-base">
                            ${valorPlantilla >= 1000 ? `${(valorPlantilla / 1000).toFixed(0)}K` : valorPlantilla}
                        </span>
                    </div>
                    <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest group-hover:text-gold-500 transition-colors flex items-center gap-1">
                        Ver equipo →
                    </div>
                </div>
            </div>
        </div>
    );
};

const Equipos = () => {
    const [equipos, setEquipos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTeam, setSelectedTeam] = useState(null);
    const [selectedPlayerId, setSelectedPlayerId] = useState(null);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await ligaService.getEquipos();
                setEquipos(data);
            } catch (error) {
                console.error("Error cargando equipos", error);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    // Stats
    const totalEquipos = equipos.length;
    const totalJugadores = equipos.reduce((sum, e) => sum + (e.plantilla?.length || 0), 0);
    const valorTotal = equipos.reduce((sum, e) =>
        sum + (e.plantilla?.reduce((s, j) => s + (j.precio || 0), 0) || 0)
        , 0);

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 min-h-screen pb-20 px-4 sm:px-6 pt-6">
            {/* Modal Perfil Jugador */}
            {selectedPlayerId && (
                <ProfileModal
                    discordId={selectedPlayerId}
                    onClose={() => setSelectedPlayerId(null)}
                />
            )}

            {/* Modal Detalle Equipo */}
            {selectedTeam && (
                <TeamModal
                    team={selectedTeam}
                    onClose={() => setSelectedTeam(null)}
                    onPlayerClick={(pid) => setSelectedPlayerId(pid)}
                />
            )}

            {/* ===== HEADER ===== */}
            <div className="max-w-7xl mx-auto mb-10">
                <div className="relative">
                    <div className="absolute -inset-4 bg-gradient-to-r from-gold-500/5 via-transparent to-gold-500/5 rounded-3xl blur-2xl" />
                    <div className="relative flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-10 h-10 bg-gold-500/10 border border-gold-500/30 rounded-xl flex items-center justify-center">
                                    <Shield size={20} className="text-gold-500" />
                                </div>
                            </div>
                            <h1 className="text-4xl sm:text-5xl font-display font-black text-white uppercase tracking-tight mb-2">
                                Clubes <span className="text-gold-500">Oficiales</span>
                            </h1>
                            <p className="text-gray-400 max-w-lg text-sm sm:text-base">
                                Explora las plantillas de los equipos que compiten por la gloria eterna en la liga.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== STATS BANNER ===== */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="grid grid-cols-3 gap-3">
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-gold-500/10 flex items-center justify-center">
                            <Shield size={18} className="text-gold-500" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{totalEquipos}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Equipos</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                            <Users size={18} className="text-blue-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">{totalJugadores}</span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Jugadores</span>
                        </div>
                    </div>
                    <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 flex items-center gap-3 hover:border-gold-500/20 transition-all">
                        <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                            <DollarSign size={18} className="text-green-400" />
                        </div>
                        <div>
                            <span className="block text-white font-black text-xl">
                                ${valorTotal >= 1000000 ? `${(valorTotal / 1000000).toFixed(1)}M` :
                                    valorTotal >= 1000 ? `${(valorTotal / 1000).toFixed(0)}K` : valorTotal}
                            </span>
                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest">Valor Liga</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== TEAMS GRID ===== */}
            <div className="max-w-7xl mx-auto">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 gap-4">
                        <Loader2 className="w-10 h-10 text-gold-500 animate-spin" />
                        <span className="text-gray-500 text-sm font-medium uppercase tracking-widest">Cargando clubes...</span>
                    </div>
                ) : equipos.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                        {equipos.map((eq, i) => (
                            <TeamCard
                                key={i}
                                equipo={eq}
                                onClick={() => setSelectedTeam(eq)}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-dark-800/30 rounded-3xl border border-white/5 border-dashed">
                        <Shield className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-gray-400 mb-2">Sin Equipos Registrados</h3>
                        <p className="text-gray-500 text-sm">La liga comenzará pronto.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Equipos;
