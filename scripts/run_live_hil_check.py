from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config.settings import settings


def _default_base_url() -> str:
    configured = settings.public_base_url.strip()
    if configured:
        return configured
    return f"http://127.0.0.1:{settings.api_port}"


def _request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    query: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 6.0,
) -> dict[str, object]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    if query:
        url = f"{url}?{urlencode(query)}"

    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=req_headers, method=method)

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"_raw": raw}
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "url": url,
                "body": parsed,
                "error": "",
            }
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"_raw": raw}
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "body": parsed,
            "error": f"HTTP {exc.code}",
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "body": {},
            "error": f"URL error: {exc.reason}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "body": {},
            "error": str(exc),
        }


def _request_binary(url: str, timeout: float = 8.0) -> dict[str, object]:
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = response.read()
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "url": url,
                "content_type": response.headers.get("Content-Type", ""),
                "size_bytes": len(payload),
                "error": "",
            }
    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "content_type": "",
            "size_bytes": 0,
            "error": f"HTTP {exc.code}",
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "content_type": "",
            "size_bytes": 0,
            "error": f"URL error: {exc.reason}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "content_type": "",
            "size_bytes": 0,
            "error": str(exc),
        }


def _add_check(report: dict[str, object], name: str, result: dict[str, object], detail: str = "") -> None:
    entry = {
        "name": name,
        "ok": bool(result.get("ok")),
        "status": int(result.get("status", 0) or 0),
        "url": str(result.get("url", "")),
        "detail": detail,
        "error": str(result.get("error", "")),
    }
    report["checks"].append(entry)
    if not entry["ok"]:
        report["ok"] = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live hardware-in-the-loop smoke checks against a running gateway")
    parser.add_argument("--base-url", default=_default_base_url(), help="Gateway base URL, e.g. http://192.168.1.10:8000")
    parser.add_argument("--unity-api-key", default=settings.unity_api_key.strip(), help="Optional Unity API key")
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--artifact", default=str(REPO_ROOT / "artifacts" / "live_hil_report.json"))
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    unity_headers: dict[str, str] = {}
    if args.unity_api_key.strip():
        unity_headers["X-Unity-Api-Key"] = args.unity_api_key.strip()

    report: dict[str, object] = {
        "ok": True,
        "base_url": base_url,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "checks": [],
    }

    health = _request_json(base_url, "/", timeout=args.timeout)
    _add_check(report, "health", health)

    network_info = _request_json(base_url, "/network/info", timeout=args.timeout)
    _add_check(report, "network_info", network_info)

    debug = _request_json(base_url, "/debug", timeout=args.timeout)
    _add_check(report, "debug", debug)

    voice = _request_json(
        base_url,
        "/unity/voice-command",
        method="POST",
        payload={"command": "take me to ta office", "mode": "quick"},
        headers=unity_headers,
        timeout=args.timeout,
    )
    _add_check(report, "unity_voice_command", voice)

    destination = "TA_Office"
    if isinstance(voice.get("body"), dict):
        destination = str(voice["body"].get("destination") or destination)

    nav_start = _request_json(
        base_url,
        "/navigation/start",
        method="POST",
        payload={"destination": destination, "start": "Entrance"},
        timeout=args.timeout,
    )
    _add_check(report, "navigation_start", nav_start)

    session_id = ""
    if isinstance(nav_start.get("body"), dict):
        session_id = str(nav_start["body"].get("session_id") or "")

    if session_id:
        nav_status = _request_json(
            base_url,
            "/navigation/status",
            query={"session_id": session_id},
            timeout=args.timeout,
        )
        _add_check(report, "navigation_status", nav_status)

        nav_next = _request_json(
            base_url,
            "/navigation/next",
            method="POST",
            payload={"session_id": session_id},
            timeout=args.timeout,
        )
        _add_check(report, "navigation_next", nav_next)

    qr_visible = _request_json(
        base_url,
        "/qr/visible",
        method="POST",
        payload={"qr_id": "hil-qr", "payload": "door"},
        timeout=args.timeout,
    )
    _add_check(report, "qr_visible", qr_visible)

    qr_active = _request_json(base_url, "/qr/active", timeout=args.timeout)
    _add_check(report, "qr_active", qr_active)

    qr_telemetry = _request_json(
        base_url,
        "/qr/telemetry",
        method="POST",
        payload={"qr_id": "hil-qr", "event": "seen", "metadata": {"confidence": 0.93}},
        timeout=args.timeout,
    )
    _add_check(report, "qr_telemetry", qr_telemetry)

    esp = _request_json(
        base_url,
        "/esp/process",
        method="POST",
        payload={"text": "hil status check", "wants_audio": True},
        timeout=args.timeout,
    )
    _add_check(report, "esp_process", esp)

    if isinstance(esp.get("body"), dict):
        tts_url = str(esp["body"].get("tts_url") or "")
        if tts_url:
            absolute_tts_url = tts_url if tts_url.startswith("http") else urljoin(base_url + "/", tts_url.lstrip("/"))
            tts = _request_binary(absolute_tts_url, timeout=max(8.0, args.timeout))
            _add_check(report, "esp_tts_fetch", tts)

    if session_id:
        nav_cancel = _request_json(
            base_url,
            "/navigation/cancel",
            method="POST",
            payload={"session_id": session_id},
            timeout=args.timeout,
        )
        _add_check(report, "navigation_cancel", nav_cancel)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    artifact_path = Path(args.artifact)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Live HIL Summary ===")
    for check in report["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        extra = f" ({check['error']})" if check["error"] else ""
        print(f"- {check['name']}: {status}{extra}")
    print(f"Report: {artifact_path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
