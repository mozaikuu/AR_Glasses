from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib.util import find_spec
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


@dataclass
class TestStep:
    name: str
    command: list[str] | None
    cwd: Path
    skip_reason: str = ""


def run_step(name: str, command: list[str], cwd: Path) -> tuple[bool, str, float]:
    # Each step is timed and captured to produce a concise final report.
    started = perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    duration = perf_counter() - started
    output = (result.stdout + "\n" + result.stderr).strip()
    return (result.returncode == 0), output, duration


def resolve_platformio_command() -> tuple[list[str] | None, str]:
    cli_path = shutil.which("platformio") or shutil.which("pio")
    if cli_path:
        return [cli_path], ""

    # If PATH does not expose platformio, use the package in the active interpreter.
    if find_spec("platformio") is not None:
        return [sys.executable, "-m", "platformio"], ""

    return None, "PlatformIO CLI not found (install `platformio` or `pio`)"


def resolve_unity_executable() -> tuple[str, str]:
    unity_executable = os.environ.get("UNITY_EXECUTABLE", "").strip()
    if unity_executable:
        if Path(unity_executable).exists():
            return unity_executable, ""
        return "", f"UNITY_EXECUTABLE not found at {unity_executable}"

    # Auto-detect common Unity Hub install locations on Windows.
    candidate_roots = [
        Path("G:/Unity Hub/Editor"),
        Path("C:/Program Files/Unity/Hub/Editor"),
        Path("C:/Unity/Hub/Editor"),
    ]
    discovered: list[Path] = []
    for root in candidate_roots:
        if root.exists():
            discovered.extend(root.glob("*/Editor/Unity.exe"))

    if discovered:
        # Prefer lexicographically latest version directory.
        unity_path = str(sorted(discovered, reverse=True)[0])
        return unity_path, ""

    return "", "UNITY_EXECUTABLE is not set"


def build_steps(repo_root: Path, artifacts_dir: Path) -> list[TestStep]:
    steps: list[TestStep] = [
        TestStep(
            name="python_unit_tests",
            command=[sys.executable, "-m", "pytest", "-m", "not integration"],
            cwd=repo_root,
        )
    ]

    steps.append(
        TestStep(
            name="system_integration_tests",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "-m",
                "integration",
                "tests/test_system_integration_smoke.py",
            ],
            cwd=repo_root,
        )
    )

    firmware_dir = repo_root / "Firmware"
    firmware_ini = firmware_dir / "platformio.ini"
    platformio_cmd, platformio_skip_reason = resolve_platformio_command()

    if not firmware_ini.exists():
        steps.append(
            TestStep(
                name="firmware_native_tests",
                command=None,
                cwd=repo_root,
                skip_reason="Firmware/platformio.ini not found",
            )
        )
    elif not platformio_cmd:
        steps.append(
            TestStep(
                name="firmware_native_tests",
                command=None,
                cwd=repo_root,
                skip_reason=platformio_skip_reason,
            )
        )
    else:
        steps.append(
            TestStep(
                name="firmware_native_tests",
                command=platformio_cmd + ["test", "-d", str(firmware_dir), "-e", "native"],
                cwd=repo_root,
            )
        )

    unity_project = repo_root / "AR-campus-nav"
    unity_executable, unity_resolution_error = resolve_unity_executable()
    unity_results = artifacts_dir / "unity-editmode-results.xml"
    unity_log = artifacts_dir / "unity-editmode.log"

    if not unity_project.exists():
        steps.append(
            TestStep(
                name="unity_editmode_tests",
                command=None,
                cwd=repo_root,
                skip_reason="AR-campus-nav project folder not found",
            )
        )
    elif not unity_executable:
        steps.append(
            TestStep(
                name="unity_editmode_tests",
                command=None,
                cwd=repo_root,
                skip_reason=unity_resolution_error,
            )
        )
    else:
        steps.append(
            TestStep(
                name="unity_editmode_tests",
                command=[
                    unity_executable,
                    "-batchmode",
                    "-nographics",
                    "-projectPath",
                    str(unity_project),
                    "-runTests",
                    "-testPlatform",
                    "EditMode",
                    "-testResults",
                    str(unity_results),
                    "-logFile",
                    str(unity_log),
                    "-quit",
                ],
                cwd=repo_root,
            )
        )

    return steps


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_dir = repo_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    steps = build_steps(repo_root, artifacts_dir)

    report: dict[str, object] = {"ok": True, "steps": []}

    for step in steps:
        if step.command is None:
            report["steps"].append(
                {
                    "name": step.name,
                    "ok": True,
                    "skipped": True,
                    "skip_reason": step.skip_reason,
                    "duration_seconds": 0.0,
                    "output": "",
                }
            )
            continue

        ok, output, duration = run_step(step.name, step.command, step.cwd)
        if not ok:
            report["ok"] = False
        report["steps"].append(
            {
                "name": step.name,
                "ok": ok,
                "skipped": False,
                "duration_seconds": round(duration, 3),
                "output": output,
            }
        )

    report_path = artifacts_dir / "test_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Test Summary ===")
    for step in report["steps"]:
        if step.get("skipped"):
            print(f"- {step['name']}: SKIP ({step['skip_reason']})")
            continue
        status = "PASS" if step["ok"] else "FAIL"
        print(f"- {step['name']}: {status} ({step['duration_seconds']}s)")

    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
