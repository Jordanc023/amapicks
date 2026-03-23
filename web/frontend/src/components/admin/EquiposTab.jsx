import React, { useState } from 'react';
import { Shield, DollarSign, Save, Users, UserPlus, CheckSquare, Square, ArrowRight } from 'lucide-react';

/**
 * Tab de Equipos – Gestión de plantillas y presupuestos.
 */
const EquiposTab = ({
    equipos,
    presupuestos,
    saving,
    handlePresupuestoChange,
    handleUpdatePresupuesto,
    handleUpdatePresupuestosMasivo,
    formatMoney,
}) => {
    const [selectedEquipos, setSelectedEquipos] = useState([]);
    const [presupuestoGeneral, setPresupuestoGeneral] = useState('');

    const toggleEquipoSelection = (equipoId) => {
        setSelectedEquipos(prev =>
            prev.includes(equipoId)
                ? prev.filter(id => id !== equipoId)
                : [...prev, equipoId]
        );
    };

    const selectAllEquipos = () => {
        if (selectedEquipos.length === equipos.length) {
            setSelectedEquipos([]);
        } else {
            setSelectedEquipos(equipos.map(eq => eq.role_id || eq.nombre));
        }
    };

    const aplicarPresupuestoGeneral = () => {
        if (selectedEquipos.length === 0) {
            alert('⚠️ Selecciona al menos un equipo');
            return;
        }
        if (!presupuestoGeneral || presupuestoGeneral < 0) {
            alert('⚠️ Ingresa un presupuesto válido');
            return;
        }
        if (!window.confirm(`¿Aplicar $${presupuestoGeneral} a ${selectedEquipos.length} equipos seleccionados?`)) {
            return;
        }
        handleUpdatePresupuestosMasivo(selectedEquipos, Number(presupuestoGeneral));
        setSelectedEquipos([]);
        setPresupuestoGeneral('');
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-end pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Equipos Registrados</h2>
                    <p className="text-gray-500 mt-1">
                        {equipos.length} equipos activos en la liga
                    </p>
                </div>
            </div>

            {/* Presupuesto General Section */}
            <div className="bg-gradient-to-r from-gold-500/10 to-gold-500/5 border border-gold-500/20 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                    <DollarSign size={20} className="text-gold-400" />
                    <h3 className="text-lg font-semibold text-white">Presupuesto General</h3>
                    <span className="text-xs text-gray-400">({selectedEquipos.length} seleccionados)</span>
                </div>
                <div className="flex flex-wrap items-end gap-4">
                    <div className="flex-1 min-w-[200px]">
                        <label className="text-[11px] text-gray-500 uppercase tracking-widest mb-2 block">Presupuesto a Aplicar</label>
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-bold">$</span>
                            <input
                                type="number"
                                value={presupuestoGeneral}
                                onChange={(e) => setPresupuestoGeneral(e.target.value)}
                                placeholder="Ej: 1000000"
                                className="w-full bg-[#161b22] border border-white/10 rounded-lg pl-7 pr-3 py-2 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 transition-all text-sm"
                            />
                        </div>
                    </div>
                    <button
                        onClick={aplicarPresupuestoGeneral}
                        disabled={saving === 'presupuestos-masivo'}
                        className="px-5 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-sm flex items-center gap-2 shadow-lg shadow-gold-500/10"
                    >
                        <ArrowRight size={16} />
                        {saving === 'presupuestos-masivo' ? 'Aplicando...' : 'Aplicar a Seleccionados'}
                    </button>
                    <button
                        onClick={selectAllEquipos}
                        className="px-4 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 hover:text-white transition-all text-sm flex items-center gap-2"
                    >
                        {selectedEquipos.length === equipos.length ? <Square size={16} /> : <CheckSquare size={16} />}
                        {selectedEquipos.length === equipos.length ? 'Deseleccionar Todo' : 'Seleccionar Todo'}
                    </button>
                </div>
            </div>

            {/* Equipos Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {equipos.map((equipo) => {
                    const eqId = equipo.role_id || equipo.nombre;
                    const jugadoresCount = equipo.jugadores?.length || 0;
                    const isSelected = selectedEquipos.includes(eqId);

                    return (
                        <div
                            key={eqId}
                            className={`group relative bg-gradient-to-br from-white/[0.05] to-white/[0.02] border rounded-2xl overflow-hidden hover:border-gold-500/30 hover:shadow-[0_0_30px_rgba(234,179,8,0.1)] transition-all duration-500 ${
                                isSelected ? 'border-gold-500/50 shadow-[0_0_20px_rgba(234,179,8,0.15)]' : 'border-white/10'
                            }`}
                        >
                            {/* Color Accent */}
                            <div className={`absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-gold-500/50 via-gold-500 to-gold-500/50 transition-opacity duration-500 ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}></div>

                            {/* Checkbox */}
                            <div className="absolute top-3 right-3 z-10">
                                <button
                                    onClick={() => toggleEquipoSelection(eqId)}
                                    className={`p-1.5 rounded-lg transition-all ${isSelected ? 'bg-gold-500 text-black' : 'bg-white/10 text-gray-400 hover:text-white'}`}
                                >
                                    {isSelected ? <CheckSquare size={16} /> : <Square size={16} />}
                                </button>
                            </div>

                            {/* Body */}
                            <div className="p-5">
                                <div className="flex items-start gap-4">
                                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-gold-500/20 to-gold-500/5 border border-gold-500/20 flex items-center justify-center flex-shrink-0 shadow-inner">
                                        {equipo.logo_url ? (
                                            <img src={equipo.logo_url} alt={equipo.nombre} className="w-10 h-10 rounded-lg object-cover" />
                                        ) : (
                                            <Shield size={24} className="text-gold-400" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0 pr-8">
                                        <h3 className="text-lg font-semibold text-white truncate">{equipo.nombre}</h3>
                                        <div className="flex items-center gap-3 mt-1">
                                            <span className="flex items-center gap-1 text-gray-400 text-xs">
                                                <Users size={12} /> {jugadoresCount} jugadores
                                            </span>
                                            <span className="flex items-center gap-1 text-gold-400 text-xs font-medium">
                                                <DollarSign size={12} /> {formatMoney(equipo.presupuesto || 0)}
                                            </span>
                                        </div>
                                        {equipo.dt && (
                                            <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                                                <UserPlus size={12} />
                                                <span>DT: {equipo.dt}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Presupuesto Control */}
                                <div className="mt-4 pt-4 border-t border-white/5">
                                    <label className="text-[11px] text-gray-500 uppercase tracking-widest mb-2 block">Presupuesto</label>
                                    <div className="flex gap-2">
                                        <div className="relative flex-1">
                                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-bold">$</span>
                                            <input
                                                type="number"
                                                value={presupuestos[eqId] ?? equipo.presupuesto ?? 0}
                                                onChange={(e) => handlePresupuestoChange(eqId, e.target.value)}
                                                className="w-full bg-[#161b22] border border-white/10 rounded-lg pl-7 pr-3 py-2 text-white focus:border-gold-500/50 focus:outline-none focus:ring-1 focus:ring-gold-500/50 transition-all text-sm"
                                            />
                                        </div>
                                        <button
                                            onClick={() => handleUpdatePresupuesto(eqId)}
                                            disabled={saving === eqId}
                                            className="px-4 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-sm flex items-center gap-1.5 shadow-lg shadow-gold-500/10"
                                        >
                                            <Save size={14} />
                                            {saving === eqId ? '...' : 'Guardar'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Empty State */}
            {equipos.length === 0 && (
                <div className="text-center py-16">
                    <Shield size={48} className="text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">No hay equipos registrados</p>
                    <p className="text-gray-600 text-sm mt-2">Los equipos se crean desde Discord mediante el comando /crear-equipo</p>
                </div>
            )}
        </div>
    );
};

export default EquiposTab;
