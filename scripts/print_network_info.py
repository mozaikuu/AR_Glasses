from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config.settings import settings


def _lan_ips() -> list[str]:
    ips: list[str] = []
    names = {"localhost", socket.gethostname()}
    for name in names:
        try:
            _, _, found = socket.gethostbyname_ex(name)
        except Exception:
            continue
        for ip in found:
            if ip.startswith("127."):
                continue
            if ip not in ips:
                ips.append(ip)
    return ips


def main() -> None:
    print("Smart Glasses Network Info")
    print("-" * 30)
    print(f"Gateway bind: {settings.api_host}:{settings.api_port}")
    print(f"MCP bind: {settings.mcp_host}:{settings.mcp_port}")

    lan_ips = _lan_ips()
    if lan_ips:
        print("LAN URLs:")
        for ip in lan_ips:
            print(f"  http://{ip}:{settings.api_port}")
    else:
        print("LAN URLs: none detected")

    if settings.public_base_url.strip():
        print(f"Public URL: {settings.public_base_url.strip()}")

    probe_url = f"http://127.0.0.1:{settings.api_port}/network/info"
    try:
        with urlopen(probe_url, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        print("Gateway network endpoint:")
        print(json.dumps(payload, indent=2))
    except Exception as exc:
        print(f"Gateway network endpoint unavailable at {probe_url}: {exc}")


if __name__ == "__main__":
    main()
