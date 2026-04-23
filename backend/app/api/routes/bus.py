from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_runtime_ready
from app.core.i18n import response_payload
from app.services.bus_service import (
    aggregated_active_incidents,
    compute_total_incident_impact,
    estimate_eta_to_student,
    predicted_demand_payload,
    predicted_eta_payload,
)
from app.services.runtime_state import runtime_state
from simulation.route_data import DAILY_SCHEDULE, DRIVER_INFO, ROUTE_NAME


router = APIRouter(prefix="/bus", tags=["Bus"])


@router.get("/location")
def get_bus_location(
    lang: str = "en",
    _: None = Depends(require_runtime_ready),
):
    snapshot = runtime_state.simulation_engine.snapshot() if runtime_state.simulation_engine else {}
    return response_payload(
        {
            "route": ROUTE_NAME,
            **snapshot,
        },
        en="Live bus location fetched successfully.",
        ar="تم جلب موقع الحافلة المباشر بنجاح.",
        lang=lang,
    )


@router.get("/status")
def get_bus_status(
    lang: str = "en",
    db: Session = Depends(db_session),
    _: None = Depends(require_runtime_ready),
):
    sim_engine = runtime_state.simulation_engine
    snapshot = sim_engine.snapshot() if sim_engine else {}
    incidents = aggregated_active_incidents(db)

    payload = {
        "route": ROUTE_NAME,
        "schedule": DAILY_SCHEDULE,
        "bus_status": snapshot.get("status"),
        "speed_kmh": snapshot.get("speed_kmh"),
        "next_stop": snapshot.get("next_stop"),
        "last_stop": snapshot.get("last_stop"),
        "updated_at": snapshot.get("timestamp"),
        "active_incident_count": len(incidents),
        "active_incidents": incidents,
        "service_started_today": datetime.utcnow().strftime("%Y-%m-%d") + "T07:15:00",
    }
    return response_payload(
        payload,
        en="Bus operational status retrieved.",
        ar="تم جلب حالة تشغيل الحافلة.",
        lang=lang,
    )


@router.get("/eta")
def get_bus_eta(
    student_location: str | None = Query(
        default=None,
        description="Student location as 'lat,lng'. Example: 31.041,31.378",
    ),
    lang: str = "en",
    db: Session = Depends(db_session),
    _: None = Depends(require_runtime_ready),
):
    eta_info = estimate_eta_to_student(student_location)
    incident_impact = compute_total_incident_impact(db)

    if eta_info.get("eta_minutes") is not None:
        eta_info["eta_minutes"] = round(max(1.0, eta_info["eta_minutes"] + incident_impact), 2)

    payload = {
        **eta_info,
        "incident_impact_minutes": incident_impact,
        "route_name": ROUTE_NAME,
    }
    return response_payload(
        payload,
        en="ETA calculated successfully.",
        ar="تم حساب وقت الوصول المتوقع بنجاح.",
        lang=lang,
    )


@router.get("/eta/predicted")
def get_predicted_eta(
    lang: str = "en",
    db: Session = Depends(db_session),
    _: None = Depends(require_runtime_ready),
):
    incident_impact = compute_total_incident_impact(db)
    payload = predicted_eta_payload(incident_impact)
    return response_payload(
        payload,
        en="Predicted ETA generated using historical simulation data.",
        ar="تم توليد وقت الوصول المتوقع باستخدام بيانات محاكاة تاريخية.",
        lang=lang,
    )


@router.get("/demand/predicted")
def get_predicted_demand(
    lang: str = "en",
    _: None = Depends(require_runtime_ready),
):
    payload = predicted_demand_payload()
    return response_payload(
        payload,
        en="Predicted passenger demand generated.",
        ar="تم توليد التنبؤ بطلب الركاب.",
        lang=lang,
    )


@router.get("/capacity")
def get_capacity(
    lang: str = "en",
    _: None = Depends(require_runtime_ready),
):
    sim_engine = runtime_state.simulation_engine
    payload = {
        "total_seats": sim_engine.total_seats,
        "current_passengers": sim_engine.current_passengers,
        "available_seats": max(0, sim_engine.total_seats - sim_engine.current_passengers),
        "occupancy_rate": sim_engine.occupancy_rate,
    }
    return response_payload(
        payload,
        en="Current bus capacity details fetched.",
        ar="تم جلب تفاصيل سعة الحافلة الحالية.",
        lang=lang,
    )


@router.get("/capacity/prediction")
def get_capacity_prediction(
    lang: str = "en",
    _: None = Depends(require_runtime_ready),
):
    sim_engine = runtime_state.simulation_engine
    demand = predicted_demand_payload()
    predicted = demand.get("predicted_passenger_count", sim_engine.predicted_passengers)
    payload = {
        "total_seats": sim_engine.total_seats,
        "predicted_passengers": predicted,
        "predicted_available_seats": max(0, sim_engine.total_seats - predicted),
        "probability_bus_full": demand.get("probability_bus_full", 0),
    }
    return response_payload(
        payload,
        en="Predicted bus capacity generated.",
        ar="تم توليد توقعات سعة الحافلة.",
        lang=lang,
    )


@router.get("/driver-info")
def get_driver_info(lang: str = "en"):
    return response_payload(
        DRIVER_INFO,
        en="Driver contact details retrieved.",
        ar="تم جلب بيانات السائق.",
        lang=lang,
    )
