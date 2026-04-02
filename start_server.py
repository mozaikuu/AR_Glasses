#!/usr/bin/env python3
"""Compatibility launcher for legacy start_server.py usage.

Deprecated: prefer running start.py directly.
"""

import sys

from start import main


if __name__ == "__main__":
    print("[DEPRECATED] start_server.py now delegates to start.py.")
    if "--profile" not in sys.argv:
        sys.argv.extend(["--profile", "production-local"])
    if "--reload" not in sys.argv:
        sys.argv.append("--reload")
    main()
