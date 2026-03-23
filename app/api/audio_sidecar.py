from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Smart Glasses Audio Sidecar", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "audio-sidecar"}
