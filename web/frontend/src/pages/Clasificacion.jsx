import React, { useState, useEffect } from 'react';
import { Trophy, RefreshCw, Hash, Shield, ChevronDown } from 'lucide-react';
import { ligaService } from '../services/api';

const Clasificacion = () => {
    const [tabla, setTabla] = useState([]);
    const [loading, setLoading] = useState(true);
    const [ligas, setLigas] = useState([]);
    const [ligaSeleccionada, setLigaSeleccionada] = useState(null);
    const [ligaInfo, setLigaInfo] = useState(null);

    // Cargar ligas disponibles
    useEffect(() => {
        const loadLigas = async () => {
            try {
                const data = await ligaService.getLigasDisponibles();
                setLigas(data);
                // Seleccionar primera liga por defecto
                if (data.length > 0 && !ligaSeleccionada) {
                    setLigaSeleccionada(data[0].id);
                }
            } catch (error) {
                console.error("Error cargando ligas:", error);
            }
        };
        loadLigas();
    }, []);

    // Cargar clasificación cuando cambia la liga seleccionada
    useEffect(() => {
        const loadClasificacion = async () => {
            if (!ligaSeleccionada) return;
            
            setLoading(true);
            try {
                const data = await ligaService.getClasificacion(ligaSeleccionada);
                setTabla(data.tabla || []);
                setLigaInfo(data.liga);
            } catch (error) {
                console.error("Error cargando clasificación:", error);
                setTabla([]);
            } finally {
                setLoading(false);
            }
        };

        loadClasificacion();
    }, [ligaSeleccionada]);

    const handleCambiarLiga = (e) => {
        setLigaSeleccionada(e.target.value);
    };

    // Encontrar nombre de liga seleccionada
    const ligaActual = ligas.find(l => l.id === ligaSeleccionada);

    if (loading && tabla.length === 0) {
        return (
            <div className="min-h-[50vh] flex items-center justify-center text-gold-500">
                <RefreshCw className="animate-spin w-8 h-8" />
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                <div className="flex-1">
                    <h1 className="text-4xl md:text-5xl font-display font-black text-white uppercase tracking-tight flex items-center gap-4">
                        <div className="w-16 h-16 bg-gold-500/10 rounded-2xl flex items-center justify-center border border-gold-500/20">
                            <Trophy className="text-gold-500 w-8 h-8" />
                        </div>
                        Clasificación Oficial
                    </h1>
                    <p className="text-gray-400 mt-4 max-w-2xl text-lg">
                        Sigue en directo los puntos y rendimiento de todos los equipos.
                    </p>
                </div>

                {/* Selector de Liga */}
                <div className="relative">
                    <div className="flex items-center gap-3 bg-dark-800 border border-white/10 rounded-xl px-4 py-3">
                        <span className="text-gray-400 text-sm">Liga:</span>
                        <div className="relative">
                            <select
                                value={ligaSeleccionada || ''}
                                onChange={handleCambiarLiga}
                                className="appearance-none bg-transparent text-white font-medium pr-8 pl-2 focus:outline-none cursor-pointer"
                            >
                                {ligas.map((liga) => (
                                    <option key={liga.id} value={liga.id}>
                                        {liga.division} - {liga.nombre}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Info de la liga */}
            {ligaInfo && (
                <div className="mb-6 flex flex-wrap gap-4">
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Temporada: </span>
                        <span className="text-white font-medium">{ligaInfo.nombre}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">División: </span>
                        <span className="text-gold-400 font-medium">{ligaInfo.division}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Jornada: </span>
                        <span className="text-white font-medium">{ligaInfo.jornada_actual}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Estado: </span>
                        <span className={`font-medium ${
                            ligaInfo.estado === 'en_curso' ? 'text-green-400' :
                            ligaInfo.estado === 'paron_copa' ? 'text-yellow-400' :
                            'text-gray-400'
                        }`}>
                            {ligaInfo.estado === 'en_curso' ? 'En Curso' :
                             ligaInfo.estado === 'paron_copa' ? 'Parón Copa' :
                             ligaInfo.estado === 'configuracion' ? 'Configuración' :
                             ligaInfo.estado}
                        </span>
                    </div>
                </div>
            )}

            <div className="bg-dark-900/50 rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
                {tabla.length === 0 ? (
                    <div className="p-16 text-center text-gray-500">
                        <Shield className="w-16 h-16 mx-auto mb-4 opacity-20" />
                        <h3 className="text-xl font-bold text-white mb-2">Tabla Vacía</h3>
                        <p>No hay equipos registrados o la temporada aún no ha comenzado.</p>
                        {ligaActual && (
                            <p className="mt-2 text-sm text-gray-600">
                                Liga seleccionada: {ligaActual.division} - {ligaActual.nombre}
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left whitespace-nowrap">
                            <thead className="bg-black/60 text-gray-400 text-xs font-bold uppercase tracking-wider border-b border-white/10">
                                <tr>
                                    <th className="p-5 pl-8 w-16 text-center"><Hash size={14} className="mx-auto" /></th>
                                    <th className="p-5">Club</th>
                                    <th className="p-5 text-center w-20" title="Partidos Jugados">PJ</th>
                                    <th className="p-5 text-center w-20 text-green-500/70" title="Partidos Ganados">PG</th>
                                    <th className="p-5 text-center w-20 text-yellow-500/70" title="Partidos Empatados">PE</th>
                                    <th className="p-5 text-center w-20 text-red-500/70" title="Partidos Perdidos">PP</th>
                                    <th className="p-5 text-center w-20" title="Goles a Favor">GF</th>
                                    <th className="p-5 text-center w-20" title="Goles en Contra">GC</th>
                                    <th className="p-5 text-center w-24 border-l border-white/5" title="Diferencia de Goles">DG</th>
                                    <th className="p-5 pr-8 text-center w-24 bg-gold-500/5 text-gold-500" title="Puntos Totales">PTS</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {tabla.map((eq, idx) => {
                                    const isChampion = idx === 0;
                                    const isRelegation = idx >= tabla.length - 2 && tabla.length > 5;
                                    const isCopaSpot = idx < 8; // Primeros 8 a copa

                                    return (
                                        <tr
                                            key={eq.equipo}
                                            className={`transition-colors hover:bg-white/5 ${isChampion ? 'bg-gold-500/5' : ''} ${isRelegation ? 'bg-red-500/5' : ''}`}
                                        >
                                            <td className="p-5 pl-8 text-center font-black text-lg">
                                                {isChampion ? (
                                                    <span className="text-gold-500">1</span>
                                                ) : (
                                                    <span className={`${isCopaSpot ? 'text-blue-400' : 'text-gray-500'}`}>{eq.pos}</span>
                                                )}
                                            </td>
                                            <td className="p-5">
                                                <div className="flex items-center gap-4">
                                                    <img
                                                        src={eq.logo}
                                                        alt={eq.equipo}
                                                        className="w-10 h-10 rounded-full bg-dark-800 border border-white/10 object-cover"
                                                    />
                                                    <span className="font-bold text-white text-lg">{eq.equipo}</span>
                                                    {isChampion && <span className="text-xs bg-gold-500/20 text-gold-400 px-2 py-0.5 rounded">Líder</span>}
                                                </div>
                                            </td>
                                            <td className="p-5 text-center font-medium text-gray-300 bg-white/[0.02]">{eq.pj}</td>
                                            <td className="p-5 text-center font-medium text-green-400">{eq.pg}</td>
                                            <td className="p-5 text-center font-medium text-yellow-500">{eq.pe}</td>
                                            <td className="p-5 text-center font-medium text-red-400">{eq.pp}</td>
                                            <td className="p-5 text-center font-medium text-gray-300">{eq.gf}</td>
                                            <td className="p-5 text-center font-medium text-gray-300">{eq.gc}</td>
                                            <td className="p-5 text-center font-mono font-bold text-gray-400 border-l border-white/5">
                                                {eq.dg > 0 ? `+${eq.dg}` : eq.dg}
                                            </td>
                                            <td className="p-5 pr-8 text-center font-black text-xl text-gold-400 bg-gold-500/5">
                                                {eq.pts}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <div className="mt-8 flex flex-wrap gap-4 text-xs text-gray-500 font-medium uppercase tracking-wider justify-center md:justify-end">
                <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-gold-500/20 border border-gold-500/50"></div> Campeón / Ascenso</span>
                <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500/20 border border-blue-500/50"></div> Clasifica a Copa</span>
                <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div> Descenso</span>
            </div>
        </div>
    );
};

export default Clasificacion;
