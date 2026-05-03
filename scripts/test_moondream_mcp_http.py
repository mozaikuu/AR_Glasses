"""Smoke-test Moondream MCP HTTP endpoints (GET / and POST analyze-image).

Uses env MCP_HOST (default 127.0.0.1) and MCP_PORT (default 8020).
Exits 0 if the server responds; analyze-image may still return a Moondream
dependency error string if torch/transformers are missing.
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment, misc]


def _minimal_jpeg_bytes() -> bytes:
    if Image is None:
        raise RuntimeError("Pillow is required to build a test JPEG (pip install pillow).")
    im = Image.new("RGB", (4, 4), color=(220, 30, 30))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def main() -> int:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8020"))
    base = f"http://{host}:{port}"

    try:
        with urlopen(base + "/", timeout=5.0) as r:
            root = json.loads(r.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"GET {base}/ failed: {e}", file=sys.stderr)
        return 1

    try:
        jpeg = _minimal_jpeg_bytes()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print("GET / ->", root.get("status"), root.get("tools", [])[:4], "...")

    payload = json.dumps(
        {
            "image_base64": base64.b64encode(jpeg).decode("ascii"),
            "prompt": "What color is this image? One short phrase.",
        }
    ).encode("utf-8")
    req = Request(
        f"{base}/tools/vision/analyze-image-moondream",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=120.0) as r:
            body = json.loads(r.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"POST analyze-image-moondream failed: {e}", file=sys.stderr)
        return 1

    text = str(body.get("text") or "").strip()
    print("POST analyze-image-moondream -> ok=", body.get("ok"), "text_len=", len(text))
    if text:
        preview = text[:200] + ("..." if len(text) > 200 else "")
        print("text preview:", preview)
    else:
        print("empty text in response:", body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
