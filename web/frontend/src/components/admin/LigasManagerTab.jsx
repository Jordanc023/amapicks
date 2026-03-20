import React, { useState, useEffect } from 'react';
import {
    Trophy, Plus, Edit2, Trash2, Users, Calendar, Settings,
    ChevronRight, AlertTriangle, CheckCircle, X, ArrowRight,
    Shield, Target, TrendingUp
} from 'lucide-react';
import { ligaService } from '../../services/api';

/**
 * Componente para gestionar múltiples ligas (D1, D2, etc.)
 * Permite crear, editar, asignar equipos y configurar temporadas.
 */
const LigasManagerTab = () => {
    const [ligas, setLigas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedLiga, setSelectedLiga] = useState(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isEquiposModalOpen, setIsEquiposModalOpen] = useState(false);
    const [isFixtureModalOpen, setIsFixtureModalOpen] = useState(false);
    const [equiposDisponibles, setEquiposDisponibles] = useState([]);
    const [equiposLiga, setEquiposLiga] = useState([]);
    const [ligaActiva, setLigaActiva] = useState(null);
    const [saving, setSaving] = useState(false);

    // Form states
    const [createForm, setCreateForm] = useState({
        nombre: '',
        descripcion: '',
        division: 'D1',
        max_equipos: 12,
        formato: 'todos_contra_todos',
        puntos_victoria: 3,
        puntos_empate: 1,
        puntos_derrota: 0,
        playoffs_habilitados: true,
        clasificados_playoffs: 4,
        jornada_paron_copa: 11,
        color_identificacion: '#FFD700'
    });

    const [fixtureForm, setFixtureForm] = useState({
        fecha_inicio: '',
        dias_entre_jornadas: 3,
        hora_default: '20:00'
    });

    // Cargar datos iniciales
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [ligasRes, ligaActivaRes, equiposRes] = await Promise.all([
                ligaService.getLigas(),
                ligaService.getLigaActiva(),
                ligaService.getEquipos()
            ]);

            setLigas(ligasRes);
            setLigaActiva(ligaActivaRes.liga_activa);
            // Filtrar equipos que no están en ninguna liga
            const equiposLibres = equiposRes.filter(eq => !eq.liga_id);
            setEquiposDisponibles(equiposLibres);
        } catch (error) {
            console.error('Error cargando ligas:', error);
            alert('❌ Error al cargar datos de ligas');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateLiga = async () => {
        if (!createForm.nombre || !createForm.division) {
            alert('⚠️ Nombre y división son obligatorios');
            return;
        }

        setSaving(true);
        try {
            const res = await ligaService.crearLiga(createForm);
            alert(`✅ Liga '${res.nombre}' creada exitosamente`);
            setIsCreateModalOpen(false);
            setCreateForm({
                nombre: '',
                descripcion: '',
                division: 'D1',
                max_equipos: 12,
                formato: 'todos_contra_todos',
                puntos_victoria: 3,
                puntos_empate: 1,
                puntos_derrota: 0,
                playoffs_habilitados: true,
                clasificados_playoffs: 4,
                jornada_paron_copa: 11,
                color_identificacion: '#FFD700'
            });
            await loadData();
        } catch (error) {
            console.error(error);
            alert(`❌ ${error.response?.data?.detail || 'Error al crear liga'}`);
        } finally {
            setSaving(false);
        }
    };

    const handleUpdateLiga = async () => {
        if (!selectedLiga) return;

        setSaving(true);
        try {
            const res = await ligaService.actualizarLiga(selectedLiga.id, createForm);
            alert(`✅ Liga '${res.nombre}' actualizada`);
            setIsEditModalOpen(false);
            setSelectedLiga(null);
            await loadData();
        } catch (error) {
            console.error(error);
            alert(`❌ ${error.response?.data?.detail || 'Error al actualizar'}`);
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteLiga = async () => {
        if (!selectedLiga) return;

        setSaving(true);
        try {
            await ligaService.eliminarLiga(selectedLiga.id);
            alert(`🗑️ Liga '${selectedLiga.nombre}' eliminada`);
            setIsDeleteModalOpen(false);
            setSelectedLiga(null);
            await loadData();
        } catch (error) {
            console.error(error);
            alert(`❌ ${error.response?.data?.detail || 'Error al eliminar'}`);
        } finally {
            setSaving(false);
        }
    };

    const handleSetLigaActiva = async (ligaId) => {
        if (!window.confirm('¿Establecer esta como la liga activa del sistema?')) return;

        setSaving(true);
        try {
            const res = await ligaService.establecerLigaActiva(ligaId);
            alert(`✅ ${res.message}`);
            await loadData();
        } catch (error) {
            console.error(error);
            alert('❌ Error al cambiar liga activa');
        } finally {
            setSaving(false);
        }
    };

    const handleAgregarEquipo = async (equipoId) => {
        if (!selectedLiga) return;

        setSaving(true);
        try {
            const res = await ligaService.agregarEquipoALiga(selectedLiga.id, equipoId);
            alert(`✅ ${res.message}`);
            // Recargar equipos de la liga
            const equiposRes = await ligaService.getEquiposLiga(selectedLiga.id);
            setEquiposLiga(equiposRes);
            // Recargar equipos disponibles
            const allEquipos = await ligaService.getEquipos();
            setEquiposDisponibles(allEquipos.filter(eq => !eq.liga_id));
        } catch (error) {
            console.error(error);
            alert(`❌ ${error.response?.data?.detail || 'Error'}`);
        } finally {
            setSaving(false);
        }
    };

    const handleRemoverEquipo = async (equipoId) => {
        if (!selectedLiga) return;
        if (!window.confirm('¿Remover este equipo de la liga?')) return;

        setSaving(true);
        try {
            await ligaService.removerEquipoDeLiga(selectedLiga.id, equipoId);
            alert('✅ Equipo removido');
            // Recargar equipos
            const equiposRes = await ligaService.getEquiposLiga(selectedLiga.id);
            setEquiposLiga(equiposRes);
            const allEquipos = await ligaService.getEquipos();
            setEquiposDisponibles(allEquipos.filter(eq => !eq.liga_id));
        } catch (error) {
            console.error(error);
            alert('❌ Error al remover equipo');
        } finally {
            setSaving(false);
        }
    };

    const handleGenerarFixture = async () => {
        if (!selectedLiga || !fixtureForm.fecha_inicio) {
            alert('⚠️ Selecciona una fecha de inicio');
            return;
        }

        if (equiposLiga.length < 2) {
            alert('⚠️ Se necesitan al menos 2 equipos en la liga');
            return;
        }

        setSaving(true);
        try {
            const res = await ligaService.generarFixtureLiga(
                selectedLiga.id,
                fixtureForm.fecha_inicio,
                fixtureForm.dias_entre_jornadas,
                fixtureForm.hora_default
            );
            alert(`✅ ${res.message}\n📊 ${res.jornadas_total} jornadas, ${res.partidos_creados} partidos`);
            setIsFixtureModalOpen(false);
            setFixtureForm({ fecha_inicio: '', dias_entre_jornadas: 3, hora_default: '20:00' });
            await loadData();
        } catch (error) {
            console.error(error);
            alert(`❌ ${error.response?.data?.detail || 'Error al generar fixture'}`);
        } finally {
            setSaving(false);
        }
    };

    const openEquiposModal = async (liga) => {
        setSelectedLiga(liga);
        setIsEquiposModalOpen(true);
        setLoading(true);
        try {
            const equiposRes = await ligaService.getEquiposLiga(liga.id);
            setEquiposLiga(equiposRes);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const openEditModal = (liga) => {
        setSelectedLiga(liga);
        setCreateForm({
            nombre: liga.nombre,
            descripcion: liga.descripcion || '',
            division: liga.division,
            max_equipos: liga.max_equipos,
            formato: liga.formato,
            puntos_victoria: liga.puntos_victoria,
            puntos_empate: liga.puntos_empate,
            puntos_derrota: liga.puntos_derrota,
            playoffs_habilitados: liga.playoffs_habilitados,
            clasificados_playoffs: liga.clasificados_playoffs,
            jornada_paron_copa: liga.jornada_paron_copa,
            color_identificacion: liga.color_identificacion
        });
        setIsEditModalOpen(true);
    };

    const openFixtureModal = (liga) => {
        setSelectedLiga(liga);
        setEquiposLiga([]);
        // Cargar equipos de la liga
        ligaService.getEquiposLiga(liga.id).then(setEquiposLiga);
        setIsFixtureModalOpen(true);
    };

    const divisionColors = {
        'D1': 'from-yellow-500 to-yellow-600',
        'D2': 'from-blue-500 to-blue-600',
        'D3': 'from-green-500 to-green-600',
        'COPA': 'from-purple-500 to-purple-600'
    };

    if (loading && ligas.length === 0) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center pb-6 border-b border-white/10">
                <div>
                    <h2 className="text-3xl font-light text-white">Gestión de Ligas</h2>
                    <p className="text-gray-500 mt-1">Crear y administrar múltiples divisiones (D1, D2, etc.)</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="px-4 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 transition-all font-medium flex items-center gap-2"
                >
                    <Plus size={18} />
                    <span>Nueva Liga</span>
                </button>
            </div>

            {/* Liga Activa Indicator */}
            {ligaActiva && (
                <div className="bg-gradient-to-r from-gold-500/10 to-gold-500/5 border border-gold-500/20 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gold-500/20 flex items-center justify-center">
                            <Trophy size={20} className="text-gold-400" />
                        </div>
                        <div>
                            <p className="text-xs text-gold-400 font-medium uppercase tracking-wider">Liga Activa del Sistema</p>
                            <p className="text-white font-medium">{ligaActiva.nombre} ({ligaActiva.division})</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Lista de Ligas */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ligas.map((liga) => (
                    <div
                        key={liga.id}
                        className={`bg-dark-800 border rounded-xl overflow-hidden transition-all hover:border-gold-500/30 ${
                            ligaActiva?.id === liga.id ? 'border-gold-500/50' : 'border-white/10'
                        }`}
                    >
                        {/* Card Header */}
                        <div className={`h-2 bg-gradient-to-r ${divisionColors[liga.division] || 'from-gray-500 to-gray-600'}`} />

                        <div className="p-5">
                            <div className="flex items-start justify-between mb-3">
                                <div>
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded bg-gradient-to-r ${divisionColors[liga.division] || 'from-gray-500 to-gray-600'} text-white`}>
                                        {liga.division}
                                    </span>
                                    <h3 className="text-lg font-medium text-white mt-2">{liga.nombre}</h3>
                                </div>
                                {ligaActiva?.id === liga.id && (
                                    <div className="w-6 h-6 rounded-full bg-gold-500/20 flex items-center justify-center">
                                        <CheckCircle size={14} className="text-gold-400" />
                                    </div>
                                )}
                            </div>

                            <p className="text-gray-500 text-sm mb-4 line-clamp-2">{liga.descripcion || 'Sin descripción'}</p>

                            {/* Stats */}
                            <div className="grid grid-cols-3 gap-2 mb-4">
                                <div className="bg-black/20 rounded-lg p-2 text-center">
                                    <p className="text-lg font-bold text-white">{liga.total_equipos || 0}</p>
                                    <p className="text-xs text-gray-500">Equipos</p>
                                </div>
                                <div className="bg-black/20 rounded-lg p-2 text-center">
                                    <p className="text-lg font-bold text-white">{liga.max_equipos}</p>
                                    <p className="text-xs text-gray-500">Máx</p>
                                </div>
                                <div className="bg-black/20 rounded-lg p-2 text-center">
                                    <p className="text-lg font-bold text-white">{(liga.jornadas_ida || 0) + (liga.jornadas_vuelta || 0)}</p>
                                    <p className="text-xs text-gray-500">Jornadas</p>
                                </div>
                            </div>

                            {/* Status Badge */}
                            <div className="mb-4">
                                <span className={`text-xs px-2 py-1 rounded-full ${
                                    liga.estado === 'en_curso' ? 'bg-green-500/20 text-green-400' :
                                    liga.estado === 'configuracion' ? 'bg-blue-500/20 text-blue-400' :
                                    liga.estado === 'paron_copa' ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-gray-500/20 text-gray-400'
                                }`}>
                                    {liga.estado === 'en_curso' ? 'En Curso' :
                                     liga.estado === 'configuracion' ? 'Configuración' :
                                     liga.estado === 'paron_copa' ? 'Parón Copa' :
                                     liga.estado === 'finalizada' ? 'Finalizada' : liga.estado}
                                </span>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-2">
                                <button
                                    onClick={() => openEquiposModal(liga)}
                                    className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-sm transition-all flex items-center justify-center gap-1"
                                >
                                    <Users size={14} />
                                    Equipos
                                </button>
                                <button
                                    onClick={() => openFixtureModal(liga)}
                                    className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-sm transition-all flex items-center justify-center gap-1"
                                    disabled={liga.estado !== 'configuracion'}
                                >
                                    <Calendar size={14} />
                                    Fixture
                                </button>
                                <button
                                    onClick={() => openEditModal(liga)}
                                    className="px-3 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg transition-all"
                                >
                                    <Edit2 size={14} />
                                </button>
                                <button
                                    onClick={() => { setSelectedLiga(liga); setIsDeleteModalOpen(true); }}
                                    className="px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>

                            {/* Set Active Button */}
                            {ligaActiva?.id !== liga.id && (
                                <button
                                    onClick={() => handleSetLigaActiva(liga.id)}
                                    disabled={saving}
                                    className="w-full mt-2 px-3 py-2 bg-gold-500/10 hover:bg-gold-500/20 text-gold-400 rounded-lg text-sm transition-all flex items-center justify-center gap-2"
                                >
                                    <Target size={14} />
                                    {saving ? 'Activando...' : 'Establecer como Activa'}
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {ligas.length === 0 && (
                <div className="text-center py-12">
                    <Trophy size={48} className="text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-500">No hay ligas creadas</p>
                    <p className="text-gray-600 text-sm mt-2">Crea tu primera liga para comenzar</p>
                </div>
            )}

            {/* ==================== MODAL: Crear Liga ==================== */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-950 border border-white/10 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center">
                            <h3 className="text-xl font-medium text-white">Crear Nueva Liga</h3>
                            <button onClick={() => setIsCreateModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Nombre de la Liga *</label>
                                    <input
                                        type="text"
                                        value={createForm.nombre}
                                        onChange={(e) => setCreateForm({ ...createForm, nombre: e.target.value })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                        placeholder="Ej: Liga de Campeones"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">División *</label>
                                    <select
                                        value={createForm.division}
                                        onChange={(e) => setCreateForm({ ...createForm, division: e.target.value })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    >
                                        <option value="D1">D1 - Primera División</option>
                                        <option value="D2">D2 - Segunda División</option>
                                        <option value="D3">D3 - Tercera División</option>
                                        <option value="COPA">COPA - Torneo Copa</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="text-sm text-gray-400 block mb-1">Descripción</label>
                                <textarea
                                    value={createForm.descripcion}
                                    onChange={(e) => setCreateForm({ ...createForm, descripcion: e.target.value })}
                                    className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none h-20"
                                    placeholder="Descripción de la liga..."
                                />
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Máx. Equipos</label>
                                    <input
                                        type="number"
                                        min="4"
                                        max="24"
                                        value={createForm.max_equipos}
                                        onChange={(e) => setCreateForm({ ...createForm, max_equipos: parseInt(e.target.value) || 12 })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Formato</label>
                                    <select
                                        value={createForm.formato}
                                        onChange={(e) => setCreateForm({ ...createForm, formato: e.target.value })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    >
                                        <option value="todos_contra_todos">Todos vs Todos</option>
                                        <option value="eliminatoria">Eliminatoria</option>
                                        <option value="grupos">Fase de Grupos</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Color</label>
                                    <input
                                        type="color"
                                        value={createForm.color_identificacion}
                                        onChange={(e) => setCreateForm({ ...createForm, color_identificacion: e.target.value })}
                                        className="w-full h-10 bg-dark-800 border border-white/10 rounded-lg cursor-pointer"
                                    />
                                </div>
                            </div>

                            <div className="border-t border-white/10 pt-4">
                                <h4 className="text-sm font-medium text-white mb-3">Sistema de Puntos</h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="text-xs text-gray-500 block mb-1">Victoria</label>
                                        <input
                                            type="number"
                                            value={createForm.puntos_victoria}
                                            onChange={(e) => setCreateForm({ ...createForm, puntos_victoria: parseInt(e.target.value) || 3 })}
                                            className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-green-400 text-center font-bold focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-500 block mb-1">Empate</label>
                                        <input
                                            type="number"
                                            value={createForm.puntos_empate}
                                            onChange={(e) => setCreateForm({ ...createForm, puntos_empate: parseInt(e.target.value) || 1 })}
                                            className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-yellow-400 text-center font-bold focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-500 block mb-1">Derrota</label>
                                        <input
                                            type="number"
                                            value={createForm.puntos_derrota}
                                            onChange={(e) => setCreateForm({ ...createForm, puntos_derrota: parseInt(e.target.value) || 0 })}
                                            className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-red-400 text-center font-bold focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="border-t border-white/10 pt-4">
                                <h4 className="text-sm font-medium text-white mb-3">Configuración Avanzada</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex items-center gap-3 bg-black/20 p-3 rounded-lg">
                                        <input
                                            type="checkbox"
                                            id="playoffs"
                                            checked={createForm.playoffs_habilitados}
                                            onChange={(e) => setCreateForm({ ...createForm, playoffs_habilitados: e.target.checked })}
                                            className="w-4 h-4 rounded border-gold-500 text-gold-500 focus:ring-gold-500"
                                        />
                                        <label htmlFor="playoffs" className="text-sm text-gray-300">Habilitar Playoffs</label>
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-500 block mb-1">Clasificados a Playoffs</label>
                                        <input
                                            type="number"
                                            min="2"
                                            max="8"
                                            value={createForm.clasificados_playoffs}
                                            onChange={(e) => setCreateForm({ ...createForm, clasificados_playoffs: parseInt(e.target.value) || 4 })}
                                            className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                            disabled={!createForm.playoffs_habilitados}
                                        />
                                    </div>
                                </div>
                                <div className="mt-3">
                                    <label className="text-xs text-gray-500 block mb-1">Jornada de Parón para Copa</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="22"
                                        value={createForm.jornada_paron_copa}
                                        onChange={(e) => setCreateForm({ ...createForm, jornada_paron_copa: parseInt(e.target.value) || 11 })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    />
                                    <p className="text-xs text-gray-600 mt-1">Al terminar esta jornada se activará el mercado y la copa</p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-white/10 flex justify-end gap-3">
                            <button
                                onClick={() => setIsCreateModalOpen(false)}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleCreateLiga}
                                disabled={saving || !createForm.nombre}
                                className="px-6 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 disabled:opacity-50 transition-all font-medium"
                            >
                                {saving ? 'Creando...' : 'Crear Liga'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==================== MODAL: Editar Liga ==================== */}
            {isEditModalOpen && selectedLiga && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-950 border border-white/10 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center">
                            <h3 className="text-xl font-medium text-white">Editar Liga</h3>
                            <button onClick={() => setIsEditModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            {/* Mismo contenido que crear, pero con datos precargados */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Nombre</label>
                                    <input
                                        type="text"
                                        value={createForm.nombre}
                                        onChange={(e) => setCreateForm({ ...createForm, nombre: e.target.value })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">División</label>
                                    <select
                                        value={createForm.division}
                                        onChange={(e) => setCreateForm({ ...createForm, division: e.target.value })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    >
                                        <option value="D1">D1 - Primera División</option>
                                        <option value="D2">D2 - Segunda División</option>
                                        <option value="D3">D3 - Tercera División</option>
                                        <option value="COPA">COPA - Torneo Copa</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Máx. Equipos</label>
                                    <input
                                        type="number"
                                        min="4"
                                        max="24"
                                        value={createForm.max_equipos}
                                        onChange={(e) => setCreateForm({ ...createForm, max_equipos: parseInt(e.target.value) || 12 })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Victoria</label>
                                    <input
                                        type="number"
                                        value={createForm.puntos_victoria}
                                        onChange={(e) => setCreateForm({ ...createForm, puntos_victoria: parseInt(e.target.value) || 3 })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-green-400 text-center font-bold focus:border-gold-500/50 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-1">Jornada Parón</label>
                                    <input
                                        type="number"
                                        value={createForm.jornada_paron_copa}
                                        onChange={(e) => setCreateForm({ ...createForm, jornada_paron_copa: parseInt(e.target.value) || 11 })}
                                        className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-3 bg-black/20 p-3 rounded-lg">
                                <input
                                    type="checkbox"
                                    id="activa-edit"
                                    checked={createForm.activa !== false}
                                    onChange={(e) => setCreateForm({ ...createForm, activa: e.target.checked })}
                                    className="w-4 h-4 rounded border-gold-500 text-gold-500 focus:ring-gold-500"
                                />
                                <label htmlFor="activa-edit" className="text-sm text-gray-300">Liga Activa (visible para usuarios)</label>
                            </div>
                        </div>

                        <div className="p-6 border-t border-white/10 flex justify-end gap-3">
                            <button
                                onClick={() => setIsEditModalOpen(false)}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleUpdateLiga}
                                disabled={saving}
                                className="px-6 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 disabled:opacity-50 transition-all font-medium"
                            >
                                {saving ? 'Guardando...' : 'Guardar Cambios'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==================== MODAL: Eliminar Liga ==================== */}
            {isDeleteModalOpen && selectedLiga && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-950 border border-red-500/20 rounded-2xl max-w-md w-full p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                                <AlertTriangle size={24} className="text-red-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-medium text-white">Eliminar Liga</h3>
                                <p className="text-gray-500 text-sm">Esta acción no se puede deshacer</p>
                            </div>
                        </div>

                        <p className="text-gray-400 mb-4">
                            ¿Estás seguro de que deseas eliminar la liga <strong className="text-white">{selectedLiga.nombre}</strong>?
                        </p>
                        <p className="text-red-400 text-sm mb-6">
                            Se eliminarán todos los partidos, la tabla de posiciones y la configuración de esta liga. Los equipos quedarán libres.
                        </p>

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setIsDeleteModalOpen(false)}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleDeleteLiga}
                                disabled={saving}
                                className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 transition-all font-medium"
                            >
                                {saving ? 'Eliminando...' : 'Eliminar Liga'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==================== MODAL: Gestionar Equipos ==================== */}
            {isEquiposModalOpen && selectedLiga && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-950 border border-white/10 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center">
                            <div>
                                <h3 className="text-xl font-medium text-white">Equipos en {selectedLiga.nombre}</h3>
                                <p className="text-gray-500 text-sm">{equiposLiga.length} de {selectedLiga.max_equipos} equipos</p>
                            </div>
                            <button onClick={() => setIsEquiposModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6">
                            {/* Equipos en la Liga */}
                            <div className="mb-6">
                                <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                                    <Shield size={16} className="text-gold-400" />
                                    Equipos Asignados ({equiposLiga.length})
                                </h4>
                                {equiposLiga.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {equiposLiga.map((eq) => (
                                            <div key={eq.id} className="bg-dark-800 border border-white/10 rounded-lg p-3 flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    {eq.logo_url && (
                                                        <img src={eq.logo_url} alt="" className="w-8 h-8 rounded-full object-cover" />
                                                    )}
                                                    <div>
                                                        <p className="text-white font-medium text-sm">{eq.nombre}</p>
                                                        <p className="text-gray-500 text-xs">DT: {eq.dt_nombre || 'Sin asignar'}</p>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleRemoverEquipo(eq.id)}
                                                    disabled={saving}
                                                    className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-sm italic">No hay equipos asignados a esta liga</p>
                                )}
                            </div>

                            {/* Equipos Disponibles */}
                            {equiposLiga.length < selectedLiga.max_equipos && (
                                <div>
                                    <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                                        <Plus size={16} className="text-green-400" />
                                        Equipos Disponibles ({equiposDisponibles.length})
                                    </h4>
                                    {equiposDisponibles.length > 0 ? (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                                            {equiposDisponibles.map((eq) => (
                                                <div key={eq.id || eq._id} className="bg-dark-800/50 border border-white/5 rounded-lg p-3 flex items-center justify-between hover:border-green-500/30 transition-all">
                                                    <div className="flex items-center gap-3">
                                                        {eq.logo_url && (
                                                            <img src={eq.logo_url} alt="" className="w-8 h-8 rounded-full object-cover" />
                                                        )}
                                                        <div>
                                                            <p className="text-white font-medium text-sm">{eq.nombre}</p>
                                                            <p className="text-gray-500 text-xs">{eq.role_name || 'Sin rol'}</p>
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => handleAgregarEquipo(eq.id || eq._id || eq.nombre)}
                                                        disabled={saving}
                                                        className="px-3 py-1 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-all text-sm"
                                                    >
                                                        Agregar
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-500 text-sm italic">No hay equipos disponibles. Crea equipos primero.</p>
                                    )}
                                </div>
                            )}

                            {equiposLiga.length >= selectedLiga.max_equipos && (
                                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                                    <p className="text-yellow-400 text-sm flex items-center gap-2">
                                        <AlertTriangle size={16} />
                                        La liga ha alcanzado el máximo de {selectedLiga.max_equipos} equipos
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ==================== MODAL: Generar Fixture ==================== */}
            {isFixtureModalOpen && selectedLiga && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-950 border border-white/10 rounded-2xl max-w-md w-full p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-medium text-white">Generar Fixture</h3>
                            <button onClick={() => setIsFixtureModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        {equiposLiga.length < 2 ? (
                            <div className="text-center py-8">
                                <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
                                <p className="text-white font-medium">Se necesitan al menos 2 equipos</p>
                                <p className="text-gray-500 text-sm mt-2">Actualmente hay {equiposLiga.length} equipos en esta liga</p>
                                <button
                                    onClick={() => { setIsFixtureModalOpen(false); openEquiposModal(selectedLiga); }}
                                    className="mt-4 px-4 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 transition-all"
                                >
                                    Gestionar Equipos
                                </button>
                            </div>
                        ) : (
                            <>
                                <div className="bg-gold-500/10 border border-gold-500/20 rounded-lg p-4 mb-6">
                                    <p className="text-gold-400 text-sm font-medium mb-2">Resumen</p>
                                    <p className="text-white text-sm">{equiposLiga.length} equipos</p>
                                    <p className="text-gray-400 text-sm">{(equiposLiga.length - 1) * 2} jornadas totales (ida y vuelta)</p>
                                    <p className="text-gray-400 text-sm">{(equiposLiga.length - 1) * equiposLiga.length} partidos</p>
                                </div>

                                <div className="space-y-4 mb-6">
                                    <div>
                                        <label className="text-sm text-gray-400 block mb-1">Fecha de Inicio *</label>
                                        <input
                                            type="date"
                                            value={fixtureForm.fecha_inicio}
                                            onChange={(e) => setFixtureForm({ ...fixtureForm, fecha_inicio: e.target.value })}
                                            className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-1">Días entre Jornadas</label>
                                            <input
                                                type="number"
                                                min="1"
                                                max="14"
                                                value={fixtureForm.dias_entre_jornadas}
                                                onChange={(e) => setFixtureForm({ ...fixtureForm, dias_entre_jornadas: parseInt(e.target.value) || 3 })}
                                                className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-1">Hora Default</label>
                                            <input
                                                type="time"
                                                value={fixtureForm.hora_default}
                                                onChange={(e) => setFixtureForm({ ...fixtureForm, hora_default: e.target.value })}
                                                className="w-full bg-dark-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-gold-500/50 focus:outline-none"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3">
                                    <button
                                        onClick={() => setIsFixtureModalOpen(false)}
                                        className="px-4 py-2 text-gray-400 hover:text-white transition-all"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        onClick={handleGenerarFixture}
                                        disabled={saving || !fixtureForm.fecha_inicio}
                                        className="px-6 py-2 bg-gold-500 text-black rounded-lg hover:bg-gold-400 disabled:opacity-50 transition-all font-medium"
                                    >
                                        {saving ? 'Generando...' : 'Generar Fixture'}
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default LigasManagerTab;
