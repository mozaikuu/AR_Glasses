from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.i18n import response_payload
from app.schemas.report import IncidentReportRequest
from app.services.bus_service import aggregated_active_incidents
from app.services.report_service import create_incident, incident_to_dict


router = APIRouter(tags=["Incidents"])


@router.post("/report/incident")
def report_incident(
    payload: IncidentReportRequest,
    lang: str = "en",
    db: Session = Depends(db_session),
):
    report = create_incident(
        db,
        reporter_role=payload.reporter_role,
        reporter_name=payload.reporter_name,
        incident_type=payload.incident_type,
        description=payload.description,
        eta_impact_minutes=payload.eta_impact_minutes,
    )

    return response_payload(
        {
            **incident_to_dict(report),
            "note": "Incident now contributes to ETA calculations.",
        },
        en="Incident reported successfully.",
        ar="تم الإبلاغ عن الحادث بنجاح.",
        lang=lang,
    )


@router.get("/reports/active")
def get_active_reports(
    lang: str = "en",
    db: Session = Depends(db_session),
):
    incidents = aggregated_active_incidents(db)
    return response_payload(
        {
            "count": len(incidents),
            "incidents": incidents,
        },
        en="Active incidents retrieved.",
        ar="تم جلب البلاغات النشطة.",
        lang=lang,
    )
