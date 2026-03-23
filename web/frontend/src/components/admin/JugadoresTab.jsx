import React, { useState } from 'react';
import { Search, Edit, Save, DollarSign, UserX, Award, Shield, Target, AlertCircle, CheckSquare, Square, ArrowRight } from 'lucide-react';

/**
 * Tab de Jugadores – Buscar, precios, stats y ban.
 */
const JugadoresTab = ({
    filteredJugadores,
    jugadores,
    searchTerm,
    setSearchTerm,
    preciosJugadores,
    saving,
    handlePrecioJugadorChange,
    handleUpdatePrecio,
    handleUpdatePreciosMasivo,
    openEditStats,
    formatMoney,
    totalJugadores,
}) => {
    const [selectedJugadores, setSelectedJugadores] = useState([]);
    const [precioGeneral, setPrecioGeneral] = useState('');
    const [clausulaGeneral, setClausulaGeneral] = useState('');

    const toggleJugadorSelection = (discordId) => {
        setSelectedJugadores(prev =>
            prev.includes(discordId)
                ? prev.filter(id => id !== discordId)
                : [...prev, discordId]
        );
    };

    const selectAllJugadores = () => {
        const jugadoresToSelect = searchTerm ? filteredJugadores : jugadores;
        if (selectedJugadores.length === jugadoresToSelect.length) {
            setSelectedJugadores([]);
        } else {
            setSelectedJugadores(jugadoresToSelect.map(j => j.discord_id));
        }
    };

    const aplicarPrecioGeneral = () => {
        if (selectedJugadores.length === 0) {
            alert('⚠️ Selecciona al menos un jugador');
            return;
        }
        const precio = precioGeneral !== '' ? Number(precioGeneral) : null;
        const clausula = clausulaGeneral !== '' ? Number(clausulaGeneral) : null;
        
        if (precio === null && clausula === null) {
            alert('⚠️ Ingresa al menos un precio o cláusula');
            return;
        }
        
        const fields = [];
        if (precio !== null) fields.push(`precio $${precio}`);
        if (clausula !== null) fields.push(`cláusula $${clausula}`);
        
        if (!window.confirm(`¿Aplicar ${fields.join(' y ')} a ${selectedJugadores.length} jugadores seleccionados?`)) {
            return;
        }
        
        handleUpdatePreciosMasivo(selectedJugadores, precio || 0, clausula || 0);
        setSelectedJugadores([]);
        setPrecioGeneral('');
        setClausulaGeneral('');
    };

    return (
        <div className="space-y-6">
            {/* Header + Search */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Plantilla Global</h2>
                    <p className="text-gray-500 mt-1">{totalJugadores} jugadores registrados</p>
                </div>
                <div className="relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Buscar jugador o equipo..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-[#0d1017] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 w-72 text-white placeholder-gray-500 focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/50 focus:outline-none transition-all"
                    />
                </div>
            </div>

            {/* Precio/Cláusula General Section */}
            <div className="bg-gradient-to-r from-blue-500/10 to-blue-500/5 border border-blue-500/20 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                    <DollarSign size={20} className="text-blue-400" />
                    <h3 className="text-lg font-semibold text-white">Precio y Cláusula General</h3>
                    <span className="text-xs text-gray-400">({selectedJugadores.length} seleccionados)</span>
                </div>
                <div className="flex flex-wrap items-end gap-4">
                    <div className="flex-1 min-w-[150px]">
                        <label className="text-[11px] text-gray-500 uppercase tracking-widest mb-2 block">Precio</label>
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-bold">$</span>
                            <input
                                type="number"
                                value={precioGeneral}
                                onChange={(e) => setPrecioGeneral(e.target.value)}
                                placeholder="Ej: 50000"
                                className="w-full bg-[#161b22] border border-white/10 rounded-lg pl-7 pr-3 py-2 text-white focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all text-sm"
                            />
                        </div>
                    </div>
                    <div className="flex-1 min-w-[150px]">
                        <label className="text-[11px] text-gray-500 uppercase tracking-widest mb-2 block">Cláusula</label>
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-bold">$</span>
                            <input
                                type="number"
                                value={clausulaGeneral}
                                onChange={(e) => setClausulaGeneral(e.target.value)}
                                placeholder="Ej: 100000"
                                className="w-full bg-[#161b22] border border-white/10 rounded-lg pl-7 pr-3 py-2 text-white focus:border-blue-500/50 focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all text-sm"
                            />
                        </div>
                    </div>
                    <button
                        onClick={aplicarPrecioGeneral}
                        disabled={saving === 'precios-masivo'}
                        className="px-5 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-sm flex items-center gap-2 shadow-lg shadow-blue-500/10"
                    >
                        <ArrowRight size={16} />
                        {saving === 'precios-masivo' ? 'Aplicando...' : 'Aplicar a Seleccionados'}
                    </button>
                    <button
                        onClick={selectAllJugadores}
                        className="px-4 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 hover:text-white transition-all text-sm flex items-center gap-2"
                    >
                        {selectedJugadores.length === (searchTerm ? filteredJugadores : jugadores).length ? <Square size={16} /> : <CheckSquare size={16} />}
                        {selectedJugadores.length === (searchTerm ? filteredJugadores : jugadores).length ? 'Deseleccionar Todo' : 'Seleccionar Todo'}
                    </button>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                    * Puedes aplicar solo precio, solo cláusula, o ambos. Deja en blanco el campo que no quieras modificar.
                </p>
            </div>

            {/* Jugadores Table */}
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/10">
                                <th className="text-left px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider w-10"></th>
                                <th className="text-left px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Jugador</th>
                                <th className="text-left px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Equipo</th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Precio</th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Cláusula</th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    <div className="flex items-center justify-center gap-1"><Target size={12} /> Goles</div>
                                </th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    <div className="flex items-center justify-center gap-1"><Award size={12} /> MVP</div>
                                </th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    <div className="flex items-center justify-center gap-1"><AlertCircle size={12} /> Rojas</div>
                                </th>
                                <th className="text-center px-5 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {filteredJugadores.map((j) => {
                                const isSelected = selectedJugadores.includes(j.discord_id);
                                return (
                                    <tr key={j.discord_id} className={`hover:bg-white/[0.03] transition-colors ${j.baneado ? 'opacity-50 bg-red-500/5' : ''} ${isSelected ? 'bg-blue-500/5' : ''}`}>
                                        <td className="px-5 py-3">
                                            <button
                                                onClick={() => toggleJugadorSelection(j.discord_id)}
                                                className={`p-1 rounded transition-all ${isSelected ? 'text-blue-400' : 'text-gray-500 hover:text-gray-300'}`}
                                            >
                                                {isSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                                            </button>
                                        </td>
                                        <td className="px-5 py-3">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-500/20 to-gold-500/5 border border-gold-500/20 flex items-center justify-center text-gold-400 text-xs font-bold flex-shrink-0">
                                                    {(j.nombre || '?').charAt(0).toUpperCase()}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-sm font-medium text-white truncate">{j.nombre || 'Sin nombre'}</p>
                                                    {j.baneado && <span className="text-red-400 text-xs flex items-center gap-1"><UserX size={10} /> Baneado</span>}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-5 py-3">
                                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${j.equipo
                                                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                                : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                                                }`}>
                                                {j.equipo ? (
                                                    <span className="flex items-center gap-1"><Shield size={10} /> {j.equipo}</span>
                                                ) : (
                                                    'Agente Libre'
                                                )}
                                            </span>
                                        </td>
                                        <td className="px-5 py-3">
                                            <div className="flex items-center justify-center">
                                                <div className="relative w-20">
                                                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-xs">$</span>
                                                    <input
                                                        type="number"
                                                        value={preciosJugadores[j.discord_id]?.precio ?? j.precio ?? 0}
                                                        onChange={(e) => handlePrecioJugadorChange(j.discord_id, 'precio', e.target.value)}
                                                        className="w-full bg-[#161b22] border border-white/10 rounded px-5 py-1.5 text-center text-xs text-white focus:border-gold-500/50 focus:outline-none"
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-5 py-3">
                                            <div className="flex items-center justify-center">
                                                <div className="relative w-20">
                                                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-xs">$</span>
                                                    <input
                                                        type="number"
                                                        value={preciosJugadores[j.discord_id]?.clausula ?? j.clausula ?? 0}
                                                        onChange={(e) => handlePrecioJugadorChange(j.discord_id, 'clausula', e.target.value)}
                                                        className="w-full bg-[#161b22] border border-white/10 rounded px-5 py-1.5 text-center text-xs text-white focus:border-gold-500/50 focus:outline-none"
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-5 py-3 text-center text-sm text-white font-medium">{j.estadisticas_temporada?.goles || 0}</td>
                                        <td className="px-5 py-3 text-center text-sm text-gold-400 font-medium">{j.estadisticas_temporada?.mvps || 0}</td>
                                        <td className="px-5 py-3 text-center text-sm text-red-400 font-medium">{j.estadisticas_temporada?.rojas || 0}</td>
                                        <td className="px-5 py-3">
                                            <div className="flex items-center justify-center gap-1.5">
                                                <button
                                                    onClick={() => handleUpdatePrecio(j.discord_id)}
                                                    disabled={saving === j.discord_id}
                                                    className="p-1.5 bg-gold-500/10 text-gold-400 rounded-lg hover:bg-gold-500/20 transition-colors disabled:opacity-50"
                                                    title="Guardar precio"
                                                >
                                                    <Save size={14} />
                                                </button>
                                                <button
                                                    onClick={() => openEditStats(j)}
                                                    className="p-1.5 bg-blue-500/10 text-blue-400 rounded-lg hover:bg-blue-500/20 transition-colors"
                                                    title="Editar estadísticas"
                                                >
                                                    <Edit size={14} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Empty State */}
            {filteredJugadores.length === 0 && (
                <div className="text-center py-12">
                    <Search size={36} className="text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No se encontraron jugadores</p>
                    <p className="text-gray-600 text-sm mt-1">Intenta con otro término de búsqueda</p>
                </div>
            )}
        </div>
    );
};

export default JugadoresTab;
