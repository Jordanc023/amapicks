import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { ChevronDown, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import FloatingSidebar from './FloatingSidebar';

const LayoutNuevo = () => {
    const { user, login, logout } = useAuth();

    return (
        <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-dark-950">
            {/* Barra lateral flotante */}
            <FloatingSidebar />

            {/* Header superior solo con logo y perfil de usuario */}
            <header className="fixed top-0 left-0 right-0 z-30 bg-dark-900/50 backdrop-blur-sm border-b border-white/5">
                <div className="flex items-center justify-between px-6 py-4">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 group ml-20">
                        <div className="w-10 h-10 bg-gold-500 rounded-full flex items-center justify-center font-bold text-dark-900 border-2 border-transparent group-hover:border-white transition-all">
                            AP
                        </div>
                        <span className="font-display font-bold text-xl tracking-wider text-white group-hover:text-gold-400 transition-colors">
                            AMAPICKS FC
                        </span>
                    </Link>

                    {/* Login / Perfil */}
                    {!user ? (
                        <button
                            type="button"
                            onClick={() => login()}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#5865F2] hover:bg-[#4752C4] text-white text-sm font-bold border border-white/10 shadow-lg transition-colors"
                        >
                            <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                                <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z" />
                            </svg>
                            Entrar con Discord
                        </button>
                    ) : (
                        <div className="flex items-center gap-4">
                            {/* Team Info (if DT) */}
                            {user.team_id && (
                                <div className="hidden lg:flex items-center gap-2 bg-dark-800 border border-white/10 rounded-full pl-1 pr-4 py-1">
                                    <div className="w-6 h-6 rounded-full bg-gold-500 flex items-center justify-center">
                                        <Shield size={14} className="text-black" />
                                    </div>
                                    <span className="text-xs font-bold text-gray-300 uppercase">
                                        {user.team_name || 'Mi Equipo'}
                                    </span>
                                </div>
                            )}

                            {/* User Dropdown */}
                            <div className="group relative">
                                <button className="flex items-center gap-2 pl-1 pr-3 py-1 bg-white/5 rounded-full hover:bg-white/10 transition-colors border border-white/10">
                                    <img
                                        src={user.avatar}
                                        alt={user.name}
                                        className="w-8 h-8 rounded-full border border-black"
                                    />
                                    <span className="text-sm font-bold text-white max-w-[100px] truncate hidden sm:block">{user.name}</span>
                                    <ChevronDown size={14} className="text-gray-500" />
                                </button>

                                {/* Dropdown Menu */}
                                <div className="absolute right-0 top-full mt-2 w-48 bg-dark-900 border border-white/10 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right z-50">
                                    <div className="p-2 space-y-1">
                                        {user.admin && (
                                            <Link to="/admin" className="block px-4 py-2 text-sm text-gold-500 hover:bg-white/5 rounded-lg font-bold">
                                                Panel Admin
                                            </Link>
                                        )}
                                        <button
                                            onClick={logout}
                                            className="w-full text-left flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-white/5 rounded-lg"
                                        >
                                            <LogOut size={14} /> Cerrar Sesión
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </header>

            {/* Contenido principal con margen para la sidebar */}
            <main className="pt-20 ml-0 lg:ml-20">
                <div className="px-4 sm:px-6 lg:px-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default LayoutNuevo;