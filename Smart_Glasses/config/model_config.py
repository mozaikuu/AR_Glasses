"""LLM model configuration."""
import torch
from config.settings import MODEL_ID, DEVICE

def get_device():
    """Get the device to use for model inference."""
    if DEVICE == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"

def get_torch_dtype(device: str):
    """Get the appropriate torch dtype for the device."""
    if device == "cuda":
        return torch.bfloat16
    return torch.float32

