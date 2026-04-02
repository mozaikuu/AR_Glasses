from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_file_settings() -> dict[str, Any]:
    # Prefer root-level local settings so local dev can run without env vars.
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "local.settings.json",
        repo_root / "app" / "config" / "local.settings.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                # Fall through to defaults if local settings are malformed.
                return {}
    return {}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_file_settings = _load_file_settings()


def _pick(key: str, default: str) -> str:
    # Env vars override local file settings for production flexibility.
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    raw = _file_settings.get(key, default)
    return str(raw)


def _pick_bool(key: str, default: bool) -> bool:
    env_value = os.getenv(key)
    if env_value is not None:
        return _as_bool(env_value, default=default)
    raw = _file_settings.get(key, default)
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    return _as_bool(str(raw), default=default)


def _pick_int(key: str, default: int) -> int:
    env_value = os.getenv(key)
    if env_value is not None:
        return int(env_value)
    raw = _file_settings.get(key, default)
    return int(raw)


def _pick_csv(key: str, default: str) -> tuple[str, ...]:
    env_value = os.getenv(key)
    if env_value is not None:
        raw = env_value
    else:
        raw = _file_settings.get(key, default)

    if isinstance(raw, list):
        return tuple(str(item).strip() for item in raw if str(item).strip())

    text = str(raw)
    parts = [part.strip() for part in text.split(",")]
    return tuple(part for part in parts if part)


@dataclass(frozen=True)
class Settings:
    api_host: str = _pick("API_HOST", "0.0.0.0")
    api_port: int = _pick_int("API_PORT", 8000)
    debug: bool = _pick_bool("DEBUG", default=False)
    auto_start_wakeword: bool = _pick_bool("AUTO_START_WAKEWORD", default=True)
    preload_on_startup: bool = _pick_bool("PRELOAD_ON_STARTUP", default=True)

    # Flask interface defaults
    flask_host: str = _pick("FLASK_HOST", "0.0.0.0")
    flask_port: int = _pick_int("FLASK_PORT", 5000)
    enable_flask: bool = _pick_bool("ENABLE_FLASK", default=False)

    # Streamlit interface defaults
    streamlit_host: str = _pick("STREAMLIT_HOST", "0.0.0.0")
    streamlit_port: int = _pick_int("STREAMLIT_PORT", 8501)
    streamlit_app_path: str = _pick("STREAMLIT_APP_PATH", "streamlit_app.py")
    enable_streamlit: bool = _pick_bool("ENABLE_STREAMLIT", default=True)

    # Optional sidecar
    audio_sidecar_host: str = _pick("AUDIO_SIDECAR_HOST", "0.0.0.0")
    audio_sidecar_port: int = _pick_int("AUDIO_SIDECAR_PORT", 8010)
    enable_audio_sidecar: bool = _pick_bool("ENABLE_AUDIO_SIDECAR", default=True)

    # MCP sidecar
    mcp_host: str = _pick("MCP_HOST", "127.0.0.1")
    mcp_port: int = _pick_int("MCP_PORT", 8020)
    enable_mcp_server: bool = _pick_bool("ENABLE_MCP_SERVER", default=True)

    # AI provider setup
    model_provider: str = _pick("MODEL_PROVIDER", "cerebras")
    model_id: str = _pick("MODEL_ID", "llama-3.1-8b")
    api_base_url: str = _pick("API_BASE_URL", "https://api.cerebras.ai/v1")
    api_key: str = _pick("API_KEY", "")
    max_agent_loops: int = _pick_int("MAX_AGENT_LOOPS", 3)
    max_answer_sentences: int = _pick_int("MAX_ANSWER_SENTENCES", 3)

    # Client/network settings
    cors_allow_origins: tuple[str, ...] = _pick_csv("CORS_ALLOW_ORIGINS", "*")
    public_base_url: str = _pick("PUBLIC_BASE_URL", "")
    unity_api_key: str = _pick("UNITY_API_KEY", "")

    # TTS (Piper)
    enable_piper_tts: bool = _pick_bool("ENABLE_PIPER_TTS", default=True)
    piper_exe: str = _pick(
        "PIPER_EXE",
        "Smart_Glasses/models/piper/piper.exe" if os.name == "nt" else "piper",
    )
    piper_model_path: str = _pick(
        "PIPER_MODEL_PATH",
        "Smart_Glasses/models/piper/en_US-lessac-medium.onnx",
    )
    piper_config_path: str = _pick(
        "PIPER_CONFIG_PATH",
        "Smart_Glasses/models/piper/en_US-lessac-medium.onnx.json",
    )

    # Launcher profile
    launcher_profile: str = _pick("LAUNCHER_PROFILE", "production-local")
    restart_crashed_services: bool = _pick_bool("RESTART_CRASHED_SERVICES", default=True)
    auto_reload: bool = _pick_bool("AUTO_RELOAD", default=True)


settings = Settings()
