"""
Minimal Moondream-only test runner.

Examples:
    python scripts/test_moondream_only.py --image path/to/image.jpg
    python scripts/test_moondream_only.py --image path/to/image.jpg --query "What text is visible?"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Moondream-only inference test")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--query", default="Describe what you see in detail", help="Prompt to ask Moondream")
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference for Moondream")
    args = parser.parse_args()

    if args.cpu:
        os.environ["MOONDREAM_FORCE_CPU"] = "1"

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"[ERROR] Image not found: {image_path}")
        return 1

    try:
        from tools.vision.moondream import load_model
        from PIL import Image

        model, tokenizer = load_model()
        if model is None:
            print("[ERROR] Moondream failed to load. Check runtime dependencies and model setup.")
            return 2

        image = Image.open(image_path).convert("RGB")
        enc_image = model.encode_image(image)
        if hasattr(model, "answer_question"):
            answer = model.answer_question(enc_image, args.query, tokenizer)
            result = {"answer": answer}
        else:
            result = model.query(enc_image, args.query)
            answer = result.get("answer", "") if isinstance(result, dict) else str(result)

        print("\n===== Moondream Output =====")
        if answer:
            print(answer)
        else:
            print("[WARN] Empty answer field returned.")
            print("Raw model response:")
            print(result)
        print("============================\n")
        return 0

    except Exception as e:
        print(f"[ERROR] Moondream inference failed: {e}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
