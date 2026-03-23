# Data and State Model

## Request Models

- `TextRequest` (`models/requests.py`)
- `MultimodalRequest`:
  - `text`
  - `image` (base64)
  - `audio` (base64)
  - `audio_dtype`
  - `mode`

## In-Memory Runtime State

- MCP connection state in gateway module globals
- Web UI transient flags/state map
- Navigation sessions (`tools/navigation/nav_runner.py`)
- QR active markers and telemetry buffers

## Data Files

- Navigation graph: `tools/navigation/navigationGraph.json` (via loader in navigation module)
- Model assets under `models/` (vision, whisper, piper)

## Persistence Characteristics

- Most state is process-local and non-persistent.
- Restarting backend clears active sessions and transient flags.
- Not horizontally scalable without external state store.

## Data Risks

- No robust persistent session store for multi-user routing.
- No centralized event/telemetry schema across all clients.
- Potential drift between Unity scene destinations and server graph locations.

