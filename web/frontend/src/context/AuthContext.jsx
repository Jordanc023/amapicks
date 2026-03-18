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
        // Redirigir al endpoint de login del backend
        window.location.href = "http://104.243.47.46/api/auth/login";
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
