"""Shared utility functions."""
import base64
import io
from PIL import Image
import numpy as np


def image_to_base64(image: np.ndarray) -> str:
    """Convert numpy array image to base64 string."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    img_bytes = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(img_bytes))

