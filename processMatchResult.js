const mongoose = require('mongoose');

// ============================================================================
// Modelos (Asegúrate de importar los correctos según tu arquitectura)
// ============================================================================
const Match = require('./models/Match'); // Reemplazar con la ruta real
const Team = require('./models/Team');   // Reemplazar con la ruta real
const Player = require('./models/Player'); // Reemplazar con la ruta real

/**
 * ⚽ Procesa el resultado de un partido de Haxball
 * Actualiza la tabla de posiciones (Teams) y recalcula el valor de mercado (Players).
 * Todo encapsulado en una sesión/transacción de MongoDB para garantizar Atomicidad.
 *
 * @param {Object} input - Datos del partido finalizado
 * @param {String} input.matchId - ID del partido en la colección Matches
 * @param {Number} input.homeScore - Goles del equipo local
 * @param {Number} input.awayScore - Goles del equipo visitante
 * @param {Array} input.playerStats - Estadísticas [{ playerId, goals, assists, saves, passes, playedMinutes }]
 */
async function processMatchResult({ matchId, homeScore, awayScore, playerStats }) {
    // Iniciamos la sesión para asegurar operaciones atómicas (DB debe ser Replica Set o Atlas)
    const session = await mongoose.startSession();
    session.startTransaction();

    try {
        // 1. Validar el Partido y Equipos
        const match = await Match.findById(matchId).session(session);
        if (!match) throw new Error("❌ Partido no encontrado en la base de datos.");
        if (match.status === 'played') throw new Error("⚠️ El partido ya fue procesado anteriormente.");

        const homeTeamId = match.homeTeamId || match.homeTeam; // Ajusta según el campo de tu DB
        const awayTeamId = match.awayTeamId || match.awayTeam;

        // 2. Lógica de Puntuación (Colección Teams)
        let homePts = 0, awayPts = 0;
        let homePG = 0, homePE = 0, homePP = 0;
        let awayPG = 0, awayPE = 0, awayPP = 0;

        if (homeScore > awayScore) {
            homePts = 3; homePG = 1; awayPP = 1; // Local gana
        } else if (awayScore > homeScore) {
            awayPts = 3; awayPG = 1; homePP = 1; // Visitante gana
        } else {
            homePts = 1; awayPts = 1;            // Empate
            homePE = 1; awayPE = 1;
        }

        // Preparar BulkWrite para los Equipos
        const teamUpdates = [
            {
                updateOne: {
                    filter: { _id: homeTeamId },
                    update: {
                        $inc: {
                            puntos: homePts, 
                            pj: 1, pg: homePG, pe: homePE, pp: homePP,
                            gf: homeScore, gc: awayScore, dg: (homeScore - awayScore)
                        }
                    }
                }
            },
            {
                updateOne: {
                    filter: { _id: awayTeamId },
                    update: {
                        $inc: {
                            puntos: awayPts, 
                            pj: 1, pg: awayPG, pe: awayPE, pp: awayPP,
                            gf: awayScore, gc: homeScore, dg: (awayScore - homeScore)
                        }
                    }
                }
            }
        ];

        // 3. Algoritmo de Valor de Mercado (Players)
        // Obtener la tabla actual antes de los cambios para saber quién está mejor posicionado
        // Ajusta los criterios de orden según tu liga.
        const standings = await Team.find({ liga: match.liga || 'D1' })
            .sort({ puntos: -1, dg: -1, gf: -1 })
            .select('_id')
            .lean()
            .session(session);

        // Mapa de Rank (1 es el mejor)
        const teamRanks = {};
        standings.forEach((t, i) => teamRanks[t._id.toString()] = i + 1);

        const homeRank = teamRanks[homeTeamId.toString()] || 99;
        const awayRank = teamRanks[awayTeamId.toString()] || 99;

        const playerUpdates = [];

        // Valor de conversión arbitrario (ajusta a la economía de tu liga)
        const VALOR_POR_PUNTO = 150000;  // Cada punto de rendimiento vale 150k
        const VICTORIA_BASE = 200000;    // Fijo por ganar
        const REDUCCION_DERROTA = -250000; // Fijo inicial de pérdida
        const VALOR_INACTIVIDAD = -500000; // Reducción fuerte para D1 inactivos

        for (const stat of playerStats) {
            const player = await Player.findById(stat.playerId).session(session);
            if (!player) continue;

            const isHome = player.teamId ? (player.teamId.toString() === homeTeamId.toString()) : false;
            
            // Si no detectamos el equipo correctamente por alguna razón, asumimos variables neutras
            const playerTeamRank = isHome ? homeRank : awayRank;
            const oppRank = isHome ? awayRank : homeRank;
            
            const teamWon = isHome ? (homeScore > awayScore) : (awayScore > homeScore);
            const teamLost = isHome ? (homeScore < awayScore) : (awayScore < homeScore);

            let valueChange = 0;

            // INACTIVIDAD D1
            if (stat.playedMinutes === 0 && (player.liga === 'D1' || player.categoria === 'D1')) {
                valueChange = VALOR_INACTIVIDAD;
            } else {
                // Cálculo Base de Rendimiento (Puntos)
                const performancePoints = 
                      (stat.goals * 1.0) 
                    + (stat.assists * 0.8) 
                    + (stat.saves * 0.5) 
                    + (stat.passes * 0.5) 
                    + (stat.playedMinutes > 0 ? 0.2 : 0);
                
                let performanceEconomics = performancePoints * VALOR_POR_PUNTO;

                if (teamWon) {
                    valueChange = VICTORIA_BASE + performanceEconomics;
                    
                    // BONO RIVAL: si ganó contra un rival mejor posicionado (su rank > rank rival)
                    if (playerTeamRank > oppRank) {
                        valueChange *= 1.10; // +10% de subida extra
                    }
                } else if (teamLost) {
                    // Cae de base, pero se amortigua con buen rendimiento individual
                    valueChange = REDUCCION_DERROTA + (performanceEconomics * 0.5); 
                    
                    // CASTIGO AGRESIVO: si perdió contra un rival peor posicionado (su rank < rank rival)
                    if (playerTeamRank < oppRank) {
                        // Hacemos que la caída (si es negativa) duela un 50% más
                        if (valueChange < 0) valueChange *= 1.50; 
                    }
                } else {
                    // Empate: ganancia moderada o pérdida leve según performance
                    valueChange = performanceEconomics * 0.75; 
                }

                // BONO CAPITÁN
                if (player.is_captain) {
                    if (valueChange > 0) {
                        valueChange *= 1.15; // +15% solo si sube su valor
                    }
                }
            }

            // Aplicamos cambio matemático del jugador, con un piso mínimo
            let finalMarketValue = Math.floor(player.valorMercado + valueChange);
            const VALOR_MINIMO_D1 = 100000;
            if (finalMarketValue < VALOR_MINIMO_D1) {
                finalMarketValue = VALOR_MINIMO_D1;
            }

            playerUpdates.push({
                updateOne: {
                    filter: { _id: stat.playerId },
                    update: { $set: { valorMercado: finalMarketValue } }
                }
            });
        }

        // 4. Ejecución Atómica de Cambios (MongoDB BulkWrite)
        await Team.bulkWrite(teamUpdates, { session });
        if (playerUpdates.length > 0) {
            await Player.bulkWrite(playerUpdates, { session });
        }

        // Actualizamos estado de partido
        match.status = 'played';
        match.homeScore = homeScore;
        match.awayScore = awayScore;
        await match.save({ session });

        // Finalizar y asegurar transacción
        await session.commitTransaction();
        session.endSession();

        return { 
            success: true, 
            message: "✅ Partido procesado con éxito. Tabla y Economía de jugadores actualizados.",
            updates: playerUpdates.length
        };

    } catch (error) {
        // En caso de cualquier error, abortamos TODO, evitamos datos huérfanos
        await session.abortTransaction();
        session.endSession();
        console.error("🔥 Error en processMatchResult:", error);
        throw error;
    }
}

module.exports = {
    processMatchResult
};
