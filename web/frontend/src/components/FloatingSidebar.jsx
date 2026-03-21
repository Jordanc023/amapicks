import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
    Home, 
    Users, 
    ShoppingCart, 
    Trophy, 
    Calendar, 
    Settings,
    Menu,
    X
} from 'lucide-react';

const FloatingSidebar = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const location = useLocation();

    // Cerrar sidebar al cambiar de ruta
    useEffect(() => {
        setIsOpen(false);
    }, [location]);

    // Cerrar sidebar al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (isOpen && !event.target.closest('.floating-sidebar')) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    const navItems = [
        { icon: Home, label: 'Mi Equipo', path: '/' },
        { icon: ShoppingCart, label: 'Mercado', path: '/mercado' },
        { icon: Users, label: 'Equipos', path: '/equipos' },
        { icon: Trophy, label: 'Clasificación', path: '/clasificacion' },
        { icon: Calendar, label: 'Jornadas', path: '/jornadas' },
        { icon: Settings, label: 'Admin', path: '/admin' },
    ];

    const isActive = (path) => {
        if (path === '/') {
            return location.pathname === '/';
        }
        return location.pathname.startsWith(path);
    };

    return (
        <>
            {/* Botón de menú móvil con efecto pulso */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`fixed top-4 left-4 z-50 lg:hidden p-3 bg-dark-800 border border-white/10 rounded-xl text-white hover:bg-dark-700 transition-all shadow-lg ${!isOpen ? 'pulse-gold' : ''}`}
                aria-label="Abrir menú de navegación"
            >
                {isOpen ? <X size={20} /> : <Menu size={20} />}
            </button>

            {/* Sidebar flotante */}
            <div 
                className={`floating-sidebar fixed left-4 top-1/2 -translate-y-1/2 z-40 transition-all duration-300 ease-out ${
                    isOpen ? 'translate-x-0 opacity-100' : '-translate-x-full opacity-0 lg:translate-x-0 lg:opacity-100'
                }`}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <nav className="bg-dark-800/90 backdrop-blur-md border border-white/10 rounded-2xl p-3 shadow-2xl">
                    <div className="flex flex-col gap-2">
                        {navItems.map((item, index) => {
                            const Icon = item.icon;
                            const active = isActive(item.path);
                            
                            return (
                                <Link
                                    key={index}
                                    to={item.path}
                                    className={`
                                        relative group flex items-center gap-3 p-3 rounded-xl transition-all duration-200
                                        ${active 
                                            ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30' 
                                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                                        }
                                    `}
                                    title={item.label}
                                >
                                    {/* Icono */}
                                    <Icon size={20} className={`flex-shrink-0 ${active ? 'text-gold-400' : ''}`} />
                                    
                                    {/* Tooltip */}
                                    <div className={`
                                        absolute left-full ml-3 px-2 py-1 bg-dark-900 text-white text-xs rounded 
                                        whitespace-nowrap transition-all duration-200 pointer-events-none
                                        ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'}
                                    `}>
                                        {item.label}
                                    </div>
                                    
                                    {/* Indicador activo */}
                                    {active && (
                                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gold-500 rounded-r-full" />
                                    )}
                                </Link>
                            );
                        })}
                    </div>
                </nav>
            </div>

            {/* Overlay para móvil */}
            {isOpen && (
                <div 
                    className="fixed inset-0 bg-black/50 z-30 lg:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </>
    );
};

export default FloatingSidebar;