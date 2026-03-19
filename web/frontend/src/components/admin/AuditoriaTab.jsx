import React from 'react';
import { Clock, User, FileText, Check, X, AlertTriangle, Shield, DollarSign } from 'lucide-react';

/**
 * Tab de Auditoría – Log de acciones recientes del sistema.
 */
const AuditoriaTab = ({ auditoriaLogs }) => {
    const getEventIcon = (tipo) => {
        const icons = {
            'fichaje': <DollarSign size={14} className="text-green-400" />,
            'venta': <DollarSign size={14} className="text-red-400" />,
            'resultado': <Check size={14} className="text-blue-400" />,
            'walkover': <X size={14} className="text-orange-400" />,
            'sancion': <AlertTriangle size={14} className="text-red-400" />,
            'creacion_equipo': <Shield size={14} className="text-purple-400" />,
        };
        return icons[tipo] || <FileText size={14} className="text-gray-400" />;
    };

    const getEventBadge = (tipo) => {
        const badges = {
            'fichaje': 'bg-green-500/10 text-green-400 border border-green-500/20',
            'venta': 'bg-red-500/10 text-red-400 border border-red-500/20',
            'resultado': 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
            'walkover': 'bg-orange-500/10 text-orange-400 border border-orange-500/20',
            'sancion': 'bg-red-500/10 text-red-400 border border-red-500/20',
            'creacion_equipo': 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
        };
        return badges[tipo] || 'bg-gray-500/10 text-gray-400 border border-gray-500/20';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-end pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Auditoría</h2>
                    <p className="text-gray-500 mt-1">Registro de acciones recientes en el sistema</p>
                </div>
                <span className="px-3 py-1 bg-white/5 text-gray-400 rounded-full text-xs font-medium border border-white/10">
                    {auditoriaLogs.length} registros
                </span>
            </div>

            {/* Log List */}
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden">
                <div className="max-h-[600px] overflow-y-auto">
                    {auditoriaLogs.length > 0 ? (
                        <div className="divide-y divide-white/5">
                            {auditoriaLogs.map((log, index) => (
                                <div key={log._id || index} className="flex items-start gap-4 p-4 hover:bg-white/[0.03] transition-colors">
                                    {/* Icon */}
                                    <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                        {getEventIcon(log.tipo)}
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${getEventBadge(log.tipo)}`}>
                                                {log.tipo}
                                            </span>
                                            {log.usuario && (
                                                <span className="flex items-center gap-1 text-xs text-gray-500">
                                                    <User size={10} /> {log.usuario}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-200 mt-1">{log.descripcion || log.detalle || 'Sin descripción'}</p>
                                    </div>

                                    {/* Timestamp */}
                                    <div className="flex items-center gap-1 text-xs text-gray-600 flex-shrink-0 mt-0.5">
                                        <Clock size={12} />
                                        <span>
                                            {log.fecha ? new Date(log.fecha).toLocaleString('es', {
                                                day: '2-digit',
                                                month: '2-digit',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            }) : '--'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-16">
                            <FileText size={36} className="text-gray-600 mx-auto mb-3" />
                            <p className="text-gray-400">No hay registros de auditoría</p>
                            <p className="text-gray-600 text-sm mt-1">Las acciones del sistema aparecerán aquí</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AuditoriaTab;
