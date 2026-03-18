import React, { useState } from 'react';
import { X, Calendar, MapPin, Clock } from 'lucide-react';

const CreatePartidoModal = ({ isOpen, onClose, equipos, onSave }) => {
    const [formData, setFormData] = useState({
        equipo_local: '',
        equipo_visitante: '',
        fecha: '',
        hora: '',
        jornada: '',
        fase: 'Liga Regular'
    });
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (formData.equipo_local === formData.equipo_visitante) {
            alert("No puedes programar un partido del mismo equipo contra sí mismo.");
            return;
        }
        if (!formData.equipo_local || !formData.equipo_visitante || !formData.fecha || !formData.hora) {
            alert("Completa los campos obligatorios.");
            return;
        }

        // Parse date for DB: YYYY-MM-DDTHH:mm:ss
        const dtString = `${formData.fecha}T${formData.hora}:00`;
        const dateObj = new Date(dtString);

        if (isNaN(dateObj.getTime())) {
            alert("Fecha / Hora inválida.");
            return;
        }

        setLoading(true);
        try {
            await onSave({
                equipo_local: formData.equipo_local,
                equipo_visitante: formData.equipo_visitante,
                fecha_hora: dateObj.toISOString(),
                jornada: parseInt(formData.jornada) || null,
                fase: formData.fase
            });
            onClose();
        } catch (error) {
            console.error("Error al guardar:", error);
            alert("Ocurrió un error programando el partido.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-dark-900 border border-white/10 rounded-3xl w-full max-w-lg overflow-hidden shadow-2xl relative">
                {/* Header */}
                <div className="bg-dark-800 p-6 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gold-500/20 flex items-center justify-center border border-gold-500/30">
                            <Calendar className="text-gold-500" size={20} />
                        </div>
                        <h2 className="text-xl font-display font-black text-white uppercase">
                            Nuevo Partido
                        </h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">

                    {/* Equipos */}
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex-1">
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Local</label>
                            <select
                                value={formData.equipo_local}
                                onChange={(e) => setFormData({ ...formData, equipo_local: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                                required
                            >
                                <option value="">Selecciona...</option>
                                {equipos.map(eq => <option key={`loc-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                        <div className="text-gray-500 font-black mt-6">VS</div>
                        <div className="flex-1">
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Visitante</label>
                            <select
                                value={formData.equipo_visitante}
                                onChange={(e) => setFormData({ ...formData, equipo_visitante: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                                required
                            >
                                <option value="">Selecciona...</option>
                                {equipos.map(eq => <option key={`vis-${eq.nombre}`} value={eq.nombre}>{eq.nombre}</option>)}
                            </select>
                        </div>
                    </div>

                    {/* Fecha y Hora */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                <Calendar size={12} className="inline mr-1" /> Fecha
                            </label>
                            <input
                                type="date"
                                value={formData.fecha}
                                onChange={(e) => setFormData({ ...formData, fecha: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                <Clock size={12} className="inline mr-1" /> Hora Local
                            </label>
                            <input
                                type="time"
                                value={formData.hora}
                                onChange={(e) => setFormData({ ...formData, hora: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                                required
                            />
                        </div>
                    </div>

                    {/* Metadata de Liga */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Fase</label>
                            <select
                                value={formData.fase}
                                onChange={(e) => setFormData({ ...formData, fase: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                            >
                                <option value="Liga Regular">Liga Regular</option>
                                <option value="Fase de Grupos">Fase de Grupos</option>
                                <option value="Cuartos de Final">Cuartos de Final</option>
                                <option value="Semifinal">Semifinal</option>
                                <option value="Gran Final">Gran Final</option>
                                <option value="Amistoso">Amistoso</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Jornada (Opcional)</label>
                            <input
                                type="number"
                                min="1"
                                placeholder="Ej: 3"
                                value={formData.jornada}
                                onChange={(e) => setFormData({ ...formData, jornada: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-gold-500 outline-none"
                            />
                        </div>
                    </div>

                    <div className="pt-4 border-t border-white/5 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-3 bg-white/5 text-gray-300 font-bold uppercase rounded-xl hover:bg-white/10 transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-gold-500 text-black font-bold uppercase rounded-xl hover:bg-gold-400 transition-colors"
                        >
                            {loading ? 'Guardando...' : 'Programar'}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default CreatePartidoModal;
