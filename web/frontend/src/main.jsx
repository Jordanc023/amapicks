import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LayoutNuevo from './components/LayoutNuevo';
import Mercado from './pages/Mercado';
import Equipos from './pages/Equipos';
import Clasificacion from './pages/Clasificacion';
import Jornadas from './pages/Jornadas';
import MiEquipo from './pages/MiEquipo';
import Admin from './pages/Admin';
import LoginCallback from './pages/LoginCallback';

import './index.css';

import { AuthProvider } from './context/AuthContext';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<LayoutNuevo />}>
                        <Route index element={<MiEquipo />} />

                        <Route path="mercado" element={<Mercado />} />
                        <Route path="equipos" element={<Equipos />} />
                        <Route path="clasificacion" element={<Clasificacion />} />
                        <Route path="jornadas" element={<Jornadas />} />
                        <Route path="admin" element={<Admin />} />
                    </Route>
                    <Route path="/auth/callback" element={<LoginCallback />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    </React.StrictMode>,
);
