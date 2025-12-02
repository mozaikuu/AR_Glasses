# Zeroconf mDNS advertisement so other devices discover the service on Wi-Fi
from zeroconf import ServiceInfo, Zeroconf
import socket

def start_wifi_broadcast(name="SmartGlasses_MCP", port=8765):
    # Get local IP in an IPv4-friendly way
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need reachable endpoint, just to pick a local interface
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    info = ServiceInfo(
        "_mcp._tcp.local.",
        f"{name}._mcp._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties={"name": name}
    )

    z = Zeroconf()
    z.register_service(info)
    print(f"[WiFi] Broadcasting {name} at {local_ip}:{port}")
    return z, local_ip
