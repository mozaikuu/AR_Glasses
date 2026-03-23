from __future__ import annotations

import threading
import time
from pathlib import Path
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config.settings import settings
from app.models.requests import (
    AudioSelectRequest,
    EspProcessRequest,
    NavigationCancelRequest,
    NavigationNextRequest,
    NavigationStartRequest,
    ProcessRequest,
    QrHiddenRequest,
    QrTelemetryRequest,
    QrVisibleRequest,
    RecordRequest,
    TextRequest,
    UnityVoiceCommandRequest,
)
from app.models.responses import HealthResponse, NavigationSessionResponse, ProcessResponse
from app.services.assistant_service import assistant_service
from app.services.audio_service import audio_service
from app.services.navigation_service import navigation_service
from app.services.qr_service import qr_service
from tools.speech.tts import synthesize_to_wav

app = FastAPI(title="Smart Glasses Distilled Gateway", version="0.1.0")

_runtime_status: dict[str, object] = {
    "preloaded": False,
    "last_warmup_error": "",
}

_tts_root = Path("assets/esp_tts")
_tts_root.mkdir(parents=True, exist_ok=True)
_mic_test_page = Path("assets/mic_test.html")


def _warmup_runtime() -> None:
    try:
        # Warm up the LLM adapter path so first user request has lower latency.
        assistant_service.compose_answer(text="warmup", mode="quick")
        _runtime_status["preloaded"] = True
        _runtime_status["last_warmup_error"] = ""
    except Exception as exc:
        _runtime_status["preloaded"] = False
        _runtime_status["last_warmup_error"] = str(exc)


@app.on_event("startup")
def on_startup() -> None:
    if settings.auto_start_wakeword:
        audio_service.start_wakeword()
    if settings.preload_on_startup:
        # Warmup runs in a daemon thread to avoid blocking service availability.
        thread = threading.Thread(target=_warmup_runtime, daemon=True)
        thread.start()


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="smart-glasses-gateway", version=app.version)


@app.get("/mic-test")
def mic_test() -> FileResponse:
    if not _mic_test_page.exists():
        raise HTTPException(status_code=404, detail="Mic test page not found")
    return FileResponse(path=_mic_test_page, media_type="text/html", filename="mic_test.html")


@app.get("/mcp-status")
def mcp_status() -> dict[str, object]:
    if not settings.enable_mcp_server:
        return {"connected": False, "enabled": False, "note": "MCP is disabled by configuration."}

    mcp_url = f"http://{settings.mcp_host}:{settings.mcp_port}/"
    try:
        with urlopen(mcp_url, timeout=1.5) as response:
            return {"connected": response.status == 200, "enabled": True, "url": mcp_url}
    except Exception as exc:
        return {"connected": False, "enabled": True, "url": mcp_url, "note": str(exc)}


@app.get("/debug")
def debug_status() -> dict[str, object]:
    return {
        "debug": settings.debug,
        "model_provider": settings.model_provider,
        "selected_audio_device": audio_service.get_selected_device(),
        "wakeword_running": audio_service.wakeword_status(),
        "active_qr_markers": len(qr_service.active()),
        "flask_enabled": settings.enable_flask,
        "audio_sidecar_enabled": settings.enable_audio_sidecar,
        "mcp_enabled": settings.enable_mcp_server,
        "preloaded": _runtime_status["preloaded"],
        "last_warmup_error": _runtime_status["last_warmup_error"],
    }


@app.post("/process", response_model=ProcessResponse)
def process(payload: ProcessRequest) -> ProcessResponse:
    result = assistant_service.process(payload)
    if settings.enable_piper_tts:
        try:
            wav_bytes = synthesize_to_wav(str(result.get("text") or ""))
            if wav_bytes and len(wav_bytes) > 16:
                filename = f"response_{int(time.time() * 1000)}.wav"
                wav_path = _tts_root / filename
                wav_path.write_bytes(wav_bytes)
                metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
                metadata["tts_url"] = f"/esp/tts/{filename}"
                result["metadata"] = metadata
        except Exception as exc:
            metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
            metadata["tts_error"] = str(exc)
            result["metadata"] = metadata
    return ProcessResponse(**result)


@app.post("/run", response_model=ProcessResponse)
def run(payload: TextRequest) -> ProcessResponse:
    return ProcessResponse(**assistant_service.run_text(payload))


@app.get("/audio/devices")
def list_audio_devices() -> dict[str, object]:
    return {"devices": audio_service.list_devices(), "selected": audio_service.get_selected_device()}


@app.post("/audio/select")
def select_audio(payload: AudioSelectRequest) -> dict[str, object]:
    if not audio_service.select_device(payload.device_id):
        raise HTTPException(status_code=404, detail="Audio device not found")
    return {"selected": audio_service.get_selected_device()}


@app.post("/control/start")
def start_control() -> dict[str, object]:
    audio_service.start_wakeword()
    return {"wakeword": "running"}


@app.post("/control/stop")
def stop_control() -> dict[str, object]:
    audio_service.stop_wakeword()
    return {"wakeword": "stopped"}


@app.post("/record")
def record(payload: RecordRequest) -> dict[str, object]:
    return {
        "duration_seconds": payload.duration_seconds,
        "transcript": "Record endpoint is active. Wire actual STT provider here.",
    }


@app.post("/unity/voice-command")
def unity_voice_command(payload: UnityVoiceCommandRequest) -> dict[str, object]:
    routed = assistant_service.route_unity_command(payload.command, mode=payload.mode)
    if routed.get("action") == "navigate" and "destination" in routed:
        routed["destination"] = navigation_service.normalize_destination(str(routed["destination"]))
    return routed


@app.get("/navigation/locations")
def navigation_locations() -> dict[str, object]:
    return {"locations": navigation_service.list_locations()}


@app.post("/navigation/start", response_model=NavigationSessionResponse)
def navigation_start(payload: NavigationStartRequest) -> NavigationSessionResponse:
    return NavigationSessionResponse(**navigation_service.start(payload.destination, start=payload.start))


@app.post("/navigation/next", response_model=NavigationSessionResponse)
def navigation_next(payload: NavigationNextRequest) -> NavigationSessionResponse:
    status = navigation_service.next_step(payload.session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Navigation session not found")
    return NavigationSessionResponse(**status)


@app.get("/navigation/status", response_model=NavigationSessionResponse)
def navigation_status(session_id: str) -> NavigationSessionResponse:
    status = navigation_service.status(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Navigation session not found")
    return NavigationSessionResponse(**status)


@app.post("/navigation/cancel")
def navigation_cancel(payload: NavigationCancelRequest) -> dict[str, object]:
    ok = navigation_service.cancel(payload.session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Navigation session not found")
    return {"cancelled": True, "session_id": payload.session_id}


@app.post("/navigate")
def navigate_alias(payload: NavigationStartRequest) -> dict[str, object]:
    # Unity MVP contract from NAVIGATION_PLAN.md: destination echo.
    return {"destination": navigation_service.normalize_destination(payload.destination)}


@app.post("/esp/process")
def esp_process(payload: EspProcessRequest) -> dict[str, object]:
    result = {"text": assistant_service.compose_answer(payload.text, mode="quick")}
    if payload.wants_audio:
        filename = "latest.wav"
        wav_path = _tts_root / filename
        wav_path.write_bytes(b"RIFF....WAVEfmt ")
        result["tts_url"] = f"/esp/tts/{filename}"
    return result


@app.get("/esp/tts/{filename}")
def esp_tts(filename: str) -> FileResponse:
    wav_path = _tts_root / filename
    if not wav_path.exists():
        raise HTTPException(status_code=404, detail="TTS file not found")
    return FileResponse(path=wav_path, media_type="audio/wav", filename=filename)


@app.post("/qr/visible")
def qr_visible(payload: QrVisibleRequest) -> dict[str, object]:
    qr_service.set_visible(payload.qr_id, payload.payload)
    return {"ok": True, "active_count": len(qr_service.active())}


@app.post("/qr/hidden")
def qr_hidden(payload: QrHiddenRequest) -> dict[str, object]:
    qr_service.set_hidden(payload.qr_id)
    return {"ok": True, "active_count": len(qr_service.active())}


@app.get("/qr/active")
def qr_active() -> dict[str, object]:
    return {"active": qr_service.active()}


@app.post("/qr/telemetry")
def qr_telemetry(payload: QrTelemetryRequest) -> dict[str, object]:
    qr_service.add_telemetry(payload.qr_id, payload.event, payload.metadata)
    return {"ok": True, "telemetry_count": qr_service.telemetry_count()}
