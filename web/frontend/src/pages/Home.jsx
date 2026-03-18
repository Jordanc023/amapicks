import React, { useEffect, useState } from 'react';
import { ArrowRight, Trophy, Users, Shield, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ligaService } from '../services/api';
import Button from '../components/Button';

// Componente Hero Section
const Hero = () => (
    <div className="relative h-[600px] flex items-center overflow-hidden">
        {/* Background Image / Overlay */}
        <div className="absolute inset-0 bg-dark-900">
            {/* Placeholder para una imagen real de estadio/jugadores */}
            <div className="absolute inset-0 bg-gradient-to-r from-dark-950 via-dark-900/80 to-transparent z-10" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-gold-600/20 via-dark-900/0 to-dark-950/0 z-0" />
        </div>

        <div className="relative z-20 max-w-7xl mx-auto px-6 w-full mt-10">
            <div className="max-w-2xl">
                <span className="inline-block py-1 px-3 rounded-full bg-gold-500/10 text-gold-400 text-xs font-bold uppercase tracking-[0.2em] mb-6 border border-gold-500/20">
                    Temporada Oficial 2026
                </span>
                <h1 className="text-5xl md:text-7xl font-display font-black text-white leading-tight mb-6">
                    DOMINA <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-300 to-gold-600">
                        EL TERRENO
                    </span>
                </h1>
                <p className="text-lg text-gray-400 mb-8 max-w-lg font-light leading-relaxed">
                    Gestiona tu equipo, ficha estrellas y compite en la liga de Haxball más prestigiosa.
                    Tu legado comienza ahora.
                </p>
                <div className="flex gap-4">
                    <Link to="/mercado">
                        <Button variant="primary" className="!px-8 !py-4 font-bold tracking-widest text-dark-900">
                            IR AL MERCADO
                        </Button>
                    </Link>
                    <Button variant="outline" className="!px-8 !py-4 tracking-widest">
                        VER PARTIDOS
                    </Button>
                </div>
            </div>
        </div>
    </div>
);

// Componente Card "Match/Stat"
const DashboardCard = ({ title, value, icon: Icon, color, image }) => (
    <div className="group relative bg-dark-800 rounded-xl overflow-hidden shadow-card hover:shadow-gold transition-all duration-500 hover:-translate-y-2 border border-white/5">
        <div className="absolute top-0 right-0 p-4 opacity-50">
            <Icon size={40} className="text-white/5 group-hover:text-gold-500/20 transition-colors" />
        </div>

        <div className="p-8 relative z-10">
            <h3 className="text-gray-400 text-sm font-bold uppercase tracking-widest mb-2">{title}</h3>
            <div className="text-4xl font-display font-bold text-white group-hover:text-gold-400 transition-colors">
                {value}
            </div>
        </div>

        {/* Gradient Line Bottom */}
        <div className="h-1 w-full bg-dark-700">
            <div className="h-full bg-gold-500 w-0 group-hover:w-full transition-all duration-700 ease-in-out" />
        </div>
    </div>
);

const Home = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await ligaService.getStats();
                setStats(data);
            } catch (e) { console.error(e) }
            finally { setLoading(false) }
        };
        load();
    }, []);

    return (
        <div className="animate-in fade-in duration-700 pb-20">
            <Hero />

            {/* Stats Section */}
            <div className="max-w-7xl mx-auto px-6 -mt-20 relative z-30">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <DashboardCard
                        title="Jugadores Activos"
                        value={stats?.jugadores_totales || "-"}
                        icon={Users}
                    />
                    <DashboardCard
                        title="Agentes Libres"
                        value={stats?.agentes_libres || "-"}
                        icon={Shield}
                    />
                    <DashboardCard
                        title="Partidos Pendientes"
                        value={stats?.partidos_pendientes || "-"}
                        icon={Clock}
                    />
                </div>
            </div>

            {/* News / Updates Section (Placeholder for "Noticias del Club") */}
            <div className="max-w-7xl mx-auto px-6 mt-20">
                <div className="flex items-center justify-between mb-10">
                    <h2 className="text-3xl font-display font-bold text-white uppercase tracking-tighter">
                        Últimas Novedades
                    </h2>
                    <Link to="#" className="text-gold-500 font-bold text-sm uppercase tracking-widest hover:text-white transition-colors flex items-center gap-2">
                        Ver todas <ArrowRight size={16} />
                    </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="bg-dark-800 h-[400px] rounded-2xl border border-white/5 relative overflow-hidden group cursor-pointer">
                        {/* Fake Image Placeholder */}
                        <div className="absolute inset-0 bg-gradient-to-t from-dark-900 to-transparent z-10" />
                        <div className="absolute inset-0 bg-dark-700 group-hover:scale-105 transition-transform duration-700" />

                        <div className="absolute bottom-0 left-0 p-8 z-20">
                            <span className="text-gold-500 font-bold text-xs uppercase tracking-widest mb-2 block">Transferencias</span>
                            <h3 className="text-2xl font-display font-bold text-white mb-4 max-w-sm">
                                EL MERCADO DE FICHAJES ABRE SUS PUERTAS
                            </h3>
                            <p className="text-gray-400 line-clamp-2">
                                Los directores técnicos ya pueden comenzar a negociar para la próxima jornada. Revisa las reglas actualizadas.
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-rows-2 gap-6 h-[400px]">
                        <div className="bg-dark-800 rounded-2xl border border-white/5 p-6 flex items-center hover:border-gold-500/30 transition-colors group cursor-pointer relative overflow-hidden">
                            <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gold-500/5 -skew-x-12" />
                            <div>
                                <span className="text-gray-500 font-bold text-xs uppercase tracking-widest mb-1 block">Partido Destacado</span>
                                <h4 className="text-xl font-display font-bold text-white">LIVERPOOL vs REAL MADRID</h4>
                                <span className="text-gold-500 text-sm font-semibold mt-2 block group-hover:translate-x-2 transition-transform">Ver previa &rarr;</span>
                            </div>
                        </div>
                        <div className="bg-dark-800 rounded-2xl border border-white/5 p-6 flex items-center hover:border-gold-500/30 transition-colors group cursor-pointer relative overflow-hidden">
                            <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-blue-500/5 -skew-x-12" />
                            <div>
                                <span className="text-gray-500 font-bold text-xs uppercase tracking-widest mb-1 block">Estadísticas</span>
                                <h4 className="text-xl font-display font-bold text-white">TOP GOLEADORES SEMANA 1</h4>
                                <span className="text-gold-500 text-sm font-semibold mt-2 block group-hover:translate-x-2 transition-transform">Ver tabla &rarr;</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
