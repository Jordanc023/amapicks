# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


# Proyecto: AMAPICKS (Liga de Haxball)
Bot de Discord en Python y plataforma web con React/Vite.

## ⚠️ REGLAS ESTRICTAS DE COMPORTAMIENTO (LEER SIEMPRE)

1. **IDIOMA:** Comunícate SIEMPRE y ÚNICAMENTE en español. Tus explicaciones, nombres de variables sugeridas y comentarios de código deben estar en español.
2. **AHORRO DE TOKENS (Súper importante):** - Sé directo. Cero saludos, cero despedidas, cero explicaciones de relleno ("¡Claro que sí! Aquí tienes...").
   - Ve directo a la solución o al bloque de código.
3. **EDICIÓN DE CÓDIGO:** Cuando te pida modificar un archivo, NO me imprimas el archivo completo de vuelta si es muy largo. Muéstrame solo la función o el bloque específico que cambió.
4. **NO ASUMAS:** Si necesitas leer un archivo para entender un problema, usa tus herramientas para leerlo primero antes de inventar una solución a ciegas.

## Project Overview

AMAPICKS is a Haxball fantasy football league manager. It combines three processes:
1. **Discord Bot** (discord.py) — handles all in-server commands via slash commands
2. **Web API** (FastAPI + Uvicorn on port 8001) — REST API for the web panel
3. **Web Frontend** (React + Vite, port 5173 dev / static in prod) — admin panel and user dashboard

All three share a single **MongoDB** database accessed via Motor (async driver).

## Commands

### Local Development

```bash
# Discord bot
python main.py

# FastAPI backend
cd web/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# React frontend (dev server)
cd web/frontend
npm run dev
```

### Frontend Build & Lint

```bash
cd web/frontend
npm run build   # outputs to dist/
npm run lint    # ESLint
```

### Install Dependencies

```bash
pip install -r requirements.txt                  # Bot
pip install -r web/backend/requirements.txt      # API
cd web/frontend && npm install                    # Frontend
```

### Production (VPS via PM2)

```bash
bash deploy.sh          # Pull, install deps, build frontend, restart PM2
pm2 restart ecosystem.config.js
pm2 logs                # View live logs from all 3 processes
```

## Architecture

### Bot (root directory)

- `main.py` — `LigaBot` class; loads all Cogs, connects to MongoDB, starts heartbeat task (sends metrics every 60s, reads remote commands), auto-syncs player/Discord roles every hour.
- `config.py` — single source of truth for role names, channel IDs, point values, and other league constants.
- `database.py` — MongoDB connection helpers shared by all bot Cogs.
- One file per feature (Cog): `fichajes.py`, `directores.py`, `equipos.py`, `jugadores.py`, `partidos.py`, `mercado.py`, `clasificacion.py`, `estadisticas.py`, `administracion.py`, `ayuda.py`.
- `utils.py`, `utils_imagen.py` — shared helpers and image generation (Pillow).

### Web Backend (`web/backend/`)

- `main.py` — FastAPI app creation, CORS setup, router registration.
- `routers/` — one file per domain: `auth.py` (Discord OAuth2 + JWT), `liga.py`, `admin.py`, `estadisticas.py`, `partidos.py`, `ligas_manager.py` (largest router, ~57 KB).
- `repositories/admin_repository.py` — data access layer for admin operations.
- Authentication flow: Discord OAuth2 → JWT token stored in browser → sent as `Authorization: Bearer` header.

### Web Frontend (`web/frontend/src/`)

- `main.jsx` — React Router v6 setup, route definitions.
- `context/AuthContext.jsx` — global auth state (Discord OAuth2 user).
- `services/api.js` — Axios instance with base URL + auth interceptors; all API calls go through here.
- `pages/` — full-page route components (`MiEquipo`, `Mercado`, `Equipos`, `Clasificacion`, `Jornadas`, `Admin`, `LoginCallback`).
- `components/admin/` — tab components used by `Admin.jsx` (`AuditoriaTab`, `EquiposTab`, `JugadoresTab`, `LigasManagerTab`, `SistemaTab`).

### Key MongoDB Collections

| Collection | Contents |
|---|---|
| `jugadores` | Player records with market value, clause |
| `equipos` | Team records |
| `ofertas_pendientes` | Active transfer offers (75%–200% of market value) |
| `partidos` | Match results |
| `configuracion` | Per-guild bot config |
| `clubes_pendientes_creacion` | Clubs created via web, awaiting bot pickup |
| `anuncios_pendientes` | Announcements queued from web panel to be posted in Discord |

### Cross-System Integration

The bot and web backend communicate **through MongoDB** (not direct HTTP calls):
- Web panel queues actions in `clubes_pendientes_creacion` / `anuncios_pendientes`.
- The bot's heartbeat task polls those collections every 60 seconds and executes them in Discord (creates roles, posts messages, etc.).

## Environment Variables (`.env`)

```
DISCORD_TOKEN
MONGO_URI
DISCORD_CLIENT_ID
DISCORD_CLIENT_SECRET
SECRET_KEY              # JWT signing
DISCORD_REDIRECT_URI
CORS_ORIGINS            # Comma-separated frontend URLs
FRONTEND_URL
```

## No Test Suite

There are no automated tests. Changes should be validated manually by running the relevant process locally.
