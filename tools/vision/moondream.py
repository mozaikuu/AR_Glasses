"""Moondream vision-language model for enhanced scene understanding."""
import sys
from pathlib import Path

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


def load_model():
    """Load the Moondream model."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers import BitsAndBytesConfig
        
        # Quantization config for lower memory usage
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        
        print(f"Loading Moondream model from {MODEL_PATH}...", file=sys.stderr)
        
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, 
            revision=MODEL_REVISION
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            revision=MODEL_REVISION,
            quantization_config=quantization_config,
            device_map={"": "cuda" if torch.cuda.is_available() else "cpu"},
            trust_remote_code=True
        )
        
        print("Moondream model loaded successfully!", file=sys.stderr)
        return model, tokenizer
    except Exception as e:
        print(f"Failed to load Moondream model: {e}", file=sys.stderr)
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
        return f"Vision processing failed: {e}"


def detect_and_describe():
    """Capture image and get detailed description."""
    try:
        import cv2
        
        # Try different camera indices
        camera_ids = [0, 1, 2]
        cap = None
        
        for camera_id in camera_ids:
            try:
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
                if cap.isOpened():
                    break
            except:
                continue
        
        if cap is None or not cap.isOpened():
            return "Camera not available: No working camera found."
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return "Failed to capture image from camera"
        
        # Convert to PIL Image
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Get detailed description
        model, tokenizer = load_model()
        if model is None or tokenizer is None:
            # Fallback to YOLO if Moondream not available
            return _fallback_yolo(frame)
        
        enc_image = model.encode_image(image)
        
        # Get object detection
        objects = model.query(enc_image, "List all objects you see in this image")["answer"]
        
        # Get scene description
        scene = model.query(enc_image, "Describe the overall scene and environment")["answer"]
        
        # Get text detected (signs, labels, etc.)
        text = model.query(enc_image, "Extract any text visible in the image")["answer"]
        
        result = f"Objects detected: {objects}\n\nScene: {scene}\n\nText: {text if text else 'None'}"
        return result
        
    except Exception as e:
        return f"Vision processing failed: {e}"


def _fallback_yolo(frame):
    """Fallback to YOLO if Moondream is not available."""
    try:
        from ultralytics import YOLO
        
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
        
        return f"YOLO Detection (fallback): {', '.join(sorted(detected))}"
    except Exception as e:
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
        return f"Visual question answering failed: {e}"


if __name__ == "__main__":
    # Test the Moondream module
    print("Testing Moondream vision module...")
    result = detect_and_describe()
    print(f"Result: {result}")
