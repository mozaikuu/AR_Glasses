# Bus System Workspace

This folder isolates the Smart Bus Tracking MVP so bus-related backend, frontend, simulation, and AI tool code stay in one place.

## Structure

- `backend/` FastAPI backend, persistence, and runtime wiring
- `frontend/` Next.js dashboard and PWA
- `simulation/` route simulation and prediction modules
- `agent_tools/` Cerebro-compatible backend wrappers
- `bus_system/docs/bus_tracking_mvp/` MVP setup, API, and architecture docs

## Quick Start

1. Backend

```bash
cd bus_system/backend
python -m pip install -r requirements.txt
python run.py
```

2. Frontend

```bash
cd bus_system/frontend
npm install
cp .env.example .env.local
npm run dev
```

3. Open

- Frontend: http://localhost:3000
- Backend docs: http://127.0.0.1:8000/docs

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
