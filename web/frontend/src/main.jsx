import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Mercado from './pages/Mercado';
import Equipos from './pages/Equipos';
import Clasificacion from './pages/Clasificacion';
import MiEquipo from './pages/MiEquipo';
import Admin from './pages/Admin';
import Estadisticas from './pages/Estadisticas';
import LoginCallback from './pages/LoginCallback';
import CrearEquipo from './pages/CrearEquipo';
import './index.css';

import { AuthProvider } from './context/AuthContext';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Layout />}>
                        <Route index element={<Home />} />
                        <Route path="equipo" element={<MiEquipo />} />
                        <Route path="crear-equipo" element={<CrearEquipo />} />
                        <Route path="mercado" element={<Mercado />} />
                        <Route path="equipos" element={<Equipos />} />
                        <Route path="clasificacion" element={<Clasificacion />} />
                        <Route path="estadisticas" element={<Estadisticas />} />
                        <Route path="admin" element={<Admin />} />
                    </Route>
                    <Route path="/auth/callback" element={<LoginCallback />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    </React.StrictMode>,
);
