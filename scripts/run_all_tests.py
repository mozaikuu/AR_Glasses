from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter


def run_step(name: str, command: list[str], cwd: Path) -> tuple[bool, str, float]:
    # Each step is timed and captured to produce a concise final report.
    started = perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    duration = perf_counter() - started
    output = (result.stdout + "\n" + result.stderr).strip()
    return (result.returncode == 0), output, duration


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    steps = [
        (
            "unit_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        ),
        (
            "gateway_smoke",
            [
                sys.executable,
                "-c",
                (
                    "from fastapi.testclient import TestClient; "
                    "from app.api.gateway import app; "
                    "c=TestClient(app); "
                    "assert c.get('/').status_code == 200; "
                    "assert c.post('/unity/voice-command', json={'command':'take me to ta office','mode':'quick'}).status_code == 200; "
                    "assert c.get('/navigation/locations').status_code == 200; "
                    "print('gateway smoke ok')"
                ),
            ],
        ),
    ]

    report: dict[str, object] = {"ok": True, "steps": []}

    for name, command in steps:
        ok, output, duration = run_step(name, command, repo_root)
        if not ok:
            report["ok"] = False
        report["steps"].append(
            {
                "name": name,
                "ok": ok,
                "duration_seconds": round(duration, 3),
                "output": output,
            }
        )

    artifacts_dir = repo_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "test_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Test Summary ===")
    for step in report["steps"]:
        status = "PASS" if step["ok"] else "FAIL"
        print(f"- {step['name']}: {status} ({step['duration_seconds']}s)")

    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
