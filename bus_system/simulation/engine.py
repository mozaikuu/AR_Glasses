from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from simulation.route_data import ROUTE_NAME, ROUTE_POINTS, VIRTUAL_STOPS


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


@dataclass
class SimulatedIncident:
    incident_type: str
    description: str
    eta_impact_minutes: int
    created_at: datetime
    expires_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_type": self.incident_type,
            "description": self.description,
            "eta_impact_minutes": self.eta_impact_minutes,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "source": "simulation",
        }


class BusSimulationEngine:
    def __init__(self, tick_seconds: int = 3, total_seats: int = 50, seed: int = 2026) -> None:
        self.tick_seconds = tick_seconds
        self.total_seats = total_seats
        self._rng = random.Random(seed)

        self.route_points = ROUTE_POINTS
        self.route_name = ROUTE_NAME
        self._segment_distances_km = self._build_segment_distances()

        self._cumulative_distance_km: list[float] = [0.0]
        for segment in self._segment_distances_km:
            self._cumulative_distance_km.append(self._cumulative_distance_km[-1] + segment)

        self.total_distance_km = self._cumulative_distance_km[-1]

        self._stop_distances = {
            stop["name"]: self._cumulative_distance_km[stop["index"]] for stop in VIRTUAL_STOPS
        }

        self.current_distance_km = 0.0
        self.speed_kmh = 36.0
        self.traffic_level = 4.6
        self.current_passengers = 11
        self.predicted_passengers = 26
        self.status = "Bus is preparing departure"
        self.last_stop = VIRTUAL_STOPS[0]["name"]
        self.next_stop = VIRTUAL_STOPS[1]["name"]
        self.updated_at = datetime.utcnow()

        self._active_incidents: list[SimulatedIncident] = []
        self._visited_stops_this_trip: set[str] = set()
        self._stop_hold_until: datetime | None = None

        self._tick_callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def _build_segment_distances(self) -> list[float]:
        distances: list[float] = []
        for i in range(len(self.route_points) - 1):
            lat1, lng1 = self.route_points[i]
            lat2, lng2 = self.route_points[i + 1]
            distances.append(_haversine_km(lat1, lng1, lat2, lng2))
        return distances

    def register_tick_callback(
        self, callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        self._tick_callback = callback

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        while self._running:
            self.tick()
            if self._tick_callback:
                await self._tick_callback(self.snapshot())
            await asyncio.sleep(self.tick_seconds)

    def tick(self) -> None:
        now = datetime.utcnow()
        self._update_traffic_level()
        self._clear_expired_incidents(now)

        if self._stop_hold_until and now < self._stop_hold_until:
            self.speed_kmh = 0.0
            self.status = f"Stopped at {self.last_stop}"
            self.updated_at = now
            return

        self._stop_hold_until = None
        self._maybe_spawn_incident(now)

        incident_penalty = self.total_incident_impact_minutes
        base_speed = self._rng.uniform(33.0, 57.0)
        speed_penalty = min(28.0, (incident_penalty * 0.65) + (self.traffic_level * 0.9))
        self.speed_kmh = max(10.0, base_speed - speed_penalty)

        distance_step = (self.speed_kmh * self.tick_seconds) / 3600.0
        self.current_distance_km += distance_step

        if self.current_distance_km >= self.total_distance_km:
            self.current_distance_km = 0.0
            self._visited_stops_this_trip.clear()
            self.current_passengers = self._rng.randint(6, 13)
            self.status = "New trip started from Mansoura"

        if not self._maybe_stop(now):
            self._simulate_passenger_drift()
            self.status = "Running toward New Mansoura University"

        self.updated_at = now

    def _update_traffic_level(self) -> None:
        drift = self._rng.uniform(-0.5, 0.7)
        self.traffic_level = max(1.0, min(10.0, self.traffic_level + drift))

    def _maybe_stop(self, now: datetime) -> bool:
        for stop in VIRTUAL_STOPS:
            stop_name = stop["name"]
            if stop_name in self._visited_stops_this_trip:
                continue

            stop_distance = self._stop_distances[stop_name]
            if abs(self.current_distance_km - stop_distance) <= 0.14:
                self._visited_stops_this_trip.add(stop_name)
                self._stop_hold_until = now + timedelta(seconds=self._rng.randint(8, 20))
                self.last_stop = stop_name
                self.next_stop = self._next_unvisited_stop_name()
                self._simulate_boarding_event()
                self.status = f"Stopped at {stop_name}"
                self.speed_kmh = 0.0
                return True
        self.next_stop = self._next_unvisited_stop_name()
        return False

    def _next_unvisited_stop_name(self) -> str:
        for stop in VIRTUAL_STOPS:
            if stop["name"] not in self._visited_stops_this_trip:
                return stop["name"]
        return VIRTUAL_STOPS[-1]["name"]

    def _simulate_boarding_event(self) -> None:
        boarding = self._rng.randint(1, 7)
        leaving = self._rng.randint(0, 3)
        self.current_passengers = max(
            0,
            min(self.total_seats, self.current_passengers + boarding - leaving),
        )

    def _simulate_passenger_drift(self) -> None:
        if self._rng.random() < 0.1:
            variation = self._rng.choice([-1, 1])
            self.current_passengers = max(
                0,
                min(self.total_seats, self.current_passengers + variation),
            )

    def _maybe_spawn_incident(self, now: datetime) -> None:
        chance = 0.025 if not self._active_incidents else 0.01
        if self._rng.random() > chance:
            return

        incident_catalog = [
            ("traffic_jam", "Unexpected congestion near toll gate", 7),
            ("delay", "Minor delay due to checkpoint traffic", 5),
            ("bus_full", "Bus is almost full after major stop", 3),
            ("breakdown", "Short technical pause for system check", 11),
            ("early_arrival", "Road is clear, bus is ahead of schedule", -4),
        ]

        incident_type, description, eta_impact = self._rng.choice(incident_catalog)
        duration_seconds = self._rng.randint(75, 220)
        self._active_incidents.append(
            SimulatedIncident(
                incident_type=incident_type,
                description=description,
                eta_impact_minutes=eta_impact,
                created_at=now,
                expires_at=now + timedelta(seconds=duration_seconds),
            )
        )

    def _clear_expired_incidents(self, now: datetime) -> None:
        self._active_incidents = [
            incident for incident in self._active_incidents if incident.expires_at > now
        ]

    @property
    def total_incident_impact_minutes(self) -> int:
        return int(sum(incident.eta_impact_minutes for incident in self._active_incidents))

    @property
    def route_progress_percent(self) -> float:
        if not self.total_distance_km:
            return 0.0
        return round((self.current_distance_km / self.total_distance_km) * 100.0, 2)

    @property
    def occupancy_rate(self) -> float:
        if not self.total_seats:
            return 0.0
        return round(self.current_passengers / self.total_seats, 3)

    def get_location(self) -> dict[str, float]:
        lat, lng = self._point_at_distance(self.current_distance_km)
        return {"lat": round(lat, 6), "lng": round(lng, 6)}

    def _point_at_distance(self, distance_km: float) -> tuple[float, float]:
        if distance_km <= 0:
            return self.route_points[0]

        if distance_km >= self.total_distance_km:
            return self.route_points[-1]

        for index in range(len(self._segment_distances_km)):
            start_distance = self._cumulative_distance_km[index]
            end_distance = self._cumulative_distance_km[index + 1]
            if start_distance <= distance_km <= end_distance:
                segment_length = self._segment_distances_km[index]
                if segment_length == 0:
                    return self.route_points[index]

                progress = (distance_km - start_distance) / segment_length
                lat1, lng1 = self.route_points[index]
                lat2, lng2 = self.route_points[index + 1]
                lat = lat1 + (lat2 - lat1) * progress
                lng = lng1 + (lng2 - lng1) * progress
                return lat, lng

        return self.route_points[-1]

    def remaining_distance_km(self) -> float:
        return max(0.0, self.total_distance_km - self.current_distance_km)

    def estimated_eta_minutes(self) -> float:
        effective_speed = max(14.0, self.speed_kmh)
        base_eta = (self.remaining_distance_km() / effective_speed) * 60.0
        return max(8.0, base_eta + self.total_incident_impact_minutes)

    def active_incidents(self) -> list[dict[str, Any]]:
        return [incident.to_dict() for incident in self._active_incidents]

    def snapshot(self) -> dict[str, Any]:
        return {
            "route_name": self.route_name,
            "location": self.get_location(),
            "speed_kmh": round(self.speed_kmh, 2),
            "traffic_level": round(self.traffic_level, 2),
            "current_passengers": self.current_passengers,
            "total_seats": self.total_seats,
            "occupancy_rate": self.occupancy_rate,
            "predicted_passengers": self.predicted_passengers,
            "status": self.status,
            "last_stop": self.last_stop,
            "next_stop": self.next_stop,
            "route_progress_percent": self.route_progress_percent,
            "estimated_eta_minutes": round(self.estimated_eta_minutes(), 2),
            "active_simulated_incidents": self.active_incidents(),
            "timestamp": self.updated_at.isoformat(),
            "route_points": [
                {"lat": lat, "lng": lng} for lat, lng in self.route_points
            ],
            "stops": VIRTUAL_STOPS,
        }
