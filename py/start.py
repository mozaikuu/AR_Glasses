#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    root_start = Path(__file__).resolve().parents[1] / "start.py"
    spec = importlib.util.spec_from_file_location("root_start", root_start)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load root start.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
