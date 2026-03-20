import React, { useState, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight, ChevronDown, Trophy, MapPin, Clock, Shield } from 'lucide-react';
import { ligaService } from '../services/api';

const Jornadas = () => {
    const [ligas, setLigas] = useState([]);
    const [ligaSeleccionada, setLigaSeleccionada] = useState(null);
    const [jornadasData, setJornadasData] = useState(null);
    const [jornadaActual, setJornadaActual] = useState(1);
    const [loading, setLoading] = useState(true);

    // Cargar ligas disponibles
    useEffect(() => {
        const loadLigas = async () => {
            try {
                const data = await ligaService.getLigasDisponibles();
                setLigas(data);
                if (data.length > 0 && !ligaSeleccionada) {
                    setLigaSeleccionada(data[0].id);
                }
            } catch (error) {
                console.error("Error cargando ligas:", error);
            }
        };
        loadLigas();
    }, []);

    // Cargar jornadas cuando cambia la liga
    useEffect(() => {
        const loadJornadas = async () => {
            if (!ligaSeleccionada) return;
            
            setLoading(true);
            try {
                const data = await ligaService.getJornadas(ligaSeleccionada);
                setJornadasData(data);
                setJornadaActual(data.jornada_actual || 1);
            } catch (error) {
                console.error("Error cargando jornadas:", error);
            } finally {
                setLoading(false);
            }
        };

        loadJornadas();
    }, [ligaSeleccionada]);

    const handleCambiarLiga = (e) => {
        setLigaSeleccionada(e.target.value);
    };

    const cambiarJornada = (direccion) => {
        if (!jornadasData) return;
        const total = jornadasData.liga?.total_jornadas || 22;
        const nueva = jornadaActual + direccion;
        if (nueva >= 1 && nueva <= total) {
            setJornadaActual(nueva);
        }
    };

    const irAJornadaActual = () => {
        if (jornadasData) {
            setJornadaActual(jornadasData.jornada_actual || 1);
        }
    };

    // Obtener jornada actual para mostrar
    const jornadaSeleccionada = jornadasData?.jornadas?.find(j => j.jornada === jornadaActual);
    const ligaActual = ligas.find(l => l.id === ligaSeleccionada);

    if (loading && !jornadasData) {
        return (
            <div className="min-h-[50vh] flex items-center justify-center text-gold-500">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
                <div className="flex-1">
                    <h1 className="text-4xl md:text-5xl font-display font-black text-white uppercase tracking-tight flex items-center gap-4">
                        <div className="w-16 h-16 bg-gold-500/10 rounded-2xl flex items-center justify-center border border-gold-500/20">
                            <Calendar className="text-gold-500 w-8 h-8" />
                        </div>
                        Jornadas
                    </h1>
                    <p className="text-gray-400 mt-4 max-w-2xl text-lg">
                        Consulta los partidos de cada jornada y los resultados actualizados.
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
            {jornadasData?.liga && (
                <div className="mb-6 flex flex-wrap gap-4">
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Temporada: </span>
                        <span className="text-white font-medium">{jornadasData.liga.nombre}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">División: </span>
                        <span className="text-gold-400 font-medium">{jornadasData.liga.division}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Jornada Actual: </span>
                        <span className="text-green-400 font-medium">{jornadasData.liga.jornada_actual}</span>
                    </div>
                    <div className="bg-dark-800/50 border border-white/10 rounded-lg px-4 py-2">
                        <span className="text-gray-400 text-sm">Total Jornadas: </span>
                        <span className="text-white font-medium">{jornadasData.liga.total_jornadas}</span>
                    </div>
                </div>
            )}

            {/* Navegación de Jornada */}
            {jornadasData && (
                <div className="bg-dark-800/50 border border-white/10 rounded-2xl p-4 mb-8">
                    <div className="flex items-center justify-between gap-4">
                        <button
                            onClick={() => cambiarJornada(-1)}
                            disabled={jornadaActual <= 1}
                            className="p-3 bg-dark-700 hover:bg-dark-600 disabled:opacity-30 rounded-xl transition-all"
                        >
                            <ChevronLeft className="w-5 h-5 text-white" />
                        </button>

                        <div className="flex-1 text-center">
                            <p className="text-gray-400 text-sm mb-1">Jornada</p>
                            <p className="text-3xl font-black text-white">{jornadaActual}</p>
                            {jornadaSeleccionada?.fecha && (
                                <p className="text-gray-500 text-sm mt-1">{jornadaSeleccionada.fecha}</p>
                            )}
                        </div>

                        <button
                            onClick={() => cambiarJornada(1)}
                            disabled={jornadaActual >= (jornadasData?.liga?.total_jornadas || 22)}
                            className="p-3 bg-dark-700 hover:bg-dark-600 disabled:opacity-30 rounded-xl transition-all"
                        >
                            <ChevronRight className="w-5 h-5 text-white" />
                        </button>
                    </div>

                    {/* Botón Ir a Jornada Actual */}
                    {jornadaActual !== jornadasData?.jornada_actual && (
                        <button
                            onClick={irAJornadaActual}
                            className="w-full mt-4 py-2 bg-gold-500/10 hover:bg-gold-500/20 text-gold-400 rounded-lg text-sm font-medium transition-all"
                        >
                            Ir a Jornada Actual ({jornadasData?.jornada_actual})
                        </button>
                    )}

                    {/* Indicador de progreso */}
                    <div className="mt-4">
                        <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-gold-500 rounded-full transition-all"
                                style={{ width: `${(jornadaActual / (jornadasData?.liga?.total_jornadas || 22)) * 100}%` }}
                            />
                        </div>
                        <div className="flex justify-between mt-2 text-xs text-gray-500">
                            <span>Jornada 1</span>
                            <span>Jornada {jornadasData?.liga?.total_jornadas || 22}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Partidos de la Jornada */}
            <div className="bg-dark-900/50 rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
                {!jornadaSeleccionada || jornadaSeleccionada.partidos.length === 0 ? (
                    <div className="p-16 text-center text-gray-500">
                        <Shield className="w-16 h-16 mx-auto mb-4 opacity-20" />
                        <h3 className="text-xl font-bold text-white mb-2">Sin Partidos</h3>
                        <p>No hay partidos programados para esta jornada aún.</p>
                        {ligaActual && (
                            <p className="mt-2 text-sm text-gray-600">
                                Liga: {ligaActual.division} - {ligaActual.nombre}
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {jornadaSeleccionada.partidos.map((partido) => (
                            <div 
                                key={partido.id}
                                className={`p-6 hover:bg-white/[0.02] transition-all ${
                                    partido.estado === 'finalizado' || partido.estado === 'jugado' ? 'bg-green-500/[0.02]' : ''
                                } ${partido.estado === 'pendiente' ? 'opacity-70' : ''}`}
                            >
                                <div className="flex flex-col md:flex-row items-center gap-4 md:gap-8">
                                    {/* Info del partido */}
                                    <div className="flex items-center gap-3 text-gray-500 text-sm min-w-[120px]">
                                        {partido.es_copa ? (
                                            <span className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs">
                                                🏆 {partido.ronda_copa || 'Copa'}
                                            </span>
                                        ) : (
                                            <>
                                                <Clock className="w-4 h-4" />
                                                <span>{partido.fecha_hora ? new Date(partido.fecha_hora).toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit'}) : '--:--'}</span>
                                            </>
                                        )}
                                    </div>

                                    {/* Equipo Local */}
                                    <div className="flex-1 flex items-center justify-end gap-4">
                                        <span className="text-white font-bold text-lg text-right">{partido.equipo_local}</span>
                                        <div className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center">
                                            <Shield className="w-5 h-5 text-gray-400" />
                                        </div>
                                    </div>

                                    {/* Marcador */}
                                    <div className="flex items-center gap-3 px-6">
                                        {partido.estado === 'finalizado' || partido.estado === 'jugado' || partido.estado === 'walkover' ? (
                                            <>
                                                <span className={`text-3xl font-black ${
                                                    partido.goles_local > partido.goles_visitante ? 'text-green-400' : 
                                                    partido.goles_local < partido.goles_visitante ? 'text-red-400' : 'text-white'
                                                }`}>
                                                    {partido.goles_local}
                                                </span>
                                                <span className="text-gray-500 text-2xl">-</span>
                                                <span className={`text-3xl font-black ${
                                                    partido.goles_visitante > partido.goles_local ? 'text-green-400' : 
                                                    partido.goles_visitante < partido.goles_local ? 'text-red-400' : 'text-white'
                                                }`}>
                                                    {partido.goles_visitante}
                                                </span>
                                            </>
                                        ) : partido.estado === 'pendiente' ? (
                                            <span className="text-gray-500 font-medium">VS</span>
                                        ) : (
                                            <span className="text-gray-500 text-sm">{partido.estado_display}</span>
                                        )}
                                    </div>

                                    {/* Equipo Visitante */}
                                    <div className="flex-1 flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center">
                                            <Shield className="w-5 h-5 text-gray-400" />
                                        </div>
                                        <span className="text-white font-bold text-lg">{partido.equipo_visitante}</span>
                                    </div>

                                    {/* Estado */}
                                    <div className="min-w-[100px] text-right">
                                        {partido.estado === 'finalizado' || partido.estado === 'jugado' ? (
                                            <span className="text-green-400 text-sm font-medium">Finalizado</span>
                                        ) : partido.estado === 'pendiente' ? (
                                            <span className="text-gray-500 text-sm">Pendiente</span>
                                        ) : (
                                            <span className={`text-sm ${
                                                partido.estado === 'walkover' ? 'text-yellow-400' : 'text-gray-400'
                                            }`}>{partido.estado_display}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Lista de todas las jornadas (mini) */}
            {jornadasData && jornadasData.jornadas.length > 0 && (
                <div className="mt-8 bg-dark-800/50 border border-white/10 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Todas las Jornadas</h3>
                    <div className="flex flex-wrap gap-2">
                        {Array.from({ length: jornadasData.liga?.total_jornadas || 22 }, (_, i) => i + 1).map((num) => {
                            const tienePartidos = jornadasData.jornadas.some(j => j.jornada === num);
                            const estaCompletada = jornadasData.jornadas.find(j => j.jornada === num)?.estado === 'completada';
                            
                            return (
                                <button
                                    key={num}
                                    onClick={() => setJornadaActual(num)}
                                    className={`w-10 h-10 rounded-lg font-bold text-sm transition-all ${
                                        num === jornadaActual 
                                            ? 'bg-gold-500 text-black' 
                                            : estaCompletada 
                                                ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                                : tienePartidos 
                                                    ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
                                                    : 'bg-dark-700 text-gray-500 hover:bg-dark-600'
                                    }`}
                                >
                                    {num}
                                </button>
                            );
                        })}
                    </div>
                    <div className="mt-4 flex gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-green-500/20"></div> Completada
                        </span>
                        <span className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-blue-500/20"></div> En Curso
                        </span>
                        <span className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-dark-700"></div> Sin Partidos
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Jornadas;
