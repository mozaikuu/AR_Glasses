# Frontend (Next.js PWA)

Modern mobile-friendly dashboard for NMU bus tracking prototype.

## Pages

- `/` Live Bus Map
- `/wallet` Student Wallet
- `/capacity` Capacity Dashboard
- `/admin` Admin Panel

## Tech

- Next.js + App Router
- TailwindCSS
- Leaflet + OpenStreetMap
- WebSocket live updates
- PWA install + simulated notifications

## Local Run

```bash
cd bus_system/frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend runs on `http://localhost:3000` and expects backend on `http://127.0.0.1:8000`.

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
