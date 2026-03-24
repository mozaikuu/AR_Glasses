from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from tools.vision.moondream import analyze_image, analyze_live_camera

app = FastAPI(title="Smart Glasses MCP Server", version="0.1.0")


class VisionCaptureRequest(BaseModel):
    prompt: str = Field(default="Describe what you see")
    camera_index: int | None = Field(default=None)
    camera_candidates: list[int] | None = Field(default=None)
    include_image: bool = Field(default=False)


class VisionImageRequest(BaseModel):
    image_base64: str
    prompt: str = Field(default="Describe this image")


@app.get("/")
def root() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "mcp-server",
        "tools": [
            "navigation",
            "speech",
            "vision.capture_moondream",
            "vision.analyze_image_moondream",
        ],
    }


@app.post("/tools/vision/capture-moondream")
def vision_capture_moondream(payload: VisionCaptureRequest) -> dict[str, object]:
    result = analyze_live_camera(
        prompt=payload.prompt,
        camera_index=payload.camera_index,
        camera_candidates=payload.camera_candidates,
    )
    if not payload.include_image and "image_base64" in result:
        result.pop("image_base64", None)
    return result


@app.post("/tools/vision/analyze-image-moondream")
def vision_analyze_image_moondream(payload: VisionImageRequest) -> dict[str, object]:
    answer = analyze_image(image_base64=payload.image_base64, prompt=payload.prompt)
    return {
        "ok": True,
        "text": answer,
        "model": "moondream",
    }
