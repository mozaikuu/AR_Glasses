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
import os

# Optional: suppress Windows symlink cache warning (non-fatal).
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Moondream model configuration
MODEL_NAME = "vikhyatk/moondream2"
MODEL_REVISION = "2025-01-09"
MODEL_PATH = BASE_DIR / "models" / "moondream"

# Global model cache
_cached_model = None
_cached_tokenizer = None
_model_lock = threading.Lock()


def _patch_transformers_tied_weights_compat():
    """
    Patch transformers to tolerate custom model classes that expose only
    `_tied_weights_keys` (older remote-code convention) instead of the newer
    `all_tied_weights_keys`.
    """
    from transformers.modeling_utils import PreTrainedModel
    if getattr(PreTrainedModel, "_sg_tied_weights_patch_applied", False):
        return

    # Newer transformers expects `all_tied_weights_keys`; older remote-code
    # models often provide only `_tied_weights_keys`.
    if not hasattr(PreTrainedModel, "all_tied_weights_keys"):
        def _all_tied_weights_keys(self):
            legacy = getattr(self, "_tied_weights_keys", None)
            if isinstance(legacy, dict):
                return legacy
            if isinstance(legacy, (list, tuple, set)):
                return {k: True for k in legacy}
            return {}

        PreTrainedModel.all_tied_weights_keys = property(_all_tied_weights_keys)

    original = getattr(PreTrainedModel, "mark_tied_weights_as_initialized", None)

    # Some transformers versions do not expose this hook at all.
    if original is not None:
        def _patched_mark_tied_weights_as_initialized(self):
            all_tied = getattr(self, "all_tied_weights_keys", None)
            if isinstance(all_tied, dict):
                for tied_param in all_tied.keys():
                    param = self.get_parameter(tied_param)
                    param._is_hf_initialized = True
                return

            legacy_tied = getattr(self, "_tied_weights_keys", None)
            if isinstance(legacy_tied, dict):
                keys = legacy_tied.keys()
            elif isinstance(legacy_tied, (list, tuple, set)):
                keys = legacy_tied
            else:
                return

            for tied_param in keys:
                try:
                    param = self.get_parameter(tied_param)
                    param._is_hf_initialized = True
                except Exception:
                    # Ignore stale or incompatible tied-weight paths from remote code.
                    continue

        PreTrainedModel.mark_tied_weights_as_initialized = _patched_mark_tied_weights_as_initialized
    PreTrainedModel._sg_tied_weights_patch_applied = True
    PreTrainedModel._sg_original_mark_tied_weights_as_initialized = original


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
        _patch_transformers_tied_weights_compat()
        
        print(f"Loading Moondream model: {MODEL_NAME}", file=sys.stderr)
        
        force_cpu = os.environ.get("MOONDREAM_FORCE_CPU", "").lower() in {"1", "true", "yes"}
        device = "cpu" if force_cpu else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Moondream: Using device: {device}", file=sys.stderr)

        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, 
            revision=MODEL_REVISION
        )
        # NOTE:
        # Do not use BitsAndBytes 4-bit quantization with this Moondream class.
        # It triggers transformers quantizer assumptions (all_tied_weights_keys) that
        # are incompatible with trust_remote_code model classes.
        model_kwargs = {
            "revision": MODEL_REVISION,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        if device == "cuda":
            model_kwargs["torch_dtype"] = torch.float16
        else:
            model_kwargs["torch_dtype"] = torch.float32

        # Prefer local cache directory if available.
        if MODEL_PATH.exists():
            os.environ.setdefault("HF_HOME", str(MODEL_PATH))

        try:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                **model_kwargs,
            )
        except OSError as e:
            if device == "cuda":
                print(f"Moondream CUDA load failed ({e}). Retrying on CPU...", file=sys.stderr)
                model_kwargs["torch_dtype"] = torch.float32
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    **model_kwargs,
                )
            else:
                raise
        if device == "cuda":
            model = model.to("cuda")
        model.eval()
        
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
        if hasattr(model, "answer_question"):
            answer = model.answer_question(enc_image, query, tokenizer)
        else:
            answer = model.query(enc_image, query).get("answer", "")
        
        return answer
        
    except Exception as e:
        print(f"Vision processing error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Vision processing failed: {e}"


def detect_and_describe(query: str = "Describe what you see in detail"):
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
        
        # Get description/answer based on the caller-provided query.
        model, tokenizer = load_model()
        if model is None or tokenizer is None:
            print("Moondream not available, falling back to YOLO", file=sys.stderr)
            return _fallback_yolo(frame)

        print("Encoding image with Moondream...", file=sys.stderr)
        enc_image = model.encode_image(image)

        print(f"Querying Moondream with: {query}", file=sys.stderr)
        if hasattr(model, "answer_question"):
            answer = model.answer_question(enc_image, query, tokenizer)
        else:
            answer = model.query(enc_image, query).get("answer", "")

        answer = (answer or "").strip()
        if not answer:
            return "I captured an image but could not extract a confident answer."

        print(f"Moondream result: {answer[:100]}...", file=sys.stderr)
        return answer
        
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
        if hasattr(model, "answer_question"):
            answer = model.answer_question(enc_image, question, tokenizer)
        else:
            answer = model.query(enc_image, question).get("answer", "")
        
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
