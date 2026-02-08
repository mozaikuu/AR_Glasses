"""Moondream vision-language model for enhanced scene understanding."""
import sys
from pathlib import Path
import threading

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import BASE_DIR
import torch
from PIL import Image
import base64
import io

# Moondream model configuration
MODEL_NAME = "vikhyatk/moondream2"
MODEL_REVISION = "2025-01-09"
MODEL_PATH = BASE_DIR / "models" / "moondream"

# Global model cache
_cached_model = None
_cached_tokenizer = None
_model_lock = threading.Lock()


def load_model():
    """
    Load the Moondream model with caching.
    Returns (model, tokenizer) tuple or (None, None) if loading fails.
    """
    global _cached_model, _cached_tokenizer
    
    with _model_lock:
        # Return cached model if already loaded
        if _cached_model is not None and _cached_tokenizer is not None:
            print("Moondream: Using cached model", file=sys.stderr)
            return _cached_model, _cached_tokenizer
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers import BitsAndBytesConfig
        
        print(f"Loading Moondream model: {MODEL_NAME}", file=sys.stderr)
        
        # Quantization config for lower memory usage
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, 
            revision=MODEL_REVISION
        )
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Moondream: Using device: {device}", file=sys.stderr)
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            revision=MODEL_REVISION,
            quantization_config=quantization_config,
            device_map={"": device},
            trust_remote_code=True
        )
        
        with _model_lock:
            _cached_model = model
            _cached_tokenizer = tokenizer
        
        print("Moondream model loaded successfully!", file=sys.stderr)
        return model, tokenizer
        
    except Exception as e:
        print(f"Failed to load Moondream model: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None, None


def infer_from_image(image_path: str = None, image_data: bytes = None, query: str = "Describe what you see in detail"):
    """
    Run Moondream inference on an image.
    
    Args:
        image_path: Path to image file
        image_data: Raw image bytes
        query: Question about the image
    
    Returns:
        str: Description of the image
    """
    try:
        model, tokenizer = load_model()
        if model is None or tokenizer is None:
            return "Vision model not available"
        
        # Load image
        if image_data:
            image = Image.open(io.BytesIO(image_data))
        elif image_path:
            image = Image.open(image_path)
        else:
            # Try to capture from camera
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Camera not available"
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return "Failed to capture image"
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Process with Moondream
        print(f"Running Moondream query: {query}", file=sys.stderr)
        
        enc_image = model.encode_image(image)
        answer = model.query(enc_image, query)["answer"]
        
        return answer
        
    except Exception as e:
        print(f"Vision processing error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Vision processing failed: {e}"


def detect_and_describe():
    """
    Capture image from camera and get detailed description.
    
    Returns:
        str: Detailed description of the scene
    """
    try:
        import cv2
        
        # Try different camera indices
        camera_ids = [0, 1, 2]
        cap = None
        
        for camera_id in camera_ids:
            try:
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
                if cap.isOpened():
                    print(f"Camera {camera_id} opened successfully", file=sys.stderr)
                    break
            except Exception as e:
                print(f"Camera {camera_id} error: {e}", file=sys.stderr)
                continue
        
        if cap is None or not cap.isOpened():
            print("No working camera found", file=sys.stderr)
            return "Camera not available: No working camera found. Please ensure camera is connected and permissions granted."
        
        # Capture frame
        print("Capturing frame...", file=sys.stderr)
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return "Failed to capture image from camera"
        
        print(f"Frame captured: {frame.shape}", file=sys.stderr)
        
        # Convert to PIL Image
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Get detailed description
        model, tokenizer = load_model()
        if model is None or tokenizer is None:
            print("Moondream not available, falling back to YOLO", file=sys.stderr)
            return _fallback_yolo(frame)
        
        print("Encoding image with Moondream...", file=sys.stderr)
        enc_image = model.encode_image(image)
        
        # Get object detection
        print("Querying for objects...", file=sys.stderr)
        objects = model.query(enc_image, "List all objects you see")["answer"]
        
        # Get scene description
        print("Querying for scene description...", file=sys.stderr)
        scene = model.query(enc_image, "Describe the overall scene")["answer"]
        
        # Get text detected
        print("Querying for text...", file=sys.stderr)
        text = model.query(enc_image, "Extract any text visible")["answer"]
        
        result = f"Objects: {objects}\n\nScene: {scene}\n\nText: {text if text else 'None'}"
        print(f"Moondream result: {result[:100]}...", file=sys.stderr)
        return result
        
    except Exception as e:
        print(f"Vision processing error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Vision processing failed: {e}"


def _fallback_yolo(frame):
    """Fallback to YOLO if Moondream is not available."""
    try:
        from ultralytics import YOLO
        
        print("Loading YOLO fallback...", file=sys.stderr)
        model = YOLO("yolo11n.pt")
        results = model(frame, verbose=False)
        names = model.names
        
        detected = set()
        for r in results:
            if r.boxes is not None:
                for c in r.boxes.cls:
                    detected.add(names[int(c)])
        
        if not detected:
            return "Camera capture successful, but no objects detected."
        
        return f"YOLO Detection: {', '.join(sorted(detected))}"
        
    except Exception as e:
        print(f"YOLO fallback error: {e}", file=sys.stderr)
        return f"Both Moondream and YOLO failed: {e}"


def answer_visual_question(question: str, image_path: str = None, image_data: bytes = None) -> str:
    """
    Answer a specific question about an image.
    
    Args:
        question: Question about the image
        image_path: Path to image file
        image_data: Raw image bytes
    
    Returns:
        str: Answer to the question
    """
    try:
        model, tokenizer = load_model()
        if model is None or tokenizer is None:
            return "Vision model not available"
        
        # Load image
        if image_data:
            image = Image.open(io.BytesIO(image_data))
        elif image_path:
            image = Image.open(image_path)
        else:
            return "No image provided"
        
        enc_image = model.encode_image(image)
        answer = model.query(enc_image, question)["answer"]
        
        return answer
        
    except Exception as e:
        print(f"Visual question answering error: {e}", file=sys.stderr)
        return f"Visual question answering failed: {e}"


if __name__ == "__main__":
    # Test the Moondream module
    print("=" * 60)
    print("Testing Moondream vision module")
    print("=" * 60)
    
    try:
        result = detect_and_describe()
        print(f"\nResult:\n{result}")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
