"""Computer vision utilities."""
import cv2
from ultralytics import YOLO
from pathlib import Path
from config.settings import SRC_DIR

# Model path
MODEL_PATH = SRC_DIR / "mcp_server" / "tools" / "computer_vision" / "yolo11n.pt"

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

