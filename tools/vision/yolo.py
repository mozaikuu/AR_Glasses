from __future__ import annotations


def detect_objects(image_base64: str) -> list[str]:
    if not image_base64:
        return []
    return ["person", "door"]
