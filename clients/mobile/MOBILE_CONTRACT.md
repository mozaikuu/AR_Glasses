# CEREBRO Mobile API Contract

All requests use JSON. The optional header `X-API-Key` is supported for authenticated deployments.

## POST /process

Multimodal input (voice, image, text) to the backend assistant.

### Request

```json
{
	"text": "optional prompt",
	"audio_base64": "...",
	"image_base64": "...",
	"metadata": {}
}
```

### Response

```json
{
	"text": "assistant response",
	"metadata": {
		"tts_url": "https://..."
	}
}
```

## Navigation Endpoints

### GET /navigation/destinations

Response:

```json
{
	"destinations": [
		{
			"id": "building-a-201",
			"name": "Building A - Room 201",
			"description": "Second floor"
		}
	]
}
```

### POST /navigation/start

Request:

```json
{
	"destination": "Building A - Room 201"
}
```

Response:

```json
{
	"session_id": "abc123",
	"destination": "Building A - Room 201",
	"total_steps": 8,
	"next_instruction": "Walk straight 10 meters"
}
```

### GET /navigation/status?session_id=abc123

Response:

```json
{
	"session_id": "abc123",
	"destination": "Building A - Room 201",
	"current_step": 3,
	"total_steps": 8,
	"next_instruction": "Turn left at the stairs",
	"is_complete": false
}
```

### POST /navigation/next

Request:

```json
{ "session_id": "abc123" }
```

### POST /navigation/stop

Request:

```json
{ "session_id": "abc123" }
```
