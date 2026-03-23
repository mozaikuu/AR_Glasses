from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.api.gateway import (
    health,
    process,
    qr_active,
    qr_hidden,
    qr_telemetry,
    qr_visible,
)
from app.models.requests import ProcessRequest, QrHiddenRequest, QrTelemetryRequest, QrVisibleRequest
from app.models.responses import HealthResponse, ProcessResponse

app = FastAPI(title="Smart Glasses Legacy API v2", version="0.1.0")
router = APIRouter(prefix="/v2")


@router.get("/health", response_model=HealthResponse)
def v2_health() -> HealthResponse:
    return health()


@router.post("/process", response_model=ProcessResponse)
def v2_process(payload: ProcessRequest) -> ProcessResponse:
    return process(payload)


@router.post("/qr/visible")
def v2_qr_visible(payload: QrVisibleRequest) -> dict[str, object]:
    return qr_visible(payload)


@router.post("/qr/hidden")
def v2_qr_hidden(payload: QrHiddenRequest) -> dict[str, object]:
    return qr_hidden(payload)


@router.post("/qr/telemetry")
def v2_qr_telemetry(payload: QrTelemetryRequest) -> dict[str, object]:
    return qr_telemetry(payload)


@router.get("/qr/active")
def v2_qr_active() -> dict[str, object]:
    return qr_active()


app.include_router(router)
