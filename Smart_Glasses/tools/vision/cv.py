"""Computer vision utilities."""
import cv2
from ultralytics import YOLO
from pathlib import Path
import os

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

# Model path - use models directory
MODEL_PATH = MODELS_DIR / "yolo11n.pt"

# Ensure models directory exists
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_model_exists():
    """Download model if it doesn't exist."""
    if not MODEL_PATH.exists():
        print(f"YOLO model not found at {MODEL_PATH}. Downloading...")
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Download using ultralytics
        YOLO("yolo11n.pt").save(str(MODEL_PATH))
        print(f"YOLO model downloaded to {MODEL_PATH}")


# Ensure model exists before loading
_ensure_model_exists()

# Load base model
model = YOLO(str(MODEL_PATH))


def detect_objects() -> str:
    """Detect objects using the camera."""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "Camera capture failed"

    results = model(frame)
    names = model.names

    detected = set()
    for r in results:
        for c in r.boxes.cls:
            detected.add(names[int(c)])

    if not detected:
        return "No objects detected"

    return "Detected: " + ", ".join(detected)

