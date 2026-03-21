# AI System

## Inference Strategy

- Preferred: Cerebras API inference (cloud)
- Fallback: local processing paths (speech/vision tooling and local model routes)
- No strict offline requirement, but fallback exists for resilience

## Core AI Pipeline

1. Input normalization in `server/gateway.py`
2. Audio transcription via `tools/speech/transcription.py`
3. Decision loop via `agent/agent_loop.py`
4. Tool execution through MCP (`server/server.py`)
5. Final response post-processing and delivery

## Tools Used by Agent

- Vision: Moondream (preferred), YOLO (fallback)
- Search: web retrieval tool
- Navigation: indoor graph/path tools and session manager

## Training vs Inference Separation

- Training artifacts/scripts are not in active production path.
- Runtime loads pre-trained models and performs inference only.
- Core runtime does not retrain models during request handling.

## Model Limitations

- Cloud dependency introduces latency and outage sensitivity.
- Whisper fallback is slower and less accurate on weak/noisy audio.
- Vision accuracy depends on camera quality, framing, and lighting.
- Tool-loop bounded iterations may stop before full completion in complex tasks.

## AI Risks

- Prompt assembly can include noisy transcriptions.
- Tool and direct LLM paths can diverge in answer style/consistency.
- Missing centralized telemetry for per-step quality monitoring.

