# Cerebro Agent Tools

This package exposes Python functions that call the FastAPI backend and are designed for AI assistant orchestration.

## Tools

- `get_bus_location(lang='en')`
- `predict_bus_arrival(student_location=None, lang='en')`
- `pay_bus_fee(student_id, amount, payment_type='trip', force_fail=False, lang='en')`
- `check_wallet(student_id, lang='en')`
- `report_delay(description, reporter_name='Cerebro Agent', eta_impact_minutes=8, lang='en')`

All backend responses include bilingual messages (`en`, `ar`).

## Base URL

Set environment variable `CEREBRO_BACKEND_URL` if backend is not running on `http://127.0.0.1:8000`.
