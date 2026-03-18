import React, { createContext, useState, useEffect, useContext } from 'react';
import { ligaService } from '../services/api';

const TempAuthContext = createContext();

export const TempAuthProvider = ({ children }) => {
    const [userTeamId, setUserTeamId] = useState(null); // ID del equipo que "somos"
    const [equipos, setEquipos] = useState([]);

    // Cargar equipos al inicio para el selector
    useEffect(() => {
        ligaService.getEquipos().then(setEquipos).catch(console.error);
    }, []);

    // Buscar el objeto del equipo seleccionado
    const activeTeam = equipos.find(e => (e.role_id?.toString() === userTeamId) || (e.nombre === userTeamId));

    return (
        <TempAuthContext.Provider value={{ userTeamId, setUserTeamId, activeTeam, equipos }}>
            {children}
        </TempAuthContext.Provider>
    );
};

export const useTempAuth = () => useContext(TempAuthContext);
