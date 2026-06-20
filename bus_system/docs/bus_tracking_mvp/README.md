# Smart University Bus Tracking MVP

Prototype demo system for New Mansoura University (NMU) bus tracking integrated with Cerebro Smart Glasses.

## Monorepo Structure

- `bus_system/backend/` FastAPI API + SQLite + simulation runtime startup
- `bus_system/frontend/` Next.js + Tailwind + Leaflet + PWA dashboard
- `bus_system/simulation/` Route movement and AI prediction generators
- `bus_system/agent_tools/` Python functions for Cerebro AI assistant usage
- `bus_system/docs/bus_tracking_mvp/` setup, API, architecture docs

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
cd bus_system/backend
python -m pip install -r requirements.txt
python run.py
```

2. Start frontend in a second terminal

```bash
cd bus_system/frontend
npm install
cp .env.example .env.local
npm run dev
```

3. Open app

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.

4. Optional: test Cerebro tools

```bash
python -c "from bus_system.agent_tools.cerebro_tools import get_bus_location; print(get_bus_location())"
```

## Free Deployment Targets

- Frontend: Vercel (`bus_system/frontend/vercel.json`)
- Backend: Render (`bus_system/backend/render.yaml`) or Railway (`bus_system/backend/railway.toml`)
