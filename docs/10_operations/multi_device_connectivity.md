# Multi-Device Connectivity Guide

This guide configures one PC as the backend host and connects Unity (Quest/Android), browser, and mobile clients.

## 1) Local LAN Mode (recommended first)

1. Start backend on the PC:
   - `uv run python start.py --profile production-local --host 0.0.0.0 --port 8000`
2. Print LAN URLs:
   - `uv run python -m scripts.print_network_info`
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

## 7) Device-By-Device Quick Steps

### Browser (same LAN)

1. Open `http://<PC_LAN_IP>:8000/`.
2. Open `http://<PC_LAN_IP>:8000/network/info`.
3. If Streamlit UI is used, open `http://<PC_LAN_IP>:8501`.

### Android phone

1. Connect phone and PC to same Wi-Fi.
2. Set app backend URL to `http://<PC_LAN_IP>:8000`.
3. If `UNITY_API_KEY` is configured, send header `X-Unity-Api-Key`.
4. Test voice command routing with destination `Stairs_G`.

### Meta Quest (Unity app)

1. Connect Quest and PC to same Wi-Fi/subnet.
2. Set runtime API URL once in Unity app:
   - `ApiEndpointResolver.SetOverride("http://<PC_LAN_IP>:8000")`
3. Optional API key override:
   - `ApiEndpointResolver.SetApiKeyOverride("<key>")`
4. Speak: "take me to stairs g" and verify navigation starts.

### Internet (free tunnel)

1. Start backend locally on the PC.
2. Start free tunnel to `http://127.0.0.1:8000`.
3. Update device base URL to tunnel URL.
4. Repeat same command tests from external network.
