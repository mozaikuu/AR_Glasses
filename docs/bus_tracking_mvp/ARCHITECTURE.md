# Architecture Overview

## 1. High-Level Flow

1. FastAPI backend starts.
2. Database tables are created and fake students are seeded.
3. Simulation engine starts as a background async loop.
4. Engine updates bus location, speed, occupancy, and random incidents every few seconds.
5. REST and WebSocket endpoints expose live + predicted state to frontend and agent tools.
6. Next.js dashboard consumes APIs and streams updates.
7. Cerebro agent tools call backend endpoints as function interfaces.

## 2. Modules

### backend/

- `app/main.py`: API app, lifespan startup, websocket stream
- `app/db/`: SQLAlchemy models and SQLite session
- `app/api/routes/`: Bus, wallet, students, incidents endpoints
- `app/services/`: Wallet logic, incident impact logic, ETA helpers
- `app/core/`: Settings, i18n response envelope, websocket manager

### simulation/

- `route_data.py`: NMU Route #1 geometry and schedule
- `engine.py`: Continuous movement + events generator
- `historical_data.py`: 3-month synthetic training data
- `predictor.py`: ETA and demand regressors (scikit-learn)

### frontend/

- App Router pages:
   - `/` live map
   - `/wallet` wallet system
   - `/capacity` occupancy and AI forecasts
   - `/admin` report incidents
- `components/live-map.tsx`: Leaflet map + websocket/polling sync
- `components/pwa-notifier.tsx`: install + local notification simulation

### agent_tools/

- `cerebro_tools.py`: AI-friendly function wrappers over API
   - `get_bus_location()`
   - `predict_bus_arrival()`
   - `pay_bus_fee()`
   - `check_wallet()`
   - `report_delay()`

## 3. Scalability Direction

- Replace SQLite with PostgreSQL by only changing `DATABASE_URL`.
- Add university dimension (`university_id`) in route/student tables.
- Duplicate simulation engines per route for multi-campus support.
- Introduce Redis pub/sub if realtime load grows.

## 4. Free Deployment

- Frontend on Vercel
- Backend on Render or Railway
- OpenStreetMap tile layer (free)
- No paid APIs required
