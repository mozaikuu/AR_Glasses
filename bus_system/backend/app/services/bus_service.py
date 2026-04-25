from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import IncidentReport
from app.services.geo import haversine_km, parse_lat_lng
from app.services.report_service import get_active_incidents
from app.services.runtime_state import runtime_state


def bus_orchestrator_ready() -> bool:
    return runtime_state.simulation_engine is not None and runtime_state.predictor is not None


def compute_total_incident_impact(db: Session) -> int:
    db_reports = get_active_incidents(db)
    db_impact = sum(report.eta_impact_minutes for report in db_reports)

    sim_engine = runtime_state.simulation_engine
    sim_impact = sim_engine.total_incident_impact_minutes if sim_engine else 0
    return int(db_impact + sim_impact)


def aggregated_active_incidents(db: Session) -> list[dict]:
    db_reports = [
        {
            "id": report.id,
            "incident_type": report.incident_type,
            "description": report.description,
            "eta_impact_minutes": report.eta_impact_minutes,
            "created_at": report.created_at.isoformat(),
            "source": "reported",
        }
        for report in get_active_incidents(db)
    ]

    sim_reports: list[dict] = []
    if runtime_state.simulation_engine:
        sim_reports = runtime_state.simulation_engine.active_incidents()

    return db_reports + sim_reports


def estimate_eta_to_student(student_location: str | None) -> dict:
    sim_engine = runtime_state.simulation_engine
    if not sim_engine:
        return {
            "eta_minutes": None,
            "distance_km": None,
            "valid_location": False,
        }

    bus_location = sim_engine.get_location()
    parsed = parse_lat_lng(student_location or "")

    if not parsed:
        return {
            "eta_minutes": round(sim_engine.estimated_eta_minutes(), 2),
            "distance_km": round(sim_engine.remaining_distance_km(), 2),
            "valid_location": False,
        }

    lat, lng = parsed
    distance_to_student = haversine_km(bus_location["lat"], bus_location["lng"], lat, lng)
    local_pickup_eta = max(3.0, (distance_to_student / 28.0) * 60.0)

    return {
        "eta_minutes": round(local_pickup_eta, 2),
        "distance_km": round(distance_to_student, 2),
        "valid_location": True,
        "student_location": {"lat": lat, "lng": lng},
    }


def predicted_eta_payload(total_incident_impact: int) -> dict:
    predictor = runtime_state.predictor
    sim_engine = runtime_state.simulation_engine
    if not predictor or not sim_engine:
        return {}

    now = datetime.utcnow()
    predicted = predictor.predict_eta_minutes(
        day_of_week=now.weekday(),
        traffic_level=sim_engine.traffic_level,
        incident_impact_minutes=total_incident_impact,
    )

    return {
        "predicted_eta_minutes": round(predicted, 2),
        "traffic_level": round(sim_engine.traffic_level, 2),
        "incident_impact_minutes": total_incident_impact,
        "model": "LinearRegression (synthetic 3-month dataset)",
    }


def predicted_demand_payload() -> dict:
    predictor = runtime_state.predictor
    sim_engine = runtime_state.simulation_engine
    if not predictor or not sim_engine:
        return {}

    now = datetime.utcnow()
    exam_day_flag = 1 if now.day % 11 == 0 or now.day % 13 == 0 else 0
    demand, probability_full = predictor.predict_demand(
        day_of_week=now.weekday(),
        traffic_level=sim_engine.traffic_level,
        is_exam_day=exam_day_flag,
    )
    sim_engine.predicted_passengers = demand

    return {
        "predicted_passenger_count": demand,
        "probability_bus_full": probability_full,
        "is_exam_day_pattern": bool(exam_day_flag),
        "model": "LinearRegression (synthetic demand signals)",
    }
