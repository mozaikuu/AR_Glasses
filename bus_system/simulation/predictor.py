from __future__ import annotations

from statistics import mean

import numpy as np
from sklearn.linear_model import LinearRegression

from simulation.historical_data import generate_historical_data


class BusPredictor:
    def __init__(self, seats: int = 50) -> None:
        self.seats = seats
        self.history = generate_historical_data(days=90)
        self.eta_model = LinearRegression()
        self.demand_model = LinearRegression()
        self._fit_models()

    def _fit_models(self) -> None:
        eta_features = np.array(
            [
                [
                    row["day_of_week"],
                    row["traffic_level"],
                    row["delay_minutes"],
                ]
                for row in self.history
            ],
            dtype=float,
        )
        eta_targets = np.array([row["travel_duration_minutes"] for row in self.history], dtype=float)

        demand_features = np.array(
            [
                [
                    row["day_of_week"],
                    row["traffic_level"],
                    row["is_exam_day"],
                ]
                for row in self.history
            ],
            dtype=float,
        )
        demand_targets = np.array([row["passenger_count"] for row in self.history], dtype=float)

        self.eta_model.fit(eta_features, eta_targets)
        self.demand_model.fit(demand_features, demand_targets)

    def average_delay_for_day(self, day_of_week: int) -> float:
        day_rows = [row for row in self.history if row["day_of_week"] == day_of_week]
        if not day_rows:
            return 6.0
        return float(mean(row["delay_minutes"] for row in day_rows))

    def predict_eta_minutes(
        self,
        day_of_week: int,
        traffic_level: float,
        incident_impact_minutes: float = 0.0,
    ) -> float:
        baseline_delay = self.average_delay_for_day(day_of_week)
        raw = float(
            self.eta_model.predict(
                np.array([[day_of_week, traffic_level, baseline_delay]], dtype=float)
            )[0]
        )
        return max(20.0, raw + incident_impact_minutes)

    def predict_demand(
        self,
        day_of_week: int,
        traffic_level: float,
        is_exam_day: int = 0,
    ) -> tuple[int, float]:
        raw_demand = float(
            self.demand_model.predict(
                np.array([[day_of_week, traffic_level, is_exam_day]], dtype=float)
            )[0]
        )
        bounded_demand = int(max(8, min(self.seats + 18, round(raw_demand))))

        fullness_ratio = bounded_demand / float(self.seats)
        probability_full = max(0.04, min(0.98, fullness_ratio * 0.84))
        return bounded_demand, round(probability_full, 3)
