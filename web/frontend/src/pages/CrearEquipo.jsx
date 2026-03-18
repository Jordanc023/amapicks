import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import { Shield, Sparkles, Paintbrush, Link as LinkIcon, AlertCircle, CheckCircle2 } from 'lucide-react';

// Setup local api instance just for this view so it embeds token automatically
const api = axios.create({
    baseURL: 'http://20.81.152.127:8001/api',
});
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

const CrearEquipo = () => {
    const { user, loading } = useAuth();

    const [formData, setFormData] = useState({
        nombre: '',
        color: '#ff0044',
        logo: null,
        logoPreview: ''
    });

    const [status, setStatus] = useState({ status: 'idle', message: '' }); // idle | loading | success | error

    if (loading) return <div className="min-h-screen text-white flex items-center justify-center">Verificando tu licencia...</div>;

    // Redirecciones de seguridad
    if (!user) {
        return <Navigate to="/" />;
    }

    if (!user.es_dt) {
        return (
            <div className="min-h-screen pt-20 flex px-4 items-center justify-center bg-black/90">
                <div className="bg-red-500/10 border border-red-500/20 p-8 rounded-2xl max-w-lg text-center">
                    <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-2">Acceso Denegado</h2>
                    <p className="text-gray-400">No posees una Licencia de Director Técnico Activa. Habla con la administración para tramitar tu pase oficial.</p>
                </div>
            </div>
        );
    }

    if (user.team_name && status.status !== 'success') {
        return <Navigate to="/equipo" />;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus({ status: 'loading', message: '' });

        if (!formData.logo) {
            setStatus({ status: 'error', message: 'Por favor, selecciona una imagen para el escudo.' });
            return;
        }

        const data = new FormData();
        data.append('nombre', formData.nombre);
        data.append('color', formData.color);
        data.append('logo', formData.logo);

        try {
            const res = await api.post('/club/fundar', data, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setStatus({ status: 'success', message: res.data.message });
        } catch (error) {
            const msg = error.response?.data?.detail || "Ha ocurrido un error al intentar fundar tu club.";
            setStatus({ status: 'error', message: msg });
        }
    };

    if (status.status === 'success') {
        return (
            <div className="min-h-screen pt-20 px-4 flex flex-col items-center justify-center bg-black/95 bg-[url('/grid-pattern.svg')]">
                <div className="animate-in zoom-in duration-500 flex flex-col items-center">
                    <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mb-6 relative">
                        <CheckCircle2 className="w-12 h-12 text-green-400" />
                        <div className="absolute inset-0 rounded-full border-4 border-green-500/30 animate-ping" style={{ animationDuration: '3s' }}></div>
                    </div>
                    <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-yellow-500 mb-2 text-center uppercase tracking-widest">
                        ¡Legado Inaugurado!
                    </h1>
                    <p className="text-gray-400 max-w-md text-center mb-8">
                        {status.message}
                    </p>
                    <a href="discord://-"
                        className="bg-[#5865F2] hover:bg-[#4752C4] px-8 py-3 rounded-xl font-bold text-white transition-all hover:scale-105 shadow-[0_0_20px_rgba(88,101,242,0.4)]">
                        Regresar a Discord
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-0 inset-x-0 h-[500px] bg-gradient-to-b from-indigo-900/20 to-transparent pointer-events-none" />
            <div
                className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-blue-600/20 blur-[120px] rounded-full pointer-events-none transition-colors duration-1000"
                style={{ backgroundColor: `${formData.color}20` }}
            />

            <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 relative z-10">
                {/* Lado Izquierdo - Formulario */}
                <div>
                    <div className="mb-10">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold-500/10 border border-gold-500/30 text-gold-400 text-xs font-bold uppercase tracking-wider mb-4">
                            <Sparkles size={14} /> Sistema Fundador
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black text-white mb-4 tracking-tight leading-tight">
                            Diseña tu propio <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500" style={{ backgroundImage: `linear-gradient(to right, white, ${formData.color})` }}>
                                Club Deportivo
                            </span>
                        </h1>
                        <p className="text-gray-400 text-lg">
                            Has recibido una licencia oficial. Ingresa los datos que forjarán la identidad de tu equipo en toda la liga AMAPICKS.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Error box */}
                        {status.status === 'error' && (
                            <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl flex items-start gap-3 animate-in fade-in">
                                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <p className="text-sm">{status.message}</p>
                            </div>
                        )}

                        {/* Campo Nombre */}
                        <div className="bg-black/40 border border-white/10 p-6 rounded-2xl backdrop-blur-md">
                            <label className="text-sm font-bold text-gray-300 uppercase tracking-wider block mb-2">Nombre de la Franquicia</label>
                            <input
                                type="text"
                                required
                                minLength="3"
                                maxLength="32"
                                value={formData.nombre}
                                onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                                placeholder="Ej: Real Madrid, Los Santos FC..."
                                className="w-full bg-[#0a0a0a] border border-white/5 rounded-xl px-4 py-3 text-white text-lg focus:border-blue-500/50 focus:outline-none transition-colors"
                            />
                        </div>

                        {/* Campo Color */}
                        <div className="bg-black/40 border border-white/10 p-6 rounded-2xl backdrop-blur-md">
                            <div className="flex items-center gap-2 mb-2">
                                <Paintbrush className="w-4 h-4 text-gray-400" />
                                <label className="text-sm font-bold text-gray-300 uppercase tracking-wider block">Color Institucional</label>
                            </div>
                            <div className="flex gap-4 items-center">
                                <div className="relative w-14 h-14 rounded-xl overflow-hidden shadow-lg border border-white/20 shrink-0">
                                    <input
                                        type="color"
                                        value={formData.color}
                                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                                        className="absolute -top-2 -left-2 w-20 h-20 cursor-pointer"
                                    />
                                </div>
                                <div className="w-full">
                                    <input
                                        type="text"
                                        value={formData.color}
                                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                                        className="w-full bg-[#0a0a0a] border border-white/5 rounded-xl px-4 py-3 text-white font-mono focus:border-blue-500/50 focus:outline-none transition-colors uppercase"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Campo Escudo */}
                        <div className="bg-black/40 border border-white/10 p-6 rounded-2xl backdrop-blur-md">
                            <div className="flex items-center gap-2 mb-2">
                                <LinkIcon className="w-4 h-4 text-gray-400" />
                                <label className="text-sm font-bold text-gray-300 uppercase tracking-wider block">Escudo del Club</label>
                            </div>
                            <input
                                type="file"
                                accept="image/*"
                                required
                                onChange={(e) => {
                                    const file = e.target.files[0];
                                    if (file) {
                                        setFormData({
                                            ...formData,
                                            logo: file,
                                            logoPreview: URL.createObjectURL(file)
                                        });
                                    }
                                }}
                                className="w-full bg-[#0a0a0a] border border-white/5 rounded-xl px-4 py-3 text-white focus:border-blue-500/50 focus:outline-none transition-colors file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-bold file:bg-[#1a1a1a] file:text-white hover:file:bg-[#2a2a2a] cursor-pointer"
                            />
                            <p className="text-xs text-gray-500 mt-2">Recomendado: Imagen PNG transparente cuadrada.</p>
                        </div>

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={status.status === 'loading'}
                            className="w-full group relative overflow-hidden rounded-2xl p-[2px]"
                        >
                            <span className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 group-hover:from-blue-400 group-hover:via-purple-400 group-hover:to-pink-400 transition-colors animate-[spin_3s_linear_infinite]"
                                style={{ backgroundImage: `linear-gradient(to right, ${formData.color}, white, ${formData.color})` }} />
                            <span className="relative block h-full w-full bg-black/80 backdrop-blur-sm rounded-2xl px-8 py-4 text-lg font-bold text-white transition hover:bg-black/60">
                                {status.status === 'loading' ? 'Registrando en los servidores...' : 'Forjar Equipo Ahora'}
                            </span>
                        </button>
                    </form>
                </div>

                {/* Lado Derecho - Preview */}
                <div className="lg:pl-10 lg:sticky lg:top-32 h-fit">
                    <p className="text-gray-500 text-sm font-bold uppercase tracking-widest text-center mb-6">Previsualización en Vivo</p>

                    {/* Tarjeta de Equipo Preview */}
                    <div className="relative group perspective-1000">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-white/0 rounded-3xl blur-xl transition-opacity opacity-50" style={{ backgroundColor: `${formData.color}30` }}></div>

                        <div
                            className="relative bg-[#0f1219] border border-white/10 rounded-3xl p-8 overflow-hidden shadow-2xl transition-transform duration-500 hover:rotate-y-12"
                            style={{ boxShadow: `0 20px 40px -10px ${formData.color}40` }}
                        >
                            {/* Accent line top */}
                            <div className="absolute top-0 inset-x-0 h-2 transition-colors duration-500" style={{ backgroundColor: formData.color }}></div>

                            {/* Background blur ring */}
                            <div className="absolute -top-20 -right-20 w-64 h-64 bg-white opacity-5 blur-3xl rounded-full" style={{ backgroundColor: formData.color }}></div>

                            <div className="relative z-10 flex flex-col items-center">
                                {/* Escudo Proxy */}
                                <div className="w-40 h-40 mb-8 flex items-center justify-center relative">
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-full blur-md"></div>
                                    {formData.logoPreview ? (
                                        <img
                                            src={formData.logoPreview}
                                            alt="Escudo Previo"
                                            className="w-full h-full object-contain filter drop-shadow-2xl transition-all duration-500 hover:scale-110"
                                            onError={(e) => { e.target.onerror = null; e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                                        />
                                    ) : null}
                                    <div className="w-32 h-32 bg-black/40 rounded-full border-2 border-dashed border-white/20 flex items-center justify-center backdrop-blur-sm"
                                        style={{ display: formData.logoPreview ? 'none' : 'flex' }}>
                                        <Shield className="w-12 h-12 text-white/20" />
                                    </div>
                                </div>

                                {/* Texts */}
                                <h2 className="text-3xl font-black text-white text-center uppercase tracking-tight mb-2 truncate w-full px-4">
                                    {formData.nombre || 'TU EQUIPO AQUÍ'}
                                </h2>

                                <div className="flex items-center gap-2 mt-4">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: formData.color }}></div>
                                    <span className="text-gray-400 text-sm font-mono">{formData.color}</span>
                                </div>

                                {/* Decorational stats skeleton */}
                                <div className="w-full grid grid-cols-2 gap-3 mt-8 pt-6 border-t border-white/5 opacity-50">
                                    <div className="bg-black/30 p-3 rounded-xl border border-white/5">
                                        <div className="h-2 w-12 bg-white/10 rounded mb-2"></div>
                                        <div className="h-4 w-20 bg-white/20 rounded"></div>
                                    </div>
                                    <div className="bg-black/30 p-3 rounded-xl border border-white/5">
                                        <div className="h-2 w-12 bg-white/10 rounded mb-2"></div>
                                        <div className="h-4 w-20 bg-white/20 rounded"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CrearEquipo;
