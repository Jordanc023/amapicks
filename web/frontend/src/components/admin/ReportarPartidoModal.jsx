import React, { useState, useEffect } from 'react';
import { X, Trophy, AlertTriangle, FileText } from 'lucide-react';

const ReportarPartidoModal = ({ isOpen, onClose, partido, onSave }) => {
    const [formData, setFormData] = useState({
        goles_local: 0,
        goles_visitante: 0,
        notas_admin: '',
        evidencia_url: '',
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && partido) {
            setFormData({
                goles_local: 0,
                goles_visitante: 0,
                notas_admin: '',
                evidencia_url: '',
            });
            setLoading(false);
        }
    }, [isOpen, partido]);

    if (!isOpen || !partido) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();

        const golesLocal = parseInt(formData.goles_local);
        const golesVisitante = parseInt(formData.goles_visitante);

        if (isNaN(golesLocal) || isNaN(golesVisitante) || golesLocal < 0 || golesVisitante < 0) {
            alert("Los goles deben ser números válidos y no negativos.");
            return;
        }

        if (!window.confirm(
            `🔴 ADVERTENCIA: Esta acción modificará la Clasificación Oficial y no se puede deshacer.\n\n` +
            `${partido.equipo_local} ${golesLocal} - ${golesVisitante} ${partido.equipo_visitante}\n\n` +
            `¿Estás seguro de enviar este resultado?`
        )) return;

        setLoading(true);
        try {
            await onSave(partido._id, {
                goles_local: golesLocal,
                goles_visitante: golesVisitante,
                jugadores_local: [],
                jugadores_visitante: [],
                notas_admin: formData.notas_admin || null,
                evidencia_url: formData.evidencia_url || null,
            });
            onClose();
        } catch (error) {
            console.error("Error al reportar:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-dark-900 border border-gold-500/20 rounded-3xl w-full max-w-lg overflow-hidden shadow-2xl relative">
                {/* Header */}
                <div className="bg-dark-800 p-6 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gold-500/20 flex items-center justify-center border border-gold-500/30">
                            <Trophy className="text-gold-500" size={20} />
                        </div>
                        <div>
                            <h2 className="text-xl font-display font-black text-white uppercase tracking-wider">
                                Reportar Resultado
                            </h2>
                            <p className="text-xs text-gray-500 mt-0.5">
                                {partido.fase || 'Liga Regular'}{partido.jornada ? ` — Jornada ${partido.jornada}` : ''}
                            </p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Info Box */}
                <div className="bg-red-500/10 border-b border-red-500/20 p-4 flex items-start gap-3">
                    <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
                    <p className="text-xs text-red-400 font-medium">Al presionar GUARDAR, el partido finalizará inmediatamente y los puntos y goles impactarán la tabla de posiciones en tiempo real.</p>
                </div>

                {/* Body Form */}
                <form onSubmit={handleSubmit} className="p-8">

                    <div className="flex items-center justify-center gap-8 mb-8">
                        {/* Eq Local */}
                        <div className="text-center flex-1">
                            <h3 className="text-lg font-bold text-white mb-4 line-clamp-1" title={partido.equipo_local}>
                                {partido.equipo_local}
                            </h3>
                            <input
                                type="number"
                                min="0"
                                value={formData.goles_local}
                                onChange={(e) => setFormData({ ...formData, goles_local: e.target.value })}
                                className="w-24 text-center text-4xl font-black bg-black/40 border border-white/10 rounded-2xl py-4 text-gold-400 focus:border-gold-500 outline-none shadow-inner mx-auto block"
                                required
                            />
                            <span className="block text-xs font-bold text-gray-500 uppercase tracking-widest mt-3">Local</span>
                        </div>

                        <div className="text-2xl font-black text-gray-600 mb-6">VS</div>

                        {/* Eq Visitante */}
                        <div className="text-center flex-1">
                            <h3 className="text-lg font-bold text-white mb-4 line-clamp-1" title={partido.equipo_visitante}>
                                {partido.equipo_visitante}
                            </h3>
                            <input
                                type="number"
                                min="0"
                                value={formData.goles_visitante}
                                onChange={(e) => setFormData({ ...formData, goles_visitante: e.target.value })}
                                className="w-24 text-center text-4xl font-black bg-black/40 border border-white/10 rounded-2xl py-4 text-gold-400 focus:border-gold-500 outline-none shadow-inner mx-auto block"
                                required
                            />
                            <span className="block text-xs font-bold text-gray-500 uppercase tracking-widest mt-3">Visitante</span>
                        </div>
                    </div>

                    {/* Notas y Evidencia */}
                    <div className="space-y-4 mb-6">
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <FileText size={12} /> Notas del Reporte (Opcional)
                            </label>
                            <textarea
                                value={formData.notas_admin}
                                onChange={(e) => setFormData({ ...formData, notas_admin: e.target.value })}
                                placeholder="Ej: Partido suspendido en min 70 por lluvia..."
                                rows={2}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:border-gold-500 outline-none resize-none placeholder-gray-600"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                URL de Evidencia (Opcional)
                            </label>
                            <input
                                type="url"
                                value={formData.evidencia_url}
                                onChange={(e) => setFormData({ ...formData, evidencia_url: e.target.value })}
                                placeholder="https://imgur.com/screenshot..."
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:border-gold-500 outline-none placeholder-gray-600"
                            />
                        </div>
                    </div>

                    <div className="pt-6 border-t border-white/5 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-4 bg-white/5 text-gray-300 font-bold uppercase tracking-wider rounded-xl hover:bg-white/10 transition-colors text-sm"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-4 bg-gold-500 text-black font-black uppercase tracking-wider rounded-xl hover:bg-gold-400 transition-all hover:scale-[1.02] shadow-lg shadow-gold-500/20 text-sm"
                        >
                            {loading ? 'Procesando...' : 'GUARDAR RESULTADO'}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default ReportarPartidoModal;
