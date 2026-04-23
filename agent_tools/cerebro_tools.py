from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_BACKEND_URL = os.getenv("CEREBRO_BACKEND_URL", "http://127.0.0.1:8000")


def _request(method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> dict[str, Any]:
    url = f"{DEFAULT_BACKEND_URL.rstrip('/')}{path}"
    with httpx.Client(timeout=20.0) as client:
        response = client.request(method, url, params=params, json=json)
        response.raise_for_status()
        return response.json()


def get_bus_location(lang: str = "en") -> dict[str, Any]:
    """Fetch live bus location and route state for Cerebro assistant."""
    return _request("GET", "/bus/location", params={"lang": lang})


def predict_bus_arrival(student_location: str | None = None, lang: str = "en") -> dict[str, Any]:
    """Predict bus arrival for a location and from model output."""
    eta_now = _request(
        "GET",
        "/bus/eta",
        params={"student_location": student_location, "lang": lang},
    )
    eta_model = _request("GET", "/bus/eta/predicted", params={"lang": lang})
    return {
        "live_eta": eta_now,
        "predicted_eta": eta_model,
    }


def pay_bus_fee(
    student_id: int,
    amount: float,
    payment_type: str = "trip",
    force_fail: bool = False,
    lang: str = "en",
) -> dict[str, Any]:
    """Pay trip fee or monthly subscription from student wallet."""
    return _request(
        "POST",
        "/wallet/pay",
        params={"lang": lang},
        json={
            "student_id": student_id,
            "amount": amount,
            "payment_type": payment_type,
            "force_fail": force_fail,
        },
    )


def check_wallet(student_id: int, lang: str = "en") -> dict[str, Any]:
    """Fetch wallet balance and subscription status for a student."""
    return _request(
        "GET",
        "/wallet/balance",
        params={"student_id": student_id, "lang": lang},
    )


def report_delay(
    description: str,
    reporter_name: str = "Cerebro Agent",
    eta_impact_minutes: int = 8,
    lang: str = "en",
) -> dict[str, Any]:
    """Report a delay incident that immediately affects ETA calculations."""
    return _request(
        "POST",
        "/report/incident",
        params={"lang": lang},
        json={
            "reporter_role": "system",
            "reporter_name": reporter_name,
            "incident_type": "delay",
            "description": description,
            "eta_impact_minutes": eta_impact_minutes,
        },
    )


def list_cerebro_tools() -> dict[str, str]:
    """Tool registry metadata for assistant orchestration layers."""
    return {
        "get_bus_location": "Retrieve current bus location and status",
        "predict_bus_arrival": "Predict ETA using live and historical simulation data",
        "pay_bus_fee": "Pay trip or subscription fees from student wallet",
        "check_wallet": "Check student wallet balance and subscription",
        "report_delay": "Report delay incident impacting ETA",
    }
