# API Spec — Minimal

GET /health

- Response: {"status":"ok","demo":"ready"}

GET /demo/route?from={lat,lon}

- Response: JSON with keys: `eta_minutes`, `route_points` (array of [lat,lon])

GET /pathfinder?start={start}&end={end}

- Response: JSON array of waypoints
