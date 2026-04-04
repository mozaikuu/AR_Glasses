from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

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

_allow_origins = list(settings.cors_allow_origins) or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in _allow_origins else _allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_runtime_status: dict[str, object] = {
    "preloaded": False,
    "last_warmup_error": "",
}

_mic_test_page = Path("assets/mic_test.html")
_tts_cache_lock = threading.Lock()
_tts_cache: dict[str, tuple[bytes, float]] = {}
_tts_cache_ttl_seconds = 180.0


def _require_unity_api_key(x_unity_api_key: str | None) -> None:
    expected = settings.unity_api_key.strip()
    if not expected:
        return

    provided = (x_unity_api_key or "").strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid Unity API key")


def _probe_mcp() -> tuple[bool, str]:
    if not settings.enable_mcp_server:
        return False, "MCP is disabled by configuration."

    mcp_url = f"http://{settings.mcp_host}:{settings.mcp_port}/"
    try:
        with urlopen(mcp_url, timeout=1.5) as response:
            if response.status == 200:
                return True, ""
            return False, f"Unexpected MCP status: {response.status}"
    except Exception as exc:
        return False, str(exc)


def _detect_lan_ips() -> list[str]:
    candidates: list[str] = []
    hostnames = {"localhost", socket.gethostname()}

    for host in hostnames:
        try:
            _, _, ips = socket.gethostbyname_ex(host)
        except Exception:
            continue

        for ip in ips:
            if ip.startswith("127."):
                continue
            if ip not in candidates:
                candidates.append(ip)

    return candidates


def _prune_tts_cache_locked(now_monotonic: float) -> None:
    expired_tokens = [token for token, (_, expires_at) in _tts_cache.items() if expires_at <= now_monotonic]
    for token in expired_tokens:
        _tts_cache.pop(token, None)


def _store_tts_clip(wav_bytes: bytes) -> str:
    token = f"{int(time.time() * 1000)}_{uuid4().hex}"
    expires_at = time.monotonic() + _tts_cache_ttl_seconds
    with _tts_cache_lock:
        _prune_tts_cache_locked(time.monotonic())
        _tts_cache[token] = (wav_bytes, expires_at)
    return token


def _consume_tts_clip(token: str) -> bytes | None:
    with _tts_cache_lock:
        _prune_tts_cache_locked(time.monotonic())
        item = _tts_cache.pop(token, None)
    if item is None:
        return None
    return item[0]


def _is_streamlit_source(client: str | None, metadata: dict[str, object]) -> bool:
    client_key = (client or "").strip().lower()
    source = str(metadata.get("source") or "").strip().lower()
    return client_key.startswith("streamlit") or source.startswith("streamlit")


def _resolve_wakeword_always_listen(
    scope: str,
    client: str | None,
    metadata: dict[str, object],
    requested: bool,
) -> tuple[bool, str]:
    normalized_scope = (scope or "streamlit-only").strip().lower()
    if normalized_scope in {"off", "disabled", "none"}:
        return requested, "scope_off"

    if normalized_scope in {"all", "global", "everywhere"}:
        return True, "global_forced"

    if normalized_scope in {"streamlit", "streamlit-only", "canary"}:
        if _is_streamlit_source(client, metadata):
            if requested:
                return True, "streamlit_requested"
            return False, "streamlit_disabled"
        if requested:
            return False, "outside_scope_deferred"
        return False, "outside_scope_passthrough"

    return requested, "unknown_scope_passthrough"


def _apply_wakeword_rollout_scope(payload: ProcessRequest) -> tuple[ProcessRequest, bool, str]:
    metadata = payload.metadata if isinstance(payload.metadata, dict) else {}
    metadata = dict(metadata)

    requested = bool(metadata.get("always_listen"))
    if payload.audio_base64:
        effective, scope_reason = _resolve_wakeword_always_listen(
            settings.wakeword_rollout_scope,
            payload.client,
            metadata,
            requested,
        )
        metadata["always_listen"] = effective
    else:
        effective = requested
        scope_reason = "no_audio"

    metadata["wakeword_rollout_scope"] = settings.wakeword_rollout_scope
    metadata["wakeword_rollout_reason"] = scope_reason

    return payload.model_copy(update={"metadata": metadata}), effective, scope_reason


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
    connected, note = _probe_mcp()
    return {
        "connected": connected,
        "enabled": bool(settings.enable_mcp_server),
        "url": f"http://{settings.mcp_host}:{settings.mcp_port}/",
        "note": note,
    }


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
        "wakeword_rollout_scope": settings.wakeword_rollout_scope,
        "preloaded": _runtime_status["preloaded"],
        "last_warmup_error": _runtime_status["last_warmup_error"],
    }


@app.get("/network/info")
def network_info() -> dict[str, object]:
    lan_ips = _detect_lan_ips()
    lan_urls = [f"http://{ip}:{settings.api_port}" for ip in lan_ips]

    return {
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "lan_ips": lan_ips,
        "lan_urls": lan_urls,
        "public_base_url": settings.public_base_url,
        "unity_api_key_required": bool(settings.unity_api_key.strip()),
    }


@app.post("/process", response_model=ProcessResponse)
def process(payload: ProcessRequest) -> ProcessResponse:
    scoped_payload, always_listen_effective, rollout_reason = _apply_wakeword_rollout_scope(payload)
    result = assistant_service.process(scoped_payload)

    result_metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    result_metadata["wakeword_rollout_scope"] = settings.wakeword_rollout_scope
    result_metadata["wakeword_rollout_reason"] = rollout_reason
    result_metadata["always_listen_effective"] = always_listen_effective
    result["metadata"] = result_metadata

    if settings.enable_piper_tts:
        try:
            wav_bytes = synthesize_to_wav(str(result.get("text") or ""))
            if wav_bytes and len(wav_bytes) > 16:
                token = _store_tts_clip(wav_bytes)
                metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
                metadata["tts_url"] = f"/esp/tts/{token}"
                metadata["tts_storage"] = "memory"
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
def unity_voice_command(
    payload: UnityVoiceCommandRequest,
    x_unity_api_key: str | None = Header(default=None, alias="X-Unity-Api-Key"),
) -> dict[str, object]:
    _require_unity_api_key(x_unity_api_key)
    routed = assistant_service.route_unity_command(payload.command, mode=payload.mode)

    # For non-navigation interactions, allow Unity/Quest to include a camera frame
    # so server-side vision can enrich the spoken response.
    if payload.image_base64 and str(routed.get("action") or "").lower() == "speak":
        try:
            processed = assistant_service.process(
                ProcessRequest(
                    text=payload.command,
                    image_base64=payload.image_base64,
                    mode=payload.mode,
                    client=payload.client,
                    metadata=payload.metadata,
                )
            )
            routed["response_text"] = str(processed.get("text") or routed.get("response_text") or "")
            routed["tool_calls"] = processed.get("tool_calls", [])
            routed["metadata"] = processed.get("metadata", {})
        except Exception as exc:
            routed["error"] = f"unity_image_context_failed: {exc}"

    return routed


@app.get("/navigation/locations")
def navigation_locations() -> dict[str, object]:
    return {"locations": navigation_service.list_locations()}


@app.post("/navigation/start", response_model=NavigationSessionResponse)
def navigation_start(payload: NavigationStartRequest) -> NavigationSessionResponse:
    if not navigation_service.is_authoritative_destination_id(payload.destination):
        raise HTTPException(status_code=400, detail="Destination must be a valid navigation.json ID")
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
def navigate_alias(
    payload: NavigationStartRequest,
    x_unity_api_key: str | None = Header(default=None, alias="X-Unity-Api-Key"),
) -> dict[str, object]:
    _require_unity_api_key(x_unity_api_key)
    if not navigation_service.is_authoritative_destination_id(payload.destination):
        raise HTTPException(status_code=400, detail="Destination must be a valid navigation.json ID")
    return {"destination": payload.destination.strip()}


@app.post("/esp/process")
def esp_process(payload: EspProcessRequest) -> dict[str, object]:
    answer = assistant_service.compose_answer(payload.text, mode="quick")
    # Keep both keys for firmware compatibility during migration.
    result = {"text": answer, "response": answer}
    if payload.wants_audio:
        wav_bytes = synthesize_to_wav(answer)
        if wav_bytes and len(wav_bytes) > 16:
            token = _store_tts_clip(wav_bytes)
            result["tts_url"] = f"/esp/tts/{token}"
            result["tts_storage"] = "memory"
        else:
            result["tts_error"] = "tts_unavailable"
    return result


@app.get("/esp/tts/{filename}")
def esp_tts(filename: str) -> Response:
    wav_bytes = _consume_tts_clip(filename)
    if wav_bytes is None:
        raise HTTPException(status_code=404, detail="TTS file not found")
    return Response(content=wav_bytes, media_type="audio/wav", headers={"Cache-Control": "no-store"})


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
