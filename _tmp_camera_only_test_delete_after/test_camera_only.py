#!/usr/bin/env python3
"""Temporary camera-only smoke test for ESP endpoint.
Delete folder _tmp_camera_only_test_delete_after after testing.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def _http_get_json(url: str, timeout: float) -> tuple[int, dict | str]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def _http_post_json(url: str, payload: dict, timeout: float) -> tuple[int, dict | str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def main() -> int:
    parser = argparse.ArgumentParser(description="ESP camera-only test")
    parser.add_argument("--esp", default="http://192.168.100.19", help="ESP base URL")
    parser.add_argument("--prompt", default="Describe what you see", help="Prompt sent to /camera/analyze")
    parser.add_argument("--attempts", type=int, default=1, help="How many analyze attempts")
    parser.add_argument("--timeout", type=float, default=40.0, help="HTTP timeout in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between attempts")
    args = parser.parse_args()

    base = args.esp.rstrip("/")
    status_url = f"{base}/camera/status"
    analyze_url = f"{base}/camera/analyze"

    print("=== PRE-STATUS ===")
    pre_code, pre_body = _http_get_json(status_url, args.timeout)
    print(f"status_code={pre_code}")
    print(json.dumps(pre_body, ensure_ascii=True, indent=2) if isinstance(pre_body, dict) else pre_body)

    success = False
    for i in range(1, args.attempts + 1):
        print(f"\n=== ANALYZE ATTEMPT {i}/{args.attempts} ===")
        code, body = _http_post_json(analyze_url, {"prompt": args.prompt}, args.timeout)
        print(f"status_code={code}")
        print(json.dumps(body, ensure_ascii=True, indent=2) if isinstance(body, dict) else body)

        post_code, post_body = _http_get_json(status_url, args.timeout)
        print("--- POST-ATTEMPT STATUS ---")
        print(f"status_code={post_code}")
        print(json.dumps(post_body, ensure_ascii=True, indent=2) if isinstance(post_body, dict) else post_body)

        # Consider only HTTP 200 analyze as capture success.
        if code == 200:
            success = True
            break

        if i < args.attempts:
            time.sleep(max(args.interval, 0.0))

    print("\n=== RESULT ===")
    if success:
        print("CAMERA_CAPTURE_OK")
        return 0

    print("CAMERA_CAPTURE_FAIL")
    return 2


if __name__ == "__main__":
    sys.exit(main())
