"""YOLO object detection tool."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ultralytics import YOLO
import cv2
from config.settings import SRC_DIR

# Model path
MODEL_PATH = SRC_DIR / "mcp_server" / "tools" / "computer_vision" / "yolo11n_coco8_trained.pt"


def infer():
    """Run inference on camera frame and return detected objects."""
    import sys

    # Try different camera indices
    camera_ids = [0, 1, 2]
    frame = None
    working_camera = None

    for camera_id in camera_ids:
        cap = None
        try:
            # Try DirectShow backend first (Windows), then fallback to default
            try:
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            except:
                cap = cv2.VideoCapture(camera_id)

            if not cap.isOpened():
                continue

            # Set camera properties for better capture
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # Try to read a frame
            ret, frame = cap.read()

            if ret and frame is not None and frame.size > 0:
                working_camera = camera_id
                print(f"Camera {camera_id} working, frame shape: {frame.shape}", file=sys.stderr)
                break
        except Exception as e:
            print(f"Error with camera {camera_id}: {e}", file=sys.stderr)
        finally:
            if cap is not None:
                cap.release()

    if frame is None or working_camera is None:
        return "Camera not available: No working camera found. Please ensure your camera is connected and permissions are granted."

    # Check if model file exists
    if not MODEL_PATH.exists():
        return f"Vision model not found: {MODEL_PATH}. Please ensure the YOLO model is installed."

    try:
        # Load model
        model = YOLO(str(MODEL_PATH), verbose=False)
        print(f"Model loaded successfully from {MODEL_PATH}", file=sys.stderr)
    except Exception as e:
        return f"Failed to load vision model: {e}"

    try:
        # Run inference
        print("Running YOLO inference...", file=sys.stderr)
        results = model(frame, verbose=False)
        names = model.names

        detected = set()
        for r in results:
            if r.boxes is not None:
                for c in r.boxes.cls:
                    detected.add(names[int(c)])

        if not detected:
            return "Camera capture successful, but no objects detected in the current frame."

        detected_list = sorted(list(detected))
        print(f"Detected objects: {detected_list}", file=sys.stderr)
        return f"Detected: {', '.join(detected_list)}"

    except Exception as e:
        return f"Vision processing failed: {e}"

