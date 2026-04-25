from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import bus, reports, students, wallet
from app.core.config import settings
from app.core.i18n import response_payload
from app.core.ws_manager import bus_ws_manager
from app.db.init_db import init_db_and_seed_students
from app.services.runtime_state import runtime_state
from simulation.engine import BusSimulationEngine
from simulation.predictor import BusPredictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_and_seed_students()

    runtime_state.predictor = BusPredictor(seats=50)
    runtime_state.simulation_engine = BusSimulationEngine(
        tick_seconds=settings.simulation_tick_seconds,
        total_seats=50,
    )

    async def tick_broadcast(snapshot: dict):
        await bus_ws_manager.broadcast({"event": "bus_update", "payload": snapshot})

    runtime_state.simulation_engine.register_tick_callback(tick_broadcast)
    await runtime_state.simulation_engine.start()

    try:
        yield
    finally:
        if runtime_state.simulation_engine:
            await runtime_state.simulation_engine.stop()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bus.router)
app.include_router(wallet.router)
app.include_router(students.router)
app.include_router(reports.router)


@app.get("/")
def root(lang: str = "en"):
    return response_payload(
        {
            "name": settings.api_title,
            "version": settings.api_version,
            "docs": "/docs",
            "websocket": "/ws/bus",
        },
        en="NMU Smart Bus Tracking backend is running.",
        ar="خدمة تتبع حافلة جامعة المنصورة الجديدة تعمل الآن.",
        lang=lang,
    )


@app.get("/health")
def health(lang: str = "en"):
    return response_payload(
        {
            "status": "healthy",
            "simulation_running": runtime_state.simulation_engine is not None,
            "predictor_loaded": runtime_state.predictor is not None,
        },
        en="System health check passed.",
        ar="فحص حالة النظام ناجح.",
        lang=lang,
    )


@app.websocket("/ws/bus")
async def bus_websocket(websocket: WebSocket):
    await bus_ws_manager.connect(websocket)
    try:
        if runtime_state.simulation_engine:
            await websocket.send_json(
                {
                    "event": "bus_snapshot",
                    "payload": runtime_state.simulation_engine.snapshot(),
                }
            )

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        bus_ws_manager.disconnect(websocket)
