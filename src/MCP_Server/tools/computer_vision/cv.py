import cv2
from ultralytics import YOLO

PATH = "./src/mcp_server/tools/Computer_Vision/"

# Load base model
model = YOLO(PATH + "yolo11n.pt")

def detect_objects() -> str:
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

detect_objects()