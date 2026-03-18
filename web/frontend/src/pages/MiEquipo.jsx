import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ligaService } from '../services/api';
import {
    Shield, Users, DollarSign, UserCircle, TrendingUp,
    Calendar, Star, Award, Zap, Activity, Crown, ChevronRight
} from 'lucide-react';

const MiEquipo = () => {
    const { user, loading: authLoading } = useAuth();
    const [miJugador, setMiJugador] = useState(null);
    const [equipo, setEquipo] = useState(null);
    const [jugadores, setJugadores] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const cargarDatos = async () => {
            if (!user) return;
            setLoading(true);
            try {
                // 1. Buscar datos del jugador logueado
                try {
                    const jugadorData = await ligaService.getJugadorDetalle(user.sub);
                    if (jugadorData && !jugadorData.error) {
                        setMiJugador(jugadorData);
                    }
                } catch (err) {
                    console.log("Usuario no es jugador registrado");
                }

                // 2. Cargar equipos y plantilla si es DT
                if (user.team_id) {
                    const equipos = await ligaService.getEquipos();
                    const miEquipo = equipos.find(e =>
                        e.nombre === user.team_name ||
                        e.role_name === user.team_name ||
                        String(e.role_id) === String(user.team_id)
                    );
                    setEquipo(miEquipo);

                    if (miEquipo) {
                        const todosJugadores = await ligaService.getJugadores('todos');
                        const misJugadores = todosJugadores.filter(j =>
                            j.equipo === miEquipo.nombre || j.equipo === miEquipo.role_name
                        );
                        setJugadores(misJugadores);
                    }
                }
            } catch (error) {
                console.error("Error cargando datos:", error);
            } finally {
                setLoading(false);
            }
        };
        if (!authLoading) cargarDatos();
    }, [user, authLoading]);

    // ====== HELPERS ======
    const getPosColor = (pos) => {
        switch (pos) {
            case 'GK': return { text: 'text-yellow-400', bg: 'bg-yellow-500', glow: 'shadow-yellow-500/30', gradient: 'from-yellow-500/20 to-yellow-600/5' };
            case 'DEF': return { text: 'text-blue-400', bg: 'bg-blue-500', glow: 'shadow-blue-500/30', gradient: 'from-blue-500/20 to-blue-600/5' };
            case 'MC': return { text: 'text-green-400', bg: 'bg-green-500', glow: 'shadow-green-500/30', gradient: 'from-green-500/20 to-green-600/5' };
            case 'DC': return { text: 'text-red-400', bg: 'bg-red-500', glow: 'shadow-red-500/30', gradient: 'from-red-500/20 to-red-600/5' };
            default: return { text: 'text-gray-400', bg: 'bg-gray-500', glow: 'shadow-gray-500/30', gradient: 'from-gray-500/20 to-gray-600/5' };
        }
    };

    const calcularFichajes = (historial) => {
        if (!historial) return 0;
        return historial.filter(h => h.action_type === 'FICHAJE').length;
    };

    const calcularDiasEnEquipo = (fechaFichaje) => {
        if (!fechaFichaje) return '??';
        const dias = Math.floor((Date.now() - new Date(fechaFichaje).getTime()) / (1000 * 60 * 60 * 24));
        return dias;
    };

    // ====== LOADING STATES ======
    if (authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500" />
            </div>
        );
    }

    if (!user) {
        return (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 min-h-screen pb-20 px-6 pt-6">
                <div className="max-w-2xl mx-auto text-center py-20">
                    <div className="relative inline-block mb-8">
                        <div className="w-24 h-24 rounded-full bg-dark-800 border-2 border-white/10 flex items-center justify-center">
                            <Shield className="w-12 h-12 text-gray-600" />
                        </div>
                        <div className="absolute -inset-4 rounded-full bg-gold-500/5 animate-pulse" />
                    </div>
                    <h1 className="text-4xl font-display font-black text-white uppercase mb-4 tracking-tight">
                        Mi Perfil
                    </h1>
                    <p className="text-gray-400 text-lg mb-8">
                        Inicia sesión con Discord para ver tu carta de jugador y gestionar tu equipo.
                    </p>
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#5865F2]/10 border border-[#5865F2]/30 rounded-xl text-[#5865F2] text-sm font-bold">
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z" /></svg>
                        Usa el botón de Login arriba
                    </div>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500" />
            </div>
        );
    }

    const posColor = getPosColor(miJugador?.posicion);
    const precio = miJugador?.precio || miJugador?.clausula || 0;
    const esDT = miJugador?.es_dt || user?.team_id;
    const totalFichajes = calcularFichajes(miJugador?.historial);

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 min-h-screen pb-20 px-4 sm:px-6 pt-6">
            <div className="max-w-6xl mx-auto">

                {/* ===== SECCIÓN 1: CARTA FIFA DEL JUGADOR ===== */}
                <div className="mb-12">
                    <div className="relative">
                        {/* Background glow */}
                        <div className="absolute inset-0 bg-gradient-to-br from-gold-500/10 via-transparent to-dark-950 rounded-3xl blur-xl" />

                        <div className="relative bg-dark-900 border border-white/10 rounded-3xl overflow-hidden">
                            {/* Top accent bar */}
                            <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-gold-600" />

                            <div className="flex flex-col lg:flex-row">
                                {/* ===== LEFT: CARTA FIFA ===== */}
                                <div className="lg:w-[380px] p-8 flex flex-col items-center justify-center relative overflow-hidden border-b lg:border-b-0 lg:border-r border-white/5">
                                    {/* Background pattern */}
                                    <div className="absolute inset-0 opacity-[0.03]" style={{
                                        backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 30px, rgba(212,175,55,0.3) 30px, rgba(212,175,55,0.3) 31px)`
                                    }} />

                                    {/* Rating OVR */}
                                    <div className="absolute top-6 left-6 z-20">
                                        <div className="text-center">
                                            <span className="block text-5xl font-display font-black text-gold-500 leading-none tracking-tight">
                                                {miJugador?.rating || Math.floor(60 + (precio / 5000))}
                                            </span>
                                            <span className={`block text-sm font-black uppercase tracking-widest mt-1 ${posColor.text}`}>
                                                {miJugador?.posicion || 'JUG'}
                                            </span>
                                        </div>
                                    </div>

                                    {/* DT Badge */}
                                    {esDT && (
                                        <div className="absolute top-6 right-6 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-gold-500/10 border border-gold-500/30 rounded-full">
                                            <Crown size={14} className="text-gold-500" />
                                            <span className="text-xs font-black text-gold-500 uppercase tracking-widest">DT</span>
                                        </div>
                                    )}

                                    {/* Player Avatar - FIFA Style */}
                                    <div className="relative w-52 h-52 mt-8 mb-6 z-10">
                                        {/* Glow ring */}
                                        <div className={`absolute -inset-3 rounded-full ${posColor.bg} opacity-20 blur-2xl animate-pulse`} />
                                        <div className={`absolute -inset-1 rounded-full bg-gradient-to-b ${posColor.gradient} border border-white/10`} />
                                        <img
                                            src={user.avatar || miJugador?.avatar_url || `https://cdn.discordapp.com/embed/avatars/0.png`}
                                            alt={user.name}
                                            className="w-full h-full object-cover rounded-full relative z-10 border-4 border-dark-800"
                                        />
                                        {/* Online indicator */}
                                        <div className="absolute bottom-3 right-3 z-20 w-5 h-5 rounded-full bg-green-500 border-3 border-dark-800 shadow-lg shadow-green-500/40" />
                                    </div>

                                    {/* Player Name */}
                                    <h1 className="text-3xl sm:text-4xl font-display font-black text-white text-center uppercase tracking-tight mb-2 relative z-10">
                                        {user.name}
                                    </h1>

                                    {/* Team badge */}
                                    {(miJugador?.equipo || user.team_name) && (
                                        <div className="flex items-center gap-2 px-4 py-1.5 bg-dark-800 border border-white/10 rounded-full mb-6 relative z-10">
                                            <Shield size={14} className="text-gold-500" />
                                            <span className="text-sm font-bold text-gray-300 uppercase tracking-wider">
                                                {miJugador?.equipo || user.team_name}
                                            </span>
                                        </div>
                                    )}

                                    {/* Stats Grid - FIFA Style */}
                                    <div className="grid grid-cols-3 gap-3 w-full relative z-10">
                                        <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 text-center hover:border-gold-500/20 transition-colors">
                                            <DollarSign size={16} className="text-gold-500 mx-auto mb-1" />
                                            <span className="block text-white font-black text-lg leading-none">
                                                {precio >= 1000 ? `${(precio / 1000).toFixed(0)}K` : precio}
                                            </span>
                                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest mt-1">Valor</span>
                                        </div>
                                        <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 text-center hover:border-gold-500/20 transition-colors">
                                            <Zap size={16} className="text-yellow-500 mx-auto mb-1" />
                                            <span className="block text-white font-black text-lg leading-none">
                                                {totalFichajes}
                                            </span>
                                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest mt-1">Fichajes</span>
                                        </div>
                                        <div className="bg-dark-800/80 border border-white/5 rounded-xl p-3 text-center hover:border-gold-500/20 transition-colors">
                                            <Calendar size={16} className="text-blue-500 mx-auto mb-1" />
                                            <span className="block text-white font-black text-lg leading-none">
                                                {calcularDiasEnEquipo(miJugador?.fecha_fichaje)}
                                            </span>
                                            <span className="block text-[10px] text-gray-500 uppercase tracking-widest mt-1">Días</span>
                                        </div>
                                    </div>

                                    {/* Clausula / Precio detail */}
                                    <div className="w-full mt-4 relative z-10">
                                        <div className="bg-gradient-to-r from-gold-500/10 to-transparent border border-gold-500/20 rounded-xl p-4 flex items-center justify-between">
                                            <div>
                                                <span className="block text-gold-400 text-[10px] font-bold uppercase tracking-widest">Cláusula de Rescisión</span>
                                                <span className="text-gold-500 font-black text-2xl">
                                                    ${new Intl.NumberFormat('en-US').format(miJugador?.clausula || precio)}
                                                </span>
                                            </div>
                                            <Award className="text-gold-500/40 w-10 h-10" />
                                        </div>
                                    </div>
                                </div>

                                {/* ===== RIGHT: DETALLES ===== */}
                                <div className="flex-1 p-8 overflow-y-auto">
                                    {/* Quick Stats Bar */}
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
                                        <div className="bg-dark-800 border border-white/5 rounded-xl p-4 text-center group hover:border-gold-500/20 transition-all">
                                            <span className="block text-2xl font-black text-white group-hover:text-gold-500 transition-colors">
                                                {miJugador?.estado_actual === 'Contratado' ? '✅' : '🟡'}
                                            </span>
                                            <span className="block text-xs text-gray-500 uppercase tracking-widest mt-1">Estado</span>
                                            <span className="block text-xs text-gray-300 font-semibold mt-0.5">
                                                {miJugador?.estado_actual || 'Agente Libre'}
                                            </span>
                                        </div>
                                        <div className="bg-dark-800 border border-white/5 rounded-xl p-4 text-center group hover:border-gold-500/20 transition-all">
                                            <span className="block text-2xl font-black text-white group-hover:text-gold-500 transition-colors">
                                                {miJugador?.posicion || '?'}
                                            </span>
                                            <span className="block text-xs text-gray-500 uppercase tracking-widest mt-1">Posición</span>
                                        </div>
                                        <div className="bg-dark-800 border border-white/5 rounded-xl p-4 text-center group hover:border-gold-500/20 transition-all">
                                            <span className="block text-2xl font-black text-white group-hover:text-gold-500 transition-colors">
                                                {miJugador?.dorsal || '#?'}
                                            </span>
                                            <span className="block text-xs text-gray-500 uppercase tracking-widest mt-1">Dorsal</span>
                                        </div>
                                        <div className="bg-dark-800 border border-white/5 rounded-xl p-4 text-center group hover:border-gold-500/20 transition-all">
                                            <span className="block text-2xl font-black text-white group-hover:text-gold-500 transition-colors">
                                                ${new Intl.NumberFormat('en-US').format(miJugador?.precio || 0)}
                                            </span>
                                            <span className="block text-xs text-gray-500 uppercase tracking-widest mt-1">Precio</span>
                                        </div>
                                    </div>

                                    {/* Trayectoria */}
                                    <div className="mb-8">
                                        <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-lg uppercase tracking-widest mb-6">
                                            <TrendingUp size={20} /> Mi Trayectoria
                                        </h3>

                                        <div className="space-y-4 relative ml-3">
                                            <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-gradient-to-b from-gold-500/40 via-white/10 to-transparent" />

                                            {miJugador?.historial && miJugador.historial.length > 0 ? (
                                                miJugador.historial.slice().reverse().map((event, idx) => (
                                                    <div key={idx} className="relative pl-8 group">
                                                        <div className={`absolute left-0 top-2 w-4 h-4 rounded-full border-2 border-dark-900 z-10 transition-transform group-hover:scale-125 ${event.action_type === 'FICHAJE' ? 'bg-green-500 shadow-lg shadow-green-500/30' :
                                                            event.action_type === 'DESPIDO' ? 'bg-red-500 shadow-lg shadow-red-500/30' : 'bg-yellow-500 shadow-lg shadow-yellow-500/30'
                                                            }`} />

                                                        <div className="bg-dark-800/60 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-all">
                                                            <div className="flex justify-between items-start">
                                                                <div>
                                                                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full border inline-block ${event.action_type === 'FICHAJE' ? 'text-green-400 border-green-500/30 bg-green-500/10' :
                                                                        event.action_type === 'DESPIDO' ? 'text-red-400 border-red-500/30 bg-red-500/10' : 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                                                        }`}>
                                                                        {event.action_type === 'FICHAJE' ? '⚽ FICHAJE' : event.action_type === 'DESPIDO' ? '🔴 DESPIDO' : '👋 RENUNCIA'}
                                                                    </span>
                                                                    <h4 className="text-white font-bold mt-2 flex items-center gap-2">
                                                                        {event.details?.equipo_destino || event.details?.equipo || 'Agente Libre'}
                                                                        {event.details?.precio && (
                                                                            <span className="text-gold-500 text-xs font-bold px-2 py-0.5 bg-gold-500/10 rounded-full">
                                                                                ${new Intl.NumberFormat('en-US').format(event.details.precio)}
                                                                            </span>
                                                                        )}
                                                                    </h4>
                                                                    <p className="text-sm text-gray-500 mt-0.5">
                                                                        {event.action_type === 'FICHAJE' ? `Fichado desde ${event.details?.equipo_origen || 'Libre'}` :
                                                                            event.action_type === 'DESPIDO' ? 'Rescindido del contrato.' : 'Abandonó el equipo.'}
                                                                    </p>
                                                                </div>
                                                                <span className="text-xs text-gray-600 font-mono bg-dark-900 px-2 py-1 rounded">
                                                                    {new Date(event.timestamp).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="pl-8 py-8 text-center">
                                                    <Activity className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                                                    <p className="text-gray-500 italic">Sin historial registrado aún.</p>
                                                    <p className="text-gray-600 text-sm mt-1">Tu trayectoria aparecerá aquí</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ===== SECCIÓN 2: DASHBOARD DT ===== */}
                {equipo && esDT && (
                    <div className="mb-12">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 bg-gold-500/10 border border-gold-500/30 rounded-xl flex items-center justify-center">
                                <Crown size={20} className="text-gold-500" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-display font-black text-white uppercase tracking-tight">
                                    Panel DT — {equipo.nombre || equipo.role_name}
                                </h2>
                                <p className="text-gray-500 text-sm">Gestión de tu equipo</p>
                            </div>
                        </div>

                        {/* DT Stats */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                            <div className="bg-dark-900 border border-white/10 rounded-2xl p-5 group hover:border-gold-500/30 transition-all">
                                <div className="flex items-center justify-between mb-3">
                                    <DollarSign className="w-5 h-5 text-gold-500" />
                                    <span className="text-xs text-gray-600 uppercase tracking-widest">Presupuesto</span>
                                </div>
                                <span className="text-3xl font-black text-gold-500">
                                    ${new Intl.NumberFormat('en-US').format(equipo.presupuesto || 0)}
                                </span>
                            </div>
                            <div className="bg-dark-900 border border-white/10 rounded-2xl p-5 group hover:border-gold-500/30 transition-all">
                                <div className="flex items-center justify-between mb-3">
                                    <Users className="w-5 h-5 text-blue-400" />
                                    <span className="text-xs text-gray-600 uppercase tracking-widest">Plantilla</span>
                                </div>
                                <span className="text-3xl font-black text-white">
                                    {jugadores.length}<span className="text-gray-600 text-lg">/12</span>
                                </span>
                            </div>
                            <div className="bg-dark-900 border border-white/10 rounded-2xl p-5 group hover:border-gold-500/30 transition-all">
                                <div className="flex items-center justify-between mb-3">
                                    <Star className="w-5 h-5 text-yellow-400" />
                                    <span className="text-xs text-gray-600 uppercase tracking-widest">Cupos</span>
                                </div>
                                <span className={`text-3xl font-black ${12 - jugadores.length > 3 ? 'text-green-400' : 12 - jugadores.length > 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                                    {12 - jugadores.length}
                                </span>
                            </div>
                            <div className="bg-dark-900 border border-white/10 rounded-2xl p-5 group hover:border-gold-500/30 transition-all">
                                <div className="flex items-center justify-between mb-3">
                                    <Activity className="w-5 h-5 text-purple-400" />
                                    <span className="text-xs text-gray-600 uppercase tracking-widest">Valor Plan.</span>
                                </div>
                                <span className="text-3xl font-black text-white">
                                    ${new Intl.NumberFormat('en-US').format(
                                        jugadores.reduce((sum, j) => sum + (j.precio || 0), 0)
                                    )}
                                </span>
                            </div>
                        </div>

                        {/* Plantilla Grid */}
                        <h3 className="flex items-center gap-2 text-gold-500 font-display font-bold text-lg uppercase tracking-widest mb-5">
                            <Users size={20} /> Plantilla
                        </h3>

                        {jugadores.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {jugadores.map((jugador, idx) => {
                                    const jPosColor = getPosColor(jugador.posicion);
                                    return (
                                        <div key={idx} className="bg-dark-800 border border-white/10 rounded-2xl p-5 flex items-center gap-4 hover:border-gold-500/20 transition-all group cursor-default">
                                            <div className="relative">
                                                <img
                                                    src={jugador.avatar_url || `https://cdn.discordapp.com/embed/avatars/${idx % 5}.png`}
                                                    alt={jugador.nombre}
                                                    className="w-14 h-14 rounded-full border-2 border-dark-700 object-cover group-hover:border-gold-500/40 transition-colors"
                                                />
                                                {jugador.es_dt && (
                                                    <div className="absolute -top-1 -right-1 w-5 h-5 bg-gold-500 rounded-full flex items-center justify-center">
                                                        <Crown size={10} className="text-black" />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h4 className="text-white font-bold text-sm truncate">{jugador.nombre}</h4>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${jPosColor.text} bg-dark-900 border-white/10`}>
                                                        {jugador.posicion || '?'}
                                                    </span>
                                                    <span className="text-xs text-gold-500 font-bold">
                                                        ${new Intl.NumberFormat('en-US').format(jugador.precio || 0)}
                                                    </span>
                                                </div>
                                            </div>
                                            <ChevronRight size={16} className="text-gray-700 group-hover:text-gold-500 transition-colors flex-shrink-0" />
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="bg-dark-800/50 border border-white/5 rounded-2xl p-10 text-center">
                                <Users className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                                <p className="text-gray-500 mb-1">Tu plantilla está vacía.</p>
                                <p className="text-gray-600 text-sm">
                                    Usa <code className="text-white bg-dark-800 px-1.5 py-0.5 rounded text-xs">/fichar</code> en Discord para fichar jugadores.
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* ===== Si no es DT y no tiene datos de jugador ===== */}
                {!miJugador && !equipo && (
                    <div className="text-center py-8">
                        <div className="bg-dark-800/50 border border-white/5 rounded-2xl p-10 max-w-md mx-auto">
                            <UserCircle className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                            <h3 className="text-xl font-display font-black text-white uppercase mb-2">
                                Sin Equipo
                            </h3>
                            <p className="text-gray-500 text-sm mb-4">
                                No estás registrado como jugador ni como DT en la liga.
                            </p>
                            <div className="bg-[#5865F2]/10 border border-[#5865F2]/30 rounded-xl p-3 text-sm text-[#5865F2] font-medium">
                                Contacta a un DT en Discord para unirte a un equipo
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MiEquipo;
