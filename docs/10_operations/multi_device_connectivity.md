# Multi-Device Connectivity Guide

This guide configures one PC as the backend host and connects Unity (Quest/Android), browser, and mobile clients.

## 1) Local LAN Mode (recommended first)

1. Start backend on the PC:
   - `uv run python start.py --profile production-local --host 0.0.0.0 --port 8000`
2. Print LAN URLs:
   - `uv run python scripts/print_network_info.py`
3. Make sure firewall allows TCP 8000.
4. On each client, use:
   - `http://<PC_LAN_IP>:8000`

Health checks:

- `GET /`
- `GET /debug`
- `GET /network/info`

## 2) Unity Endpoint Configuration

Unity navigation scripts now resolve API base URL in this order:

1. `PlayerPrefs["SmartGlasses.ApiBaseUrl"]`
2. `SMART_GLASSES_API_BASE_URL` environment variable (Editor/Desktop)
3. Script Inspector fallback (`serverBaseUrl`)

Set override once in Unity runtime code:

- `ApiEndpointResolver.SetOverride("http://192.168.1.23:8000")`

Clear it:

- `ApiEndpointResolver.ClearOverride()`

Files:

- [AR-campus-nav/Assets/Scripts/Navigation/ApiEndpointResolver.cs](AR-campus-nav/Assets/Scripts/Navigation/ApiEndpointResolver.cs)
- [AR-campus-nav/Assets/Scripts/Navigation/VoiceNavigationController.cs](AR-campus-nav/Assets/Scripts/Navigation/VoiceNavigationController.cs)
- [AR-campus-nav/Assets/Scripts/Navigation/NavigationManager.cs](AR-campus-nav/Assets/Scripts/Navigation/NavigationManager.cs)

## 3) Internet Mode (free)

Use a free tunnel on the PC that forwards to `http://127.0.0.1:8000`.

Recommended free options:

1. Cloudflare Tunnel quick tunnel
2. Tailscale Funnel (private mesh + optional public)
3. ngrok free (URL/session limitations)

When tunnel is active, set `PUBLIC_BASE_URL` in local settings and use that URL on remote clients.

## 4) Optional Unity API Key Protection

If exposing Unity control endpoints over internet, set `UNITY_API_KEY`.
Then Unity must send header:

- `X-Unity-Api-Key: <value>`

Protected endpoints:

- `POST /unity/voice-command`
- `POST /navigate`

## 5) Another Machine Setup

On new PC:

1. Install Python 3.11+ and uv.
2. Clone repository.
3. Run:
   - `powershell -ExecutionPolicy Bypass -File scripts/setup_machine.ps1 -OpenFirewall`
4. Start backend:
   - `uv run python start.py --profile production-local --host 0.0.0.0 --port 8000`

## 6) Cross-Device Test Matrix

1. Browser

- Open `http://<gateway>/` and verify health response.

2. Android phone and Meta Quest

- Ensure same LAN first.
- Use Unity API base URL `http://<PC_LAN_IP>:8000`.
- Speak: "take me to Stairs_G".
- Verify server route action is `navigate` and Unity starts movement.

3. Internet test

- Switch base URL to tunnel URL and repeat same command.
