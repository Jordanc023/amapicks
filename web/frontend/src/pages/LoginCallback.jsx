import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RefreshCw } from 'lucide-react';

const LoginCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { handleCallback } = useAuth();

    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            handleCallback(token);
            navigate('/'); // Ir al Home
        } else {
            console.error("No token received");
            navigate('/');
        }
    }, [searchParams, handleCallback, navigate]);

    return (
        <div className="min-h-screen bg-black flex items-center justify-center text-gold-500">
            <div className="flex flex-col items-center gap-4">
                <RefreshCw className="animate-spin w-12 h-12" />
                <h2 className="text-xl font-display uppercase tracking-widest text-white">Iniciando Sesión...</h2>
            </div>
        </div>
    );
};

export default LoginCallback;
