# Backend (FastAPI)

NMU Smart Bus Tracking API for simulation, wallet, incidents, and AI prediction.

## Features

- SQLite persistence (PostgreSQL-ready schema design)
- Live bus simulation engine starts automatically with API startup
- WebSocket stream for real-time bus updates
- Bilingual EN/AR response envelopes
- Wallet top-up and payment simulation
- Student subscription handling
- Capacity and ETA prediction using scikit-learn

## Local Run

```bash
cd bus_system/backend
python -m pip install -r requirements.txt
python run.py
```

Open:

- API base: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
  -- WebSocket: `ws://127.0.0.1:8000/ws/bus`

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.

## Main Endpoints

- `GET /bus/location`
- `GET /bus/eta?student_location=31.04,31.37`
- `GET /bus/status`
- `GET /bus/capacity`
- `GET /bus/capacity/prediction`
- `GET /bus/eta/predicted`
- `GET /bus/demand/predicted`
- `POST /wallet/add`
- `POST /wallet/pay`
- `GET /wallet/history?student_id=1`
- `POST /report/incident`
- `GET /reports/active`
- `GET /bus/driver-info`
