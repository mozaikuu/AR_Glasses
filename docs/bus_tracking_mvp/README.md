# Smart University Bus Tracking MVP

Prototype demo system for New Mansoura University (NMU) bus tracking integrated with Cerebro Smart Glasses.

## Monorepo Structure

- `backend/` FastAPI API + SQLite + simulation runtime startup
- `frontend/` Next.js + Tailwind + Leaflet + PWA dashboard
- `simulation/` Route movement and AI prediction generators
- `agent_tools/` Python functions for Cerebro AI assistant usage
- `docs/bus_tracking_mvp/` setup, API, architecture docs

## Core MVP Features

- Live bus route simulation (Mansoura -> NMU)
- WebSocket + REST real-time tracking
- Student wallet + trip fees + monthly subscription
- Capacity and demand prediction
- Incident reporting that dynamically changes ETA
- Driver contact endpoint for AI assistant
- Bilingual response support (English / Arabic)
- Installable PWA with simulated arrival notifications

## Local Setup (Step-by-Step)

1. Start backend

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

2. Start frontend in a second terminal

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

3. Open app

- Frontend: `http://localhost:3000`
- Backend docs: `http://127.0.0.1:8000/docs`

4. Optional: test Cerebro tools

```bash
python -c "from agent_tools.cerebro_tools import get_bus_location; print(get_bus_location())"
```

## Free Deployment Targets

- Frontend: Vercel (`frontend/vercel.json`)
- Backend: Render (`backend/render.yaml`) or Railway (`backend/railway.toml`)
