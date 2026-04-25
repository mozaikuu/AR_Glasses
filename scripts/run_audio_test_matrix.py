from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
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
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> dict[str, object]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

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


def _body_dict(result: dict[str, object]) -> dict[str, object]:
    body = result.get("body")
    return body if isinstance(body, dict) else {}


def _extract_metadata(body: dict[str, object]) -> dict[str, object]:
    metadata = body.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _short(value: str, limit: int = 160) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _resolve_ffmpeg_binary() -> str:
    env_ffmpeg = os.getenv("FFMPEG_BIN", "").strip()
    if env_ffmpeg:
        return env_ffmpeg

    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg

    try:
        import imageio_ffmpeg  # type: ignore

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe:
            return ffmpeg_exe
    except Exception:
        pass

    return ""


def _load_audio_as_wav_bytes(audio_path: Path, ffmpeg_bin: str) -> tuple[bytes, str]:
    suffix = audio_path.suffix.lower()
    if suffix == ".wav":
        return audio_path.read_bytes(), "wav"

    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg_not_available_for_non_wav_input")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        "-acodec",
        "pcm_s16le",
        str(tmp_path),
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "ffmpeg conversion failed").strip()
            raise RuntimeError(message)
        return tmp_path.read_bytes(), "converted_to_wav"
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def _looks_like_vision_intent(transcript: str) -> bool:
    lowered = transcript.lower()
    cues = [
        "can you read this",
        "read this",
        "what do you see",
        "what am i looking at",
        "what i am looking at",
        "what i'm looking at",
        "what is in front",
        "what is in front of me",
        "describe what you see",
        "describe what i am looking at",
        "describe what i'm looking at",
        "look at this",
        "identify this",
        "vision",
        "camera",
    ]
    return any(cue in lowered for cue in cues)


def _looks_like_error_text(text: str) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered:
        return True
    error_markers = (
        "request failed",
        "timed out",
        "traceback",
        "exception",
        " unavailable",
        "unavailable",
        "vision processing failed",
        "failed to",
        "could not",
        "error:",
    )
    return any(marker in lowered for marker in error_markers)


def _append_case(
    report: dict[str, object],
    *,
    name: str,
    system: str,
    ok: bool,
    status: int,
    evidence: dict[str, object],
    error: str = "",
) -> None:
    entry = {
        "name": name,
        "system": system,
        "ok": ok,
        "status": status,
        "evidence": evidence,
        "error": error,
    }
    cases = report.setdefault("cases", [])
    if isinstance(cases, list):
        cases.append(entry)
    if not ok:
        report["ok"] = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run four-audio matrix against the live gateway")
    parser.add_argument("--base-url", default=_default_base_url(), help="Gateway base URL")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--vision-timeout",
        type=float,
        default=75.0,
        help="Timeout in seconds for each vision /process attempt",
    )
    parser.add_argument("--audio-dir", default=str(REPO_ROOT / "Audio_Testing"))
    parser.add_argument("--unity-api-key", default=settings.unity_api_key.strip())
    parser.add_argument("--artifact", default=str(REPO_ROOT / "artifacts" / "audio_test_matrix_report.json"))
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    audio_dir = Path(args.audio_dir)

    report: dict[str, object] = {
        "ok": True,
        "base_url": base_url,
        "audio_dir": str(audio_dir),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cases": [],
        "conversion": {},
    }

    expected_files = {
        "fibbonaci": audio_dir / "Fibbonaci.m4a",
        "hey_computer": audio_dir / "Hey Computer.m4a",
        "ta_office": audio_dir / "Ta Office.m4a",
        "vision": audio_dir / "Vision.m4a",
    }

    missing_files = [str(path) for path in expected_files.values() if not path.exists()]
    if missing_files:
        report["ok"] = False
        report["error"] = "missing_audio_files"
        report["missing_files"] = missing_files
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Missing audio files:")
        for missing in missing_files:
            print(f"- {missing}")
        print(f"Report: {artifact_path}")
        return 1

    ffmpeg_bin = _resolve_ffmpeg_binary()
    report["ffmpeg_bin"] = ffmpeg_bin

    audio_b64: dict[str, str] = {}
    base_metadata = {
        "audio_format": "wav_pcm",
        "sample_rate": 16000,
        "sample_width": 2,
    }

    for key, path in expected_files.items():
        try:
            wav_bytes, conversion_kind = _load_audio_as_wav_bytes(path, ffmpeg_bin)
            audio_b64[key] = base64.b64encode(wav_bytes).decode("ascii")
            conversion = report.get("conversion")
            if isinstance(conversion, dict):
                conversion[key] = {
                    "input_path": str(path),
                    "input_bytes": path.stat().st_size,
                    "wav_bytes": len(wav_bytes),
                    "conversion": conversion_kind,
                }
        except Exception as exc:
            _append_case(
                report,
                name=f"prepare_{key}",
                system="audio_preprocessing",
                ok=False,
                status=0,
                evidence={"input_path": str(path)},
                error=str(exc),
            )

    if not report.get("ok"):
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Audio preparation failed; see report for details.")
        print(f"Report: {artifact_path}")
        return 1

    health = _request_json(base_url, "/", timeout=args.timeout)
    _append_case(
        report,
        name="gateway_health",
        system="gateway",
        ok=bool(health.get("ok")),
        status=int(health.get("status", 0) or 0),
        evidence={"body": _body_dict(health)},
        error=str(health.get("error") or ""),
    )

    if not health.get("ok"):
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Gateway unavailable; aborting matrix run.")
        print(f"Report: {artifact_path}")
        return 1

    companion_result = _request_json(
        base_url,
        "/process",
        method="POST",
        timeout=args.timeout,
        payload={
            "audio_base64": audio_b64["fibbonaci"],
            "mode": "quick",
            "client": "companion",
            "metadata": dict(base_metadata),
        },
    )
    companion_body = _body_dict(companion_result)
    companion_meta = _extract_metadata(companion_body)
    companion_transcript = str(companion_meta.get("transcript") or "").strip()
    companion_text = str(companion_body.get("text") or "").strip()
    companion_ok = bool(companion_result.get("ok")) and bool(companion_transcript) and bool(companion_text)
    _append_case(
        report,
        name="fibbonaci_companion",
        system="companion",
        ok=companion_ok,
        status=int(companion_result.get("status", 0) or 0),
        evidence={
            "transcript": _short(companion_transcript),
            "text": _short(companion_text),
            "tool_calls": companion_body.get("tool_calls", []),
        },
        error=str(companion_result.get("error") or ""),
    )

    wakeword_result = _request_json(
        base_url,
        "/process",
        method="POST",
        timeout=args.timeout,
        payload={
            "audio_base64": audio_b64["hey_computer"],
            "mode": "quick",
            "client": "esp32",
            "metadata": {**base_metadata, "always_listen": True},
        },
    )
    wakeword_body = _body_dict(wakeword_result)
    wakeword_meta = _extract_metadata(wakeword_body)
    wake_triggered = bool(wakeword_meta.get("wakeword_triggered"))
    wakeword_ok = bool(wakeword_result.get("ok")) and wake_triggered
    _append_case(
        report,
        name="hey_computer_wakeword",
        system="wakeword",
        ok=wakeword_ok,
        status=int(wakeword_result.get("status", 0) or 0),
        evidence={
            "wakeword_triggered": wake_triggered,
            "wakeword": str(wakeword_meta.get("wakeword") or ""),
            "response_text": _short(str(wakeword_body.get("text") or "")),
            "transcript": _short(str(wakeword_meta.get("transcript") or "")),
        },
        error=str(wakeword_result.get("error") or ""),
    )

    nav_process_result = _request_json(
        base_url,
        "/process",
        method="POST",
        timeout=args.timeout,
        payload={
            "audio_base64": audio_b64["ta_office"],
            "mode": "quick",
            "client": "esp32",
            "metadata": dict(base_metadata),
        },
    )
    nav_process_body = _body_dict(nav_process_result)
    nav_process_meta = _extract_metadata(nav_process_body)
    nav_transcript = str(nav_process_meta.get("transcript") or "").strip()

    unity_headers: dict[str, str] = {}
    if args.unity_api_key.strip():
        unity_headers["X-Unity-Api-Key"] = args.unity_api_key.strip()

    unity_route_result: dict[str, object]
    nav_start_result: dict[str, object]
    nav_destination = ""

    if nav_transcript:
        unity_route_result = _request_json(
            base_url,
            "/unity/voice-command",
            method="POST",
            timeout=args.timeout,
            headers=unity_headers,
            payload={
                "command": nav_transcript,
                "mode": "quick",
                "client": "unity_quest",
            },
        )
        unity_route_body = _body_dict(unity_route_result)
        nav_destination = str(unity_route_body.get("destination") or "").strip()
        if bool(unity_route_result.get("ok")) and str(unity_route_body.get("action") or "") == "navigate" and nav_destination:
            nav_start_result = _request_json(
                base_url,
                "/navigation/start",
                method="POST",
                timeout=args.timeout,
                payload={"destination": nav_destination, "start": "Entrance"},
            )
            nav_start_body = _body_dict(nav_start_result)
            session_id = str(nav_start_body.get("session_id") or "").strip()
            if session_id:
                _request_json(
                    base_url,
                    "/navigation/cancel",
                    method="POST",
                    timeout=args.timeout,
                    payload={"session_id": session_id},
                )
        else:
            nav_start_result = {
                "ok": False,
                "status": 0,
                "body": {},
                "error": "unity_route_did_not_return_navigate_destination",
            }
    else:
        unity_route_result = {
            "ok": False,
            "status": 0,
            "body": {},
            "error": "no_transcript_from_ta_office_audio",
        }
        nav_start_result = {
            "ok": False,
            "status": 0,
            "body": {},
            "error": "navigation_start_skipped_no_transcript",
        }

    unity_route_body = _body_dict(unity_route_result)
    nav_ok = (
        bool(nav_process_result.get("ok"))
        and bool(nav_transcript)
        and bool(unity_route_result.get("ok"))
        and str(unity_route_body.get("action") or "") == "navigate"
        and bool(nav_destination)
        and bool(nav_start_result.get("ok"))
    )
    _append_case(
        report,
        name="ta_office_navigation",
        system="navigation",
        ok=nav_ok,
        status=int(nav_start_result.get("status", 0) or int(unity_route_result.get("status", 0) or 0)),
        evidence={
            "transcript": _short(nav_transcript),
            "unity_action": str(unity_route_body.get("action") or ""),
            "unity_intent": str(unity_route_body.get("intent") or ""),
            "destination": nav_destination,
            "navigation_start_ok": bool(nav_start_result.get("ok")),
        },
        error="; ".join(
            part
            for part in [
                str(nav_process_result.get("error") or "").strip(),
                str(unity_route_result.get("error") or "").strip(),
                str(nav_start_result.get("error") or "").strip(),
            ]
            if part
        ),
    )

    vision_clients = ["esp32", "unity_quest", "mobile_browser", "pc_browser", "companion"]
    vision_case_ok = True
    for client_name in vision_clients:
        max_attempts = 3
        attempt_delay_seconds = 1.0
        attempts_used = 0
        vision_result: dict[str, object] = {}
        vision_body: dict[str, object] = {}
        vision_meta: dict[str, object] = {}
        vision_transcript = ""
        vision_text = ""
        tool_calls: list[object] = []
        has_vision_tool = False
        transcript_looks_vision = False
        stt_failed = False

        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            vision_result = _request_json(
                base_url,
                "/process",
                method="POST",
                timeout=max(args.vision_timeout, args.timeout),
                payload={
                    "audio_base64": audio_b64["vision"],
                    "mode": "quick",
                    "client": client_name,
                    "metadata": dict(base_metadata),
                },
            )
            vision_body = _body_dict(vision_result)
            vision_meta = _extract_metadata(vision_body)
            vision_transcript = str(vision_meta.get("transcript") or "").strip()
            vision_text = str(vision_body.get("text") or "").strip()
            tool_calls_raw = vision_body.get("tool_calls", [])
            tool_calls = tool_calls_raw if isinstance(tool_calls_raw, list) else []
            has_vision_tool = any(str(item).startswith("vision.") for item in tool_calls)
            transcript_looks_vision = _looks_like_vision_intent(vision_transcript)
            stt_failed = "could not transcribe" in vision_text.lower()
            has_usable_vision_response = (
                bool(vision_text)
                and transcript_looks_vision
                and not stt_failed
                and not _looks_like_error_text(vision_text)
            )

            if has_vision_tool or has_usable_vision_response:
                break
            if attempt < max_attempts:
                time.sleep(attempt_delay_seconds)

        case_ok = bool(vision_result.get("ok")) and (has_vision_tool or has_usable_vision_response)
        vision_case_ok = vision_case_ok and case_ok
        _append_case(
            report,
            name=f"vision_{client_name}",
            system="vision",
            ok=case_ok,
            status=int(vision_result.get("status", 0) or 0),
            evidence={
                "client": client_name,
                "transcript": _short(vision_transcript),
                "tool_calls": tool_calls,
                "text": _short(vision_text),
                "transcript_looks_vision": transcript_looks_vision,
                "has_vision_tool": has_vision_tool,
                "has_usable_vision_response": has_usable_vision_response,
                "attempts_used": attempts_used,
            },
            error=str(vision_result.get("error") or ""),
        )

    _append_case(
        report,
        name="vision_all_devices",
        system="vision",
        ok=vision_case_ok,
        status=200 if vision_case_ok else 0,
        evidence={"clients": vision_clients},
        error="",
    )

    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    artifact_path = Path(args.artifact)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Audio Matrix Summary ===")
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        status = "PASS" if bool(case.get("ok")) else "FAIL"
        print(f"- {case.get('name')}: {status}")
    print(f"Report: {artifact_path}")

    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
