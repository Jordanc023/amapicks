import React, { useState, useEffect } from 'react';
import { X, Save, AlertTriangle } from 'lucide-react';
import { ligaService } from '../../services/api';

const EditStatsModal = ({ isOpen, onClose, jugador, onSave }) => {
    const [stats, setStats] = useState({
        goles: 0,
        asistencias: 0,
        mvps: 0,
        amarillas: 0,
        rojas: 0
    });
    const [baneado, setBaneado] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (jugador) {
            setStats({
                goles: jugador.estadisticas_temporada?.goles || 0,
                asistencias: jugador.estadisticas_temporada?.asistencias || 0,
                mvps: jugador.estadisticas_temporada?.mvps || 0,
                amarillas: jugador.estadisticas_temporada?.amarillas || 0,
                rojas: jugador.estadisticas_temporada?.rojas || 0
            });
            setBaneado(jugador.baneado || false);
        }
    }, [jugador]);

    if (!isOpen || !jugador) return null;

    const handleChange = (e) => {
        const { name, value } = e.target;
        setStats(prev => ({ ...prev, [name]: parseInt(value) || 0 }));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await ligaService.updatePlayerStats(jugador.discord_id, stats);
            if (baneado !== (jugador.baneado || false)) {
                await ligaService.updatePlayerBan(jugador.discord_id, baneado, "Actualizado por Admin Web");
            }
            onSave(jugador.discord_id, stats, baneado);
            onClose();
        } catch (error) {
            console.error(error);
            alert("Error al guardar estadísticas");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
            <div className="bg-dark-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-black/20">
                    <div>
                        <h2 className="text-xl font-display font-black text-white uppercase flex items-center gap-2">
                            Editar Jugador
                        </h2>
                        <p className="text-gray-400 text-sm">{jugador.nombre}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                {/* Form */}
                <div className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs uppercase font-bold text-gray-500 mb-1">Goles</label>
                            <input type="number" name="goles" value={stats.goles} onChange={handleChange} className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:border-gold-500 outline-none" />
                        </div>
                        <div>
                            <label className="block text-xs uppercase font-bold text-gray-500 mb-1">Asistencias</label>
                            <input type="number" name="asistencias" value={stats.asistencias} onChange={handleChange} className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:border-gold-500 outline-none" />
                        </div>
                        <div className="col-span-2">
                            <label className="block text-xs uppercase font-bold text-gray-500 mb-1">MVPs</label>
                            <input type="number" name="mvps" value={stats.mvps} onChange={handleChange} className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:border-gold-500 outline-none" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs uppercase font-bold text-gray-500 mb-1 flex items-center gap-1">
                                <div className="w-2 h-3 bg-yellow-500 rounded-sm"></div> Amarillas
                            </label>
                            <input type="number" name="amarillas" value={stats.amarillas} onChange={handleChange} className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:border-gold-500 outline-none" />
                        </div>
                        <div>
                            <label className="block text-xs uppercase font-bold text-gray-500 mb-1 flex items-center gap-1">
                                <div className="w-2 h-3 bg-red-500 rounded-sm"></div> Rojas
                            </label>
                            <input type="number" name="rojas" value={stats.rojas} onChange={handleChange} className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:border-gold-500 outline-none" />
                        </div>
                    </div>

                    <div className="pt-4 border-t border-white/10 mt-6">
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={baneado}
                                onChange={(e) => setBaneado(e.target.checked)}
                                className="w-5 h-5 rounded border-white/20 bg-black/40 text-red-500 focus:ring-red-500 focus:ring-offset-dark-900"
                            />
                            <span className="text-white font-bold flex items-center gap-2">
                                <AlertTriangle size={18} className={baneado ? "text-red-500" : "text-gray-500"} />
                                Jugador Baneado
                            </span>
                        </label>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10 bg-black/20 flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 border border-white/10 text-white rounded-xl hover:bg-white/5 transition-colors font-bold uppercase text-sm"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 px-4 py-2 bg-gold-500 text-black rounded-xl hover:bg-gold-400 disabled:opacity-50 transition-colors font-bold uppercase text-sm flex items-center justify-center gap-2"
                    >
                        {saving ? "Guardando..." : <><Save size={18} /> Guardar</>}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EditStatsModal;
