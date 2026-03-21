import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Menu, X, ChevronDown, User, LogOut, DollarSign, Hexagon, Users, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
    const [scrolled, setScrolled] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);
    const location = useLocation();
    const { user, login, logout } = useAuth();

    // Detect scroll for navbar bg
    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const navLinks = [
        { name: 'Mi Equipo', path: '/' },
        { name: 'Mercado', path: '/mercado' },
        { name: 'Equipos', path: '/equipos' },
        { name: 'Clasificación', path: '/clasificacion' },
        { name: 'Jornadas', path: '/jornadas' },
    ];

    return (
        <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'bg-dark-900/90 backdrop-blur-md border-b border-white/5 shadow-lg' : 'bg-transparent'}`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-20">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 group">
                        <div className="w-10 h-10 bg-gold-500 rounded-full flex items-center justify-center font-bold text-dark-900 border-2 border-transparent group-hover:border-white transition-all">
                            AP
                        </div>
                        <span className="font-display font-bold text-xl tracking-wider text-white group-hover:text-gold-400 transition-colors">
                            AMAPICKS FC
                        </span>
                    </Link>

                    {/* Desktop Menu */}
                    <div className="hidden md:flex items-center space-x-8">
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={link.path}
                                className={`text-sm font-semibold uppercase tracking-widest transition-colors hover:text-gold-400 ${location.pathname === link.path ? 'text-gold-500 border-b-2 border-gold-500 pb-1' : 'text-gray-300'}`}
                            >
                                {link.name}
                            </Link>
                        ))}
                    </div>

                    {/* User Profile / Login */}
                    <div className="hidden md:flex items-center gap-4">
                        {user ? (
                            <div className="flex items-center gap-4">
                                {/* Team Info (if DT) */}
                                {user.team_id && (
                                    <div className="flex items-center gap-2 bg-dark-900 border border-white/10 rounded-full pl-1 pr-4 py-1">
                                        <div className="w-6 h-6 rounded-full bg-gold-500 flex items-center justify-center">
                                            <Shield size={14} className="text-black" />
                                        </div>
                                        <span className="text-xs font-bold text-gray-300 uppercase hidden lg:block">
                                            {user.team_name || 'Mi Equipo'}
                                        </span>
                                    </div>
                                )}

                                {/* User Dropdown */}
                                <div className="group relative">
                                    <button className="flex items-center gap-2 pl-1 pr-3 py-1 bg-white/5 rounded-full hover:bg-white/10 transition-colors border border-white/5">
                                        <img
                                            src={user.avatar}
                                            alt={user.name}
                                            className="w-8 h-8 rounded-full border border-black"
                                        />
                                        <span className="text-sm font-bold text-white max-w-[100px] truncate">{user.name}</span>
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
                        ) : (
                            <button
                                onClick={login}
                                className="flex items-center gap-2 px-6 py-2.5 bg-[#5865F2] hover:bg-[#4752C4] text-white font-bold rounded-xl transition-all shadow-lg shadow-[#5865F2]/20 hover:scale-105 active:scale-95"
                            >
                                <Users size={18} />
                                <span>Login con Discord</span>
                            </button>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center">
                        <button onClick={() => setMenuOpen(!menuOpen)} className="text-gray-300 hover:text-white">
                            {menuOpen ? <X size={28} /> : <Menu size={28} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu Dropdown */}
            {menuOpen && (
                <div className="md:hidden bg-dark-900 border-b border-white/10 absolute w-full">
                    <div className="px-4 pt-2 pb-6 space-y-2">
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={link.path}
                                onClick={() => setMenuOpen(false)}
                                className={`block px-3 py-4 text-base font-bold uppercase tracking-wider border-b border-white/5 ${location.pathname === link.path ? 'text-gold-500' : 'text-gray-300'}`}
                            >
                                {link.name}
                            </Link>
                        ))}
                        {/* Mobile Login Button */}
                        {!user && (
                            <button
                                onClick={login}
                                className="block w-full text-left px-3 py-4 text-base font-bold uppercase tracking-wider text-[#5865F2]"
                            >
                                Login con Discord
                            </button>
                        )}
                    </div>
                </div>
            )}
        </nav>
    );
};

const Layout = () => {
    return (
        <div className="min-h-screen flex flex-col font-sans bg-dark-950 text-white selection:bg-gold-500/30">
            <Navbar />
            <main className="flex-1 pt-20 relative">
                {/* global minimal bg effect */}
                <div className="fixed inset-0 pointer-events-none z-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03]" />
                <Outlet />
            </main>

            <footer className="border-t border-white/5 bg-dark-900 py-8 mt-20 relative z-10">
                <div className="max-w-7xl mx-auto px-4 text-center">
                    <p className="text-gray-600 text-sm font-medium tracking-widest uppercase">
                        © 2026 Amapicks League. Official Partner of Haxball.
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Layout;
