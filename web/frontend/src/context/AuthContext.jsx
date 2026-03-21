import React, { createContext, useState, useEffect, useContext } from 'react';
import { ligaService } from '../services/api';
import { jwtDecode } from "jwt-decode"; // Necesitaremos installing jwt-decode

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // { name, avatar, team_id, admin, ... }
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            try {
                const decoded = jwtDecode(token);
                // Verificar expiración
                if (decoded.exp * 1000 < Date.now()) {
                    logout();
                } else {
                    setUser(decoded);
                    // Configurar header global para axios si fuera necesario, 
                    // pero ligaService usa instancia 'api'. Podriamos añadir interceptor.
                }
            } catch (error) {
                console.error("Token inválido", error);
                logout();
            }
        }
        setLoading(false);
    }, [token]);

    const login = () => {
        const isLocalhost = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
        const defaultApiUrl = isLocalhost ? 'http://localhost:8000' : 'http://20.81.152.127:8001';
        const apiUrl = import.meta.env.VITE_AUTH_API_URL || import.meta.env.VITE_API_HOST || defaultApiUrl;

        console.log('Auth login:', { apiUrl, location: window.location.href });

        try {
            window.location.href = `${apiUrl}/api/auth/login`;
        } catch (error) {
            console.error('Error redirigiendo a login:', error);
            alert('No se pudo iniciar sesión. Revisa la consola para más detalles.');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        window.location.href = "/";
    };

    const handleCallback = (newToken) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, handleCallback, loading, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
