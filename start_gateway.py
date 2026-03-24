"""Compatibility launcher for the unified startup path.

Deprecated: prefer running start.py directly.
"""

import sys

from start import main


if __name__ == "__main__":
    print("[DEPRECATED] start_gateway.py now delegates to start.py.")
    if "--reload" not in sys.argv:
        sys.argv.append("--reload")
    main()

