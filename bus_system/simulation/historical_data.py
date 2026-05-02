from __future__ import annotations

from datetime import date, timedelta
from random import Random
from typing import Any


def generate_historical_data(days: int = 90, seed: int = 2026) -> list[dict[str, Any]]:
    """Generate synthetic but patterned daily telemetry for 3 months."""
    rng = Random(seed)
    today = date.today()
    records: list[dict[str, Any]] = []

    for days_ago in range(days, 0, -1):
        sample_date = today - timedelta(days=days_ago)
        day_of_week = sample_date.weekday()

        is_weekend = day_of_week in (4, 5)
        is_exam_day = (sample_date.day % 11 == 0) or (sample_date.day % 13 == 0)

        traffic_baseline = 4.0 + (1.8 if day_of_week in (0, 1) else 0.8)
        traffic_noise = rng.uniform(-1.4, 2.3)
        traffic_level = max(1.0, min(10.0, traffic_baseline + traffic_noise))

        delay_minutes = max(0.0, traffic_level * rng.uniform(0.7, 1.6) + rng.uniform(-2.0, 4.0))

        passenger_base = 29 + (7 if not is_weekend else -5) + (6 if is_exam_day else 0)
        passenger_count = int(max(12, min(58, passenger_base + rng.randint(-9, 10))))

        travel_duration = max(
            34.0,
            44.0 + delay_minutes + (traffic_level * 1.15) + rng.uniform(-5.5, 4.0),
        )

        records.append(
            {
                "date": sample_date.isoformat(),
                "day_of_week": day_of_week,
                "traffic_level": round(traffic_level, 2),
                "delay_minutes": round(delay_minutes, 2),
                "travel_duration_minutes": round(travel_duration, 2),
                "passenger_count": passenger_count,
                "is_exam_day": int(is_exam_day),
            }
        )

    return records
