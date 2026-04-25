from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IncidentReport


INCIDENT_IMPACT_DEFAULTS = {
    "traffic_jam": 12,
    "bus_full": 4,
    "breakdown": 20,
    "early_arrival": -6,
    "delay": 8,
}


def create_incident(
    db: Session,
    reporter_role: str,
    reporter_name: str | None,
    incident_type: str,
    description: str,
    eta_impact_minutes: int | None = None,
) -> IncidentReport:
    report = IncidentReport(
        reporter_role=reporter_role,
        reporter_name=reporter_name or "anonymous",
        incident_type=incident_type,
        description=description,
        eta_impact_minutes=(
            eta_impact_minutes
            if eta_impact_minutes is not None
            else INCIDENT_IMPACT_DEFAULTS.get(incident_type, 0)
        ),
        is_active=True,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def deactivate_stale_incidents(db: Session, ttl_minutes: int = 120) -> None:
    threshold = datetime.utcnow() - timedelta(minutes=ttl_minutes)
    stale_reports = db.scalars(
        select(IncidentReport).where(
            IncidentReport.is_active.is_(True),
            IncidentReport.created_at < threshold,
        )
    ).all()

    changed = False
    for report in stale_reports:
        report.is_active = False
        report.resolved_at = datetime.utcnow()
        changed = True

    if changed:
        db.commit()


def get_active_incidents(db: Session) -> list[IncidentReport]:
    deactivate_stale_incidents(db)
    return db.scalars(
        select(IncidentReport).where(IncidentReport.is_active.is_(True)).order_by(IncidentReport.created_at.desc())
    ).all()


def incident_to_dict(report: IncidentReport) -> dict:
    return {
        "id": report.id,
        "reporter_role": report.reporter_role,
        "reporter_name": report.reporter_name,
        "incident_type": report.incident_type,
        "description": report.description,
        "eta_impact_minutes": report.eta_impact_minutes,
        "is_active": report.is_active,
        "created_at": report.created_at.isoformat(),
    }
