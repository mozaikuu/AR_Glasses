from __future__ import annotations

import base64
import io
import os
import threading
from typing import Any


_model_lock = threading.Lock()
_cached_model: Any = None
_cached_tokenizer: Any = None


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_model() -> tuple[Any, Any] | tuple[None, None]:
    global _cached_model, _cached_tokenizer

    with _model_lock:
        if _cached_model is not None and _cached_tokenizer is not None:
            return _cached_model, _cached_tokenizer

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = os.getenv("MOONDREAM_MODEL_NAME", "vikhyatk/moondream2")
        model_revision = os.getenv("MOONDREAM_REVISION", "2025-01-09")
        force_cpu = _to_bool(os.getenv("MOONDREAM_FORCE_CPU"), default=False)
        device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")

        tokenizer = AutoTokenizer.from_pretrained(model_name, revision=model_revision)

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            revision=model_revision,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=(torch.float16 if device == "cuda" else torch.float32),
        )
        if device == "cuda":
            model = model.to("cuda")
        model.eval()

        with _model_lock:
            _cached_model = model
            _cached_tokenizer = tokenizer
        return model, tokenizer
    except Exception:
        return None, None


def _open_camera(candidate_indexes: list[int]) -> tuple[Any, int] | tuple[None, None]:
    import cv2

    for idx in candidate_indexes:
        cap = None
        try:
            # CAP_DSHOW is usually more stable on Windows; fallback is handled automatically.
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(idx)
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                continue
            return cap, idx
        except Exception:
            if cap is not None:
                cap.release()
            continue
    return None, None


def capture_frame(
    camera_index: int | None = None,
    camera_candidates: list[int] | None = None,
) -> tuple[bytes | None, int | None, str | None]:
    """Capture one camera frame and return JPEG bytes."""
    try:
        import cv2
    except Exception:
        return None, None, "opencv-python is not installed"

    indexes = [camera_index] if camera_index is not None else (camera_candidates or [0, 1, 2])
    cap, used_index = _open_camera(indexes)
    if cap is None:
        return None, None, "No working camera found"

    try:
        # Warm-up reads improve reliability on some webcams.
        for _ in range(3):
            cap.read()
        ok, frame = cap.read()
        if not ok or frame is None:
            return None, None, "Failed to capture camera frame"

        ok, jpeg = cv2.imencode(".jpg", frame)
        if not ok:
            return None, None, "Failed to encode frame as JPEG"
        return jpeg.tobytes(), used_index, None
    finally:
        cap.release()


def analyze_image_bytes(image_bytes: bytes, prompt: str = "Describe this image") -> str:
    if not image_bytes:
        return "No image provided"

    model, tokenizer = _load_model()
    if model is None or tokenizer is None:
        return "Moondream unavailable. Install torch, transformers, pillow, and model dependencies."

    try:
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        encoded_image = model.encode_image(image)
        if hasattr(model, "answer_question"):
            answer = model.answer_question(encoded_image, prompt, tokenizer)
        else:
            result = model.query(encoded_image, prompt)
            answer = result.get("answer", "") if isinstance(result, dict) else str(result)
        answer = (answer or "").strip()
        return answer or "I captured an image but could not produce a confident answer."
    except Exception as exc:
        return f"Vision processing failed: {exc}"


def analyze_live_camera(
    prompt: str = "Describe what you see",
    camera_index: int | None = None,
    camera_candidates: list[int] | None = None,
) -> dict[str, Any]:
    """Capture an image from camera and analyze it with Moondream."""
    image_bytes, used_index, capture_error = capture_frame(
        camera_index=camera_index,
        camera_candidates=camera_candidates,
    )
    if capture_error:
        return {
            "ok": False,
            "error": capture_error,
            "model": "moondream",
            "camera_index": used_index,
        }

    answer = analyze_image_bytes(image_bytes=image_bytes or b"", prompt=prompt)
    return {
        "ok": True,
        "text": answer,
        "model": "moondream",
        "camera_index": used_index,
        "image_base64": base64.b64encode(image_bytes or b"").decode("ascii"),
    }


def analyze_image(image_base64: str, prompt: str = "Describe this image") -> str:
    if not image_base64:
        return "No image provided"
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception:
        return "Invalid base64 image payload"
    return analyze_image_bytes(image_bytes=image_bytes, prompt=prompt)
