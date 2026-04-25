from typing import Literal

from pydantic import BaseModel, Field


IncidentType = Literal[
    "traffic_jam",
    "bus_full",
    "breakdown",
    "early_arrival",
    "delay",
]


class IncidentReportRequest(BaseModel):
    reporter_role: Literal["student", "driver", "system"] = "student"
    reporter_name: str | None = None
    incident_type: IncidentType
    description: str = ""
    eta_impact_minutes: int | None = Field(default=None, ge=0, le=60)
