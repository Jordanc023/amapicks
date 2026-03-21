import React from 'react';
import LigasManagerTab from './LigasManagerTab';
import LigaTab from './LigaTab';

/**
 * Pestaña unificada: gestión de competiciones (ligas, liga activa, fixture)
 * + calendario, partidos y panel de control.
 */
const CompeticionTab = ({ onCompeticionChanged, ligaTabProps }) => {
    return (
        <div className="space-y-16 pb-16">
            <section>
                <LigasManagerTab onCompeticionChanged={onCompeticionChanged} />
            </section>

            <div className="relative pt-4">
                <div className="flex items-center gap-4 mb-8">
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />
                    <span className="text-[10px] uppercase tracking-[0.2em] text-gray-500 px-2 whitespace-nowrap">
                        Fixture, resultados y herramientas
                    </span>
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />
                </div>
                <LigaTab {...ligaTabProps} />
            </div>
        </div>
    );
};

export default CompeticionTab;
