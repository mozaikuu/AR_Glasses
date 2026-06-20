# Supplementary engineering discussion

### Supplementary topic: reproducible ML ops for student projects

Pin Python dependencies, record `pip freeze` or lockfiles for demos, and snapshot model weights used during evaluation. Small teams benefit more from repeatable `pytest` gates than from exotic MLOps platforms.


### Supplementary topic: containerization vs bare-metal in lab gateways

Containers improve parity across laptops but add USB/audio forwarding pain. Bare-metal venvs are simpler for microphone access during voice demos. Choose based on demo machine constraints.


### Supplementary topic: rate limiting and backoff on free-tier STT

Free tiers throttle concurrent streams; exponential backoff prevents thundering herds when multiple phones reconnect. Surface user-visible “try again” states instead of silent hangs.


### Supplementary topic: structured logging with correlation ids

Assign each request a correlation id propagated to STT, LLM, and TTS subcalls to debug tail latency. JSON logs parse better than ad-hoc print statements during overnight soak tests.


### Supplementary topic: feature flags and staged rollouts

Gate experimental tools (MCP, vision) behind settings so advisors can run stable mode. Flags belong in `settings` with defaults documented for reproducibility.


### Supplementary topic: contract testing between Expo and FastAPI

Consumer-driven contract tests catch renamed JSON fields before mobile release. Even a handful of golden-file fixtures beats manual tapping before demos.


### Supplementary topic: protobuf vs JSON for embedded (thesis discussion only)

Protobuf saves bandwidth on paper, but embedded HTTP stacks and human debuggability often favor JSON for coursework. Document the tradeoff; pick JSON unless bandwidth is measured as a bottleneck.


### Supplementary topic: WebSockets vs polling for session updates

WebSockets reduce latency for push updates but complicate load balancers and reconnect logic. Polling is crude yet easy to reason about in student timelines.


### Supplementary topic: offline-first caches on mobile clients

Cache last successful navigation graph and TTS clips for corridor dead zones. Invalidate caches when `navigation.json` version bumps.


### Supplementary topic: accessibility (screen reader + voice)

Screen reader users need semantic labels on buttons that trigger recording. Voice-only flows should expose repeatable prompts and cancel words.


### Supplementary topic: internationalization of navigation strings

Separate translatable resource bundles from route ids. RTL layouts and concatenated English strings do not mix.


### Supplementary topic: localization of date/time answers

LLMs may hallucinate time zones; anchor schedule answers to server clock and explicit campus timezone configuration.


### Supplementary topic: static analysis (ruff/mypy) adoption

Ruff catches unused imports and risky patterns quickly; mypy catches pydantic model drift. Both reduce demo-week surprises.


### Supplementary topic: security scanners in CI

Dependency scanners flag CVEs in transitive packages. Treat alerts as triage items, not automatic upgrades, to avoid breaking pins.


### Supplementary topic: secrets scanning (gitleaks)

Prevent accidental commits of `.env` API keys. Rotate keys immediately if leaks occur, even on private repos.


### Supplementary topic: dependency pinning and SBOM

Graduation reviewers appreciate pinned requirements and a short SBOM table listing major libraries and versions used at submission time.


### Supplementary topic: disaster recovery for demo laptops

Keep a USB stick with venv instructions, model cache notes, and offline TTS assets. Assume conference Wi-Fi will fail.


### Supplementary topic: battery profiling on Android clients

Continuous microphone and camera preview drain batteries fast. Measure mAh impact when claiming “all-day” use.


### Supplementary topic: thermal throttling on ESP32 when Wi-Fi active

Wi-Fi transmit bursts heat the module; audio + Wi-Fi concurrently can trigger brownouts if power supply traces are thin.


### Supplementary topic: memory fragmentation on long-running Python

Long-running demo servers may grow RSS due to caches; cap cache sizes (as with TTS TTL) and restart between multi-hour events.


### Supplementary topic: garbage collection pauses and ASR tail latency

GC pauses hit tail latency for streaming audio pipelines. Preallocate buffers where possible and avoid huge allocations per request.


### Supplementary topic: campus IT firewall rules for LAN demos

Some universities block device-to-device Wi-Fi. Pre-approve MAC addresses or use a dedicated router segment for demos.


### Supplementary topic: TLS termination strategies

Terminate TLS at nginx for public demos while keeping plain HTTP inside the lab VLAN if appropriate—document threat model assumptions.


### Supplementary topic: reverse proxy with nginx for public demos

Reverse proxies add rate limits, gzip, and request logging. They also become a single point of failure unless health-checked.


### Supplementary topic: load testing with k6 (future work)

k6 scripts can hammer `/process` with canned JSON to find saturation points. Pair with CPU profiling to locate Python hotspots.
