import React from 'react';
import {
    Activity, FileText, Settings, AlertTriangle, RefreshCw, RotateCcw,
    Ban, ChevronDown, Save, Trash2
} from 'lucide-react';

/**
 * Tab de Sistema – Sub-tabs: Control y Anuncios, Ajustes Globales, Zona de Peligro.
 */
const SistemaTab = ({
    // Sub-tab state
    activeSystemTab,
    setActiveSystemTab,
    // System status
    systemStatus,
    // Saving
    saving,
    // Handlers
    handleSyncCommands,
    handlePM2Action,
    handleSendAnnouncement,
    handleSaveGlobalConfig,
    handleBackup,
    handleResetSeason,
    handleFullReset,
    handleNuke,
    handlePurgeLogs,
    // Config
    globalConfig,
    setGlobalConfig,
    loadingConfig,
    // Anuncio form
    anuncioForm,
    setAnuncioForm,
}) => {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-end pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Centro de Sistema</h2>
                    <p className="text-gray-500 mt-1">Supervisión del Bot, Ajustes Globales y Mantenimiento Avanzado</p>
                </div>
            </div>

            {/* Sub-Tabs */}
            <div className="flex bg-[#0d1017] p-1.5 rounded-2xl border border-white/5 mx-auto max-w-2xl mb-8">
                <button
                    onClick={() => setActiveSystemTab('general')}
                    className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all ${activeSystemTab === 'general' ? 'bg-blue-500/20 text-blue-400 shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                >
                    Control y Anuncios
                </button>
                <button
                    onClick={() => setActiveSystemTab('config')}
                    className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all ${activeSystemTab === 'config' ? 'bg-gold-500/20 text-gold-400 shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                >
                    Ajustes Globales
                </button>
                <button
                    onClick={() => setActiveSystemTab('peligro')}
                    className={`flex-1 py-3 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2 ${activeSystemTab === 'peligro' ? 'bg-red-500/20 text-red-500 shadow-lg' : 'text-red-500/50 hover:text-red-400 hover:bg-white/5'}`}
                >
                    <AlertTriangle size={16} /> Zona Precaución
                </button>
            </div>

            <div className="max-w-4xl mx-auto">

                {/* 1. TAB GENERAL */}
                {activeSystemTab === 'general' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Bloque: Control del Bot */}
                        <div className="space-y-6">
                            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                                <div className="p-5 border-b border-white/10 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                            <Activity size={20} className="text-blue-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-medium text-white">Estado del Bot</h3>
                                            <p className="text-gray-500 text-xs">Monitoreo y comandos en vivo</p>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 border text-xs font-bold rounded-full flex items-center gap-2 uppercase tracking-widest ${systemStatus?.bot_status === 'Online'
                                        ? 'bg-green-500/10 border-green-500/30 text-green-400'
                                        : 'bg-red-500/10 border-red-500/30 text-red-400'
                                        }`}>
                                        <span className={`w-2 h-2 rounded-full ${systemStatus?.bot_status === 'Online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                                        {systemStatus?.bot_status || 'Cargando...'}
                                    </span>
                                </div>
                                <div className="p-6">
                                    <div className="grid grid-cols-2 pb-6 gap-4">
                                        <div className="bg-black/20 p-4 rounded-xl border border-white/5 text-center">
                                            <p className="text-gray-500 text-xs uppercase mb-1">Uptime</p>
                                            <p className="text-white font-bold text-lg">{systemStatus?.bot_uptime || '--'}</p>
                                        </div>
                                        <div className="bg-black/20 p-4 rounded-xl border border-white/5 text-center">
                                            <p className="text-gray-500 text-xs uppercase mb-1">Latencia (Ping)</p>
                                            <p className="text-green-400 font-bold text-lg">{systemStatus?.bot_latency || 0}ms</p>
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <button
                                            onClick={handleSyncCommands}
                                            disabled={saving === 'sync-cmds'}
                                            className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors group disabled:opacity-50"
                                        >
                                            <div className="flex items-center gap-3">
                                                <RefreshCw size={18} className={`text-blue-400 transition-transform duration-500 ${saving === 'sync-cmds' ? 'animate-spin' : 'group-hover:rotate-180'}`} />
                                                <span className="text-sm text-gray-200">{saving === 'sync-cmds' ? 'Solicitando...' : 'Forzar Sincronización de Comandos (Slash)'}</span>
                                            </div>
                                            <ChevronDown size={16} className="text-gray-500 -rotate-90" />
                                        </button>
                                        <button
                                            onClick={() => handlePM2Action('stop')}
                                            disabled={saving === 'pm2-stop'}
                                            className="w-full flex items-center justify-between p-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg transition-colors group text-red-400 disabled:opacity-50"
                                        >
                                            <div className="flex items-center gap-3">
                                                <Ban size={18} className="group-hover:scale-110 transition-transform duration-500" />
                                                <span className="text-sm font-medium">{saving === 'pm2-stop' ? 'Deteniendo...' : 'Apagar Bot (PM2 Stop)'}</span>
                                            </div>
                                            <ChevronDown size={16} className="text-red-500/50 -rotate-90" />
                                        </button>
                                        <button
                                            onClick={() => handlePM2Action('restart')}
                                            disabled={saving === 'pm2-restart'}
                                            className="w-full flex items-center justify-between p-3 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 rounded-lg transition-colors group text-orange-400 disabled:opacity-50"
                                        >
                                            <div className="flex items-center gap-3">
                                                <RotateCcw size={18} className={`transition-transform duration-500 ${saving === 'pm2-restart' ? 'animate-spin' : 'group-hover:-rotate-180'}`} />
                                                <span className="text-sm font-medium">{saving === 'pm2-restart' ? 'Reiniciando...' : 'Reiniciar Bot (PM2 Restart)'}</span>
                                            </div>
                                            <ChevronDown size={16} className="text-orange-500/50 -rotate-90" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Bloque: Anuncios Globales (Megáfono) */}
                        <div className="space-y-6">
                            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                                <div className="p-5 border-b border-white/10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                                            <FileText size={20} className="text-purple-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-medium text-white">Megáfono (Anuncios)</h3>
                                            <p className="text-gray-500 text-xs">Enviar mensajes oficiales al servidor de Discord</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-6 space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-sm text-gray-400 mb-1 block">Título</label>
                                            <input
                                                type="text"
                                                value={anuncioForm.titulo}
                                                onChange={e => setAnuncioForm({ ...anuncioForm, titulo: e.target.value })}
                                                className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                placeholder="Ej: Inicio de Temporada"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 mb-1 block">Color (Hex)</label>
                                            <div className="flex gap-2">
                                                <input
                                                    type="color"
                                                    value={anuncioForm.color}
                                                    onChange={e => setAnuncioForm({ ...anuncioForm, color: e.target.value })}
                                                    className="h-10 w-12 rounded cursor-pointer bg-transparent border-none"
                                                />
                                                <input
                                                    type="text"
                                                    value={anuncioForm.color}
                                                    onChange={e => setAnuncioForm({ ...anuncioForm, color: e.target.value })}
                                                    className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">Canal Destino (Nombre)</label>
                                        <input
                                            type="text"
                                            value={anuncioForm.canal_destino}
                                            onChange={e => setAnuncioForm({ ...anuncioForm, canal_destino: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                            placeholder="anuncios"
                                        />
                                        <p className="text-xs text-gray-500 mt-1">Busca cualquier canal que contenga esta palabra. Default: 'anuncios' o 'general'.</p>
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-1 block">URL de Imagen (Opcional)</label>
                                        <input
                                            type="text"
                                            value={anuncioForm.imagen_url}
                                            onChange={e => setAnuncioForm({ ...anuncioForm, imagen_url: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-2.5 text-white focus:border-purple-500/50 focus:outline-none"
                                            placeholder="https://imgur.com/..."
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm text-gray-400 mb-2 block">Cuerpo del Mensaje</label>
                                        <textarea
                                            rows="4"
                                            value={anuncioForm.mensaje}
                                            onChange={e => setAnuncioForm({ ...anuncioForm, mensaje: e.target.value })}
                                            className="w-full bg-[#161b22] border border-white/10 rounded-lg p-3 text-white focus:border-purple-500/50 focus:outline-none resize-none"
                                            placeholder="Escribe el anuncio para la liga... (Soporta Markdown de Discord)"
                                        ></textarea>
                                    </div>
                                    <button
                                        onClick={handleSendAnnouncement}
                                        disabled={saving === 'anuncio'}
                                        className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 disabled:opacity-50 text-white font-bold rounded-lg transition-all shadow-lg shadow-purple-500/20"
                                    >
                                        {saving === 'anuncio' ? 'Enviando Anuncio...' : '📢 Publicar Noticia Oficial'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 2. TAB CONFIG */}
                {activeSystemTab === 'config' && (
                    <div className="bg-[#0f1219] border border-white/5 rounded-2xl overflow-hidden shadow-xl max-w-3xl mx-auto">
                        <div className="p-5 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/20 flex items-center justify-center">
                                    <Settings size={20} className="text-gold-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-medium text-white">Configuración del Juego</h3>
                                    <p className="text-gray-500 text-xs">Variables en tiempo real del servidor y del bot</p>
                                </div>
                            </div>
                        </div>
                        <div className="p-6 space-y-6 flex-1 relative">
                            <p className="text-xs text-gray-500">
                                Puntos (victoria/empate/derrota) y goles W.O. se configuran por liga en{' '}
                                <span className="text-gold-400">Admin → Ligas</span> (crear o editar).
                            </p>
                            {loadingConfig ? (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                                    <div className="w-8 h-8 border-4 border-gold-500/30 border-t-gold-500 rounded-full animate-spin"></div>
                                </div>
                            ) : null}

                            <div className="flex items-center justify-between p-4 bg-black/20 rounded-xl border border-white/5">
                                <div>
                                    <h4 className="text-white text-sm font-medium">Estado del Mercado</h4>
                                    <p className="text-gray-500 text-xs mt-1">Permitir Fichajes e Intercambios</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={!!globalConfig?.mercado_abierto}
                                        onChange={(e) => setGlobalConfig({ ...globalConfig, mercado_abierto: e.target.checked })}
                                    />
                                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                                </label>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-2 flex justify-between">
                                        <span>Límite de Jugadores por Plantilla</span>
                                        <span className="text-gold-400 font-bold">{globalConfig?.limite_plantilla || 12}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="5" max="25"
                                        value={globalConfig?.limite_plantilla || 12}
                                        onChange={(e) => setGlobalConfig({ ...globalConfig, limite_plantilla: e.target.value })}
                                        className="w-full accent-gold-500"
                                    />
                                </div>

                                <div className="border-t border-white/5 pt-4 grid gap-3">
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 block">Rutas de Texto (IDs o Nombres exactos)</label>
                                        <div className="grid grid-cols-2 gap-2">
                                            <input type="text" value={globalConfig?.canal_ofertas_id || ''} onChange={e => setGlobalConfig({ ...globalConfig, canal_ofertas_id: e.target.value })} placeholder="ID Canal Ofertas" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                            <input type="text" value={globalConfig?.canal_fichajes || ''} onChange={e => setGlobalConfig({ ...globalConfig, canal_fichajes: e.target.value })} placeholder="Nmbr. Canal Fichajes" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                            <input type="text" value={globalConfig?.rol_dt || ''} onChange={e => setGlobalConfig({ ...globalConfig, rol_dt: e.target.value })} placeholder="Nmbr. Rol DT" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                            <input type="text" value={globalConfig?.rol_agente_libre || ''} onChange={e => setGlobalConfig({ ...globalConfig, rol_agente_libre: e.target.value })} placeholder="Nmbr. Rol Agente" className="w-full bg-[#161b22] border border-white/10 rounded p-2 text-xs text-white" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="p-4 border-t border-white/5 bg-black/20">
                            <button
                                onClick={handleSaveGlobalConfig}
                                disabled={saving === 'global-config'}
                                className="w-full py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-black hover:from-gold-400 hover:to-gold-500 font-bold rounded-lg transition-colors text-sm shadow-[0_0_15px_rgba(234,179,8,0.2)]"
                            >
                                {saving === 'global-config' ? 'Guardando...' : 'Guardar ajustes globales del servidor'}
                            </button>
                        </div>
                    </div>
                )}

                {/* 3. TAB ZONA PELIGRO */}
                {activeSystemTab === 'peligro' && (
                    <div className="bg-[#1f0909] border border-red-500/30 rounded-2xl overflow-hidden relative max-w-3xl mx-auto shadow-2xl">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/10 rounded-full blur-3xl"></div>
                        <div className="p-6 border-b border-red-500/20 bg-black/20">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center">
                                    <AlertTriangle size={20} className="text-red-500" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-red-500">Zona de Peligro</h3>
                                    <p className="text-red-400/70 text-xs">Mantenimiento de Base de Datos y Limpieza</p>
                                </div>
                            </div>
                        </div>
                        <div className="p-6 space-y-4 relative z-10">
                            <div className="p-4 bg-black/40 border border-red-500/10 rounded-xl">
                                <h4 className="text-white text-sm font-medium mb-1 flex items-center gap-2"><Save size={14} className="text-gray-400" /> Generar Backup</h4>
                                <p className="text-gray-500 text-xs mb-3">Crea un volcado total de la base de datos descargable como JSON. Útil antes del cierre de liga.</p>
                                <button
                                    onClick={handleBackup}
                                    disabled={saving === 'backup'}
                                    className="w-full py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white border border-gray-600 rounded-lg transition-colors text-sm font-medium">
                                    {saving === 'backup' ? 'Generando...' : 'Descargar Backup Completo'}
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-4 bg-black/40 border border-orange-500/10 rounded-xl">
                                    <h4 className="text-orange-400 text-sm font-medium mb-1">Resetear Temporada</h4>
                                    <p className="text-gray-500 text-xs mb-3">Borra partidos, tabla y estadísticas. Mantiene equipos.</p>
                                    <button
                                        onClick={handleResetSeason}
                                        disabled={saving === 'reset'}
                                        className="w-full py-2 bg-orange-600/20 hover:bg-orange-600 hover:text-white disabled:opacity-50 border border-orange-500/50 text-orange-500 rounded-lg transition-all text-xs font-bold">
                                        {saving === 'reset' ? 'Reseteando...' : 'RESET LIGA'}
                                    </button>
                                </div>
                                <div className="p-4 bg-black/40 border border-yellow-500/10 rounded-xl">
                                    <h4 className="text-yellow-400 text-sm font-medium mb-1">Reset Completo (Stats 0)</h4>
                                    <p className="text-gray-500 text-xs mb-3">Todo a CERO: presupuestos, precios, stats. Mantiene estructuras.</p>
                                    <button
                                        onClick={handleFullReset}
                                        disabled={saving === 'full-reset'}
                                        className="w-full py-2 bg-yellow-600/20 hover:bg-yellow-600 hover:text-white disabled:opacity-50 border border-yellow-500/50 text-yellow-500 rounded-lg transition-all text-xs font-bold">
                                        {saving === 'full-reset' ? 'Reseteando...' : 'FULL RESET'}
                                    </button>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-3">
                                <div className="p-4 bg-black/40 border border-blue-500/10 rounded-xl">
                                    <h4 className="text-blue-400 text-sm font-medium mb-1">Purgar Registros</h4>
                                    <p className="text-gray-500 text-xs mb-3">Elimina historiales y auditoría (+60 días) para aligerar la BD.</p>
                                    <button
                                        onClick={handlePurgeLogs}
                                        disabled={saving === 'purge'}
                                        className="w-full py-2 bg-blue-600/20 hover:bg-blue-600 hover:text-white disabled:opacity-50 border border-blue-500/50 text-blue-500 rounded-lg transition-all text-xs font-bold">
                                        {saving === 'purge' ? 'Limpiando...' : 'PURGAR BD'}
                                    </button>
                                </div>
                            </div>
                            <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-xl">
                                <h4 className="text-red-400 text-sm font-medium mb-1 flex items-center gap-2"><Trash2 size={14} /> NUKE: Borrado Total de Base de Datos</h4>
                                <p className="text-red-200/50 text-xs mb-3">Borra absolutamente todos los equipos, jugadores, partidos, fichajes y tabla de la BD. ¡Irreversible!</p>
                                <button
                                    onClick={handleNuke}
                                    disabled={saving === 'nuke'}
                                    className="w-full py-2 bg-red-600/20 hover:bg-red-600 disabled:opacity-50 hover:text-white border border-red-500/50 text-red-500 rounded-lg transition-all text-sm font-bold tracking-wider">
                                    {saving === 'nuke' ? 'DETONANDO CARGAS...' : 'INICIAR NUEVA ASOCIACIÓN DE 0'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
};

export default SistemaTab;
