#!/usr/bin/env python3
"""Compatibility launcher for legacy start_server.py usage.

Deprecated: prefer running start.py directly.
"""

import os
import socket

from config.settings import API_PORT
from start import main


def get_local_ip() -> str:
    """Get a best-effort local LAN IP for convenience output."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


if __name__ == "__main__":
    local_ip = get_local_ip()
    os.environ["SERVER_IP"] = local_ip

    print("[DEPRECATED] start_server.py now delegates to start.py.")
    print(f"Gateway URL: http://{local_ip}:{API_PORT}")
    print(f"Health URL:  http://{local_ip}:{API_PORT}/health")
    main()
