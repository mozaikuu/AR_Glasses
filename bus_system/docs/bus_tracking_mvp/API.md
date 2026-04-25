# API Documentation

Base URL (local): `http://127.0.0.1:8000`

All endpoints support bilingual responses through `?lang=en` or `?lang=ar`.

## Bus

- `GET /bus/location`
   - Live location, route points, stops, speed, occupancy, ETA

- `GET /bus/eta?student_location=31.0409,31.3785`
   - ETA to provided student location (or fallback to route ETA)

- `GET /bus/status`
   - Current bus operational status + schedule + active incidents

- `GET /bus/eta/predicted`
   - AI predicted ETA using synthetic historical data

- `GET /bus/demand/predicted`
   - AI predicted demand + probability bus becomes full

- `GET /bus/capacity`
   - Current passenger and seat usage

- `GET /bus/capacity/prediction`
   - Predicted occupancy and full probability

- `GET /bus/driver-info`
   - Driver contact information for AI agent

## Wallet

- `POST /wallet/add`

```json
{
	"student_id": 1,
	"amount": 50
}
```

- `POST /wallet/pay`

```json
{
	"student_id": 1,
	"amount": 12,
	"payment_type": "trip",
	"force_fail": false
}
```

- `GET /wallet/history?student_id=1`

- `GET /wallet/balance?student_id=1`

## Students

- `GET /students`
   - Seeded students and home locations

- `POST /students/{student_id}/subscribe`

```json
{
	"months": 1
}
```

## Incident Reporting

- `POST /report/incident`

```json
{
	"reporter_role": "driver",
	"reporter_name": "Admin Dashboard",
	"incident_type": "delay",
	"description": "Traffic near gate",
	"eta_impact_minutes": 8
}
```

- `GET /reports/active`

## Realtime

- `WS /ws/bus`
   - Server pushes `bus_update` payloads with location and telemetry
