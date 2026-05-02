from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.bus_service import bus_orchestrator_ready


def require_runtime_ready() -> None:
    if not bus_orchestrator_ready():
        raise HTTPException(status_code=503, detail="Simulation runtime not initialized yet")


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
