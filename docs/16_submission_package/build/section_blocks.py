"""
Unique subsection bodies for generate_expanded_docs.py (no recycled boilerplate).
"""
from __future__ import annotations


def _default(title: str) -> str:
    return (
        "This note ties the heading to Smart Glasses Distilled as implemented: a FastAPI gateway "
        "(`app/api/gateway.py`), typed request models, navigation session routes, assistant `/process`, "
        "and pytest coverage under `tests/`. It is an engineering framing for the graduation report, "
        "not a substitute for peer-reviewed citations where your advisor requires them.\n\n"
        "Replace or extend with concrete references from `15_references.md` and your literature matrix "
        "before final binding."
    )


# Title string must match callers in generate_expanded_docs.py exactly.
SECTION_BLOCKS: dict[str, str] = {}

# --- 2.1 Indoor localization & maps ---
SECTION_BLOCKS["2.1.1 Wi-Fi fingerprinting and RSSI maps"] = """\
Wi-Fi fingerprinting records spatial patterns of received signal strength (RSSI) from visible access points and matches live scans to a stored radio map. It is attractive on campuses because infrastructure already exists and client APIs are widely available.

Accuracy is sensitive to device heterogeneity, AP power changes, crowd absorption, and multipath in long corridors. Student deployments should budget time for calibration walks, versioning of radio maps, and clear degradation behavior when similarity scores are ambiguous.

For this project, indoor positioning is not claimed as a novel Wi-Fi contribution; instead, navigation steps are served by the gateway from structured data (`navigation.json` / client assets), while connectivity remains a transport concern for STT/TTS and HTTP APIs."""

SECTION_BLOCKS["2.1.2 BLE beacons and proximity graphs"] = """\
BLE beacons advertise identifiers at low duty cycle, enabling proximity zones and coarse graph nodes (“near the lab door”) rather than continuous metric coordinates. Beacon systems trade installation effort (battery swaps, mounting policy) against reliability.

Interference from human bodies, scheduling jitter on scanners, and inconsistent scan APIs across Android vendors affect repeatability. Engineering practice often combines BLE regions with Wi-Fi or inertial hints.

Smart Glasses Distilled can consume BLE-derived context if exposed to the gateway as metadata, but the repository’s primary navigation story is session-based instructions aligned with authored floor content."""

SECTION_BLOCKS["2.1.3 Ultra-wideband and time-of-flight ranging"] = """\
UWB time-of-flight can yield decimeter-level ranges between anchors and tags in favorable geometry. It addresses some multipath pitfalls of narrowband RSSI, but requires dedicated silicon and anchor deployment budgets uncommon in coursework unless sponsored.

NLOS (non-line-of-sight) paths, metal studs, and multipath still produce outliers; robust fusion filters and outlier rejection are part of real products.

The graduation codebase does not implement a UWB stack; UWB appears here only as related work context when comparing precision localization research to gateway-mediated campus assistance."""

SECTION_BLOCKS["2.1.4 Pedestrian dead reckoning with IMU"] = """\
Pedestrian dead reckoning integrates accelerometer and gyroscope signals to propagate step counts and heading changes from a last-known anchor. Short windows work well; drift accumulates without absolute fixes.

Phone and wearable IMU pipelines differ in sampling stability and mounting; backpack versus handheld versus glasses mount changes step detection thresholds.

Client-side PDR could complement server-delivered navigation in future work, but the current navigation service issues discrete steps from authored graphs rather than fusing continuous IMU tracks."""

SECTION_BLOCKS["2.1.5 Visual odometry and visual-inertial odometry"] = """\
Visual odometry tracks camera motion from frame-to-frame feature correspondences; VIO fuses IMU predictions with visual updates for smoother trajectories under motion blur or low texture.

Indoor repetition (blank walls, fluorescent flicker) challenges feature stability; compute and thermal budgets matter on phones and embedded boards.

The project’s vision path supports contextual Q&A (Moondream/MCP) rather than claiming a full VIO localization pipeline; AR clients remain consumers of gateway responses and authored spatial assets."""

SECTION_BLOCKS["2.1.6 SLAM in indoor environments"] = """\
SLAM jointly estimates a sensor trajectory and a map representation (often occupancy grids or sparse landmarks). Indoor SLAM must handle glass, dynamic pedestrians, and symmetric corridors where loop closure is ambiguous.

Operational SLAM stacks require calibration, map maintenance, and failure recovery UX when tracking is lost.

Repository scope includes mesh/floorplan processing helpers for authoring navigation assets, not a production SLAM front-end running on-device during every walk."""

SECTION_BLOCKS["2.1.7 Topological maps versus metric maps"] = """\
Topological maps represent places and adjacency (“A–B corridor connects to stairwell S”) and align with human turn-by-turn instructions. Metric maps add coordinates for AR overlays and precise distance estimates.

Many campus assistants only need topology plus a handful of metric anchors for rendering.

The gateway’s navigation sessions are naturally topological step lists enriched with optional coordinate text when metadata exists—matching how mobile clients prompt users without requiring centimeter fixes."""

SECTION_BLOCKS["2.1.8 Graph search and A* on floor meshes"] = """\
Floor meshes or extracted polylines can be discretized into graphs for shortest-path planning. A* remains the default teaching example when an admissible heuristic exists (e.g., Euclidean lower bound in open spaces).

Stairwells, one-way doors, and elevators require edge constraints and multi-floor supergraphs.

The Expo client contains MVP graph/route utilities; the backend navigation service remains deliberately simple for reproducible demos, with room to plug richer planners later."""

SECTION_BLOCKS["2.1.9 Multi-floor routing and elevator modeling"] = """\
Vertical circulation breaks 2D assumptions: elevators, stairs, and accessibility ramps need typed edges with wait-time distributions or at least static penalties.

Elevator banks also introduce statefulness (which car arrives), usually ignored in student prototypes.

Future extensions could model floors explicitly in `navigation.json`; current sessions illustrate the API contract with template-like multi-step routes."""

SECTION_BLOCKS["2.1.10 Campus-scale GIS integration"] = """\
Outdoor GIS layers (roads, footpaths) integrate cleanly with GPS, while indoor footprints often live in CAD/BIM or vendor-specific indoor GIS products.

Bridging indoor and outdoor graphs at building entrances is a classic integration seam.

The project’s demonstrator focuses on HTTP services and authored indoor assets; campus GIS could supply authoritative building footprints as upstream data sources."""

SECTION_BLOCKS["2.1.11 Accessibility and inclusive routing"] = """\
Inclusive routing prefers ramps and elevators, avoids stairs when a user requires step-free paths, and may widen corridors for turning radius in wheelchairs.

Policy data must be trustworthy; mislabeling an elevator as “out of service” has higher stakes than a generic detour.

Any production deployment should validate accessibility edges with facilities management; the current codebase exposes navigation text hooks where such policies would be enforced."""

SECTION_BLOCKS["2.1.12 Commercial indoor navigation SDKs"] = """\
Commercial SDKs bundle mapping tools, anchor management, analytics, and SLAs. They accelerate time-to-market but create licensing, data residency, and customization constraints.

SDK black boxes complicate academic evaluation when raw likelihoods or maps cannot be exported.

Smart Glasses Distilled prioritizes open, testable HTTP contracts so thesis artifacts remain inspectable without a proprietary indoor engine dependency."""

SECTION_BLOCKS["2.1.13 OpenStreetMap indoor and Simple Indoor Tagging"] = """\
OpenStreetMap indoor extensions and Simple Indoor Tagging (SIT) encourage community-editable floor polygons, doorways, and routing graphs. They democratize basemaps but require governance to prevent stale indoor geometry.

Quality varies by contributor skill and building access permissions.

Where OSM indoor data exists for a campus, it could seed `navigation.json` graphs; maintenance workflows remain an organizational problem beyond code."""

SECTION_BLOCKS["2.1.14 Digital twins for buildings"] = """\
Digital twins keep live or periodically refreshed models of HVAC, occupancy, and structural assets. Navigation can consume twin updates (e.g., blocked corridor) if fed into the routing graph.

Twins imply data pipelines, authentication, and schema alignment between BIM and runtime services.

This project does not operate a twin back end; the subsection situates future integration if a campus exposes standardized indoor change feeds."""

SECTION_BLOCKS["2.1.15 Simulation-to-reality transfer for navigation ML"] = """\
Learning navigation policies in simulation enables cheap data, but policies brittle to lighting, texture, and human density fail on real floors without domain randomization or fine-tuning.

Evaluation must separate “planner success in sim” from “task success with real users carrying phones at walking pace.”

The repository’s regression story is pytest on HTTP behavior rather than RL navigation training; sim-to-real remains future research adjacent to the implemented gateway."""

# --- 2.2 Voice / language stack ---
SECTION_BLOCKS["2.2.1 Cloud ASR latency budgets"] = """\
Cloud ASR adds network round trips and queueing variance on top of model compute. Interactive assistants need budgets for partial results, endpointing, and barge-in cancellation.

Campus Wi-Fi contention during events can dominate tail latency.

The gateway’s audio path should log timestamps per stage (upload, transcribe, LLM, TTS) when advisors request quantitative tables in Chapter 4."""

SECTION_BLOCKS["2.2.2 Streaming partial hypotheses and barge-in"] = """\
Streaming ASR emits partial transcripts that fluctuate before finalization; dialog managers must avoid acting prematurely while still feeling responsive.

Barge-in requires echo cancellation discipline and rapid cancellation of pending TTS playback.

`AssistantService` implements wake-follow windows and transcript normalization—document these behaviors when discussing streaming UX."""

SECTION_BLOCKS["2.2.3 Wake-word detection and false accepts"] = """\
Wake-word engines trade false accepts (accidental triggers) against false rejects (missed commands). Public demos suffer from background speech and TV audio.

Rollout policy belongs in configuration (`settings.wakeword_rollout_scope`) rather than hard-coded client forks.

Tests should include negative audio cases where no wake word appears to guard regressions."""

SECTION_BLOCKS["2.2.4 On-device keyword spotting"] = """\
Tiny keyword spotters run continuously at milliwatts, gating uplink to heavier cloud models. Vocabulary is limited compared to full LVCSR.

Hybrid designs keep privacy-sensitive always-listening stages local.

ESP-class peripherals in this project are better matched to button/wake flows unless a dedicated DSP front-end is added."""

SECTION_BLOCKS["2.2.5 LLM tool use and grounding"] = """\
Tool-augmented LLMs route user intents to APIs (navigation, vision, calendars). Reliability hinges on schema design, argument validation, and refusal when tools disagree.

Grounding reduces hallucinated campus facts by retrieving snippets (RAG) or executing structured queries.

Optional MCP integration in the repo illustrates the tool-call pattern without mandating a specific vendor model."""

SECTION_BLOCKS["2.2.6 Retrieval-augmented generation for campus FAQs"] = """\
RAG pairs a retriever (vector or keyword index) with a generator to cite local policies, exam rules, or building hours. Chunking and metadata filters dominate quality.

Stale embeddings misinform users; refresh pipelines matter.

For Smart Glasses Distilled, small curated JSON or markdown corpora may outperform large uncurated scrapes during demos."""

SECTION_BLOCKS["2.2.7 Multimodal models combining vision and language"] = """\
Vision-language models can answer “what is on this poster?” from a captured frame. Latency and privacy move to the forefront versus text-only chat.

Moondream or MCP vision tools in this codebase exemplify optional multimodal paths gated by heuristics and client capabilities.

Advisors often ask for explicit consent flows when cameras are involved."""

SECTION_BLOCKS["2.2.8 Safety alignment and refusal policies"] = """\
Assistants should refuse unsafe instructions (e.g., disabling lab safety interlocks) and avoid leaking secrets from prompts. Alignment techniques vary by provider.

Campus deployments still need institutional policy: the model is not the compliance officer.

Document which provider safety filters are enabled and known gaps for your defense Q&A."""

SECTION_BLOCKS["2.2.9 TTS quality versus latency (neural vs classical)"] = """\
Neural TTS sounds natural but costs GPU time or remote API fees; classical concatenative/parametric systems are cheaper but robotic.

Caching frequent phrases (“Turn left”) improves perceived speed.

The gateway implements in-memory TTS clip caching for repeated prompts during demos."""

SECTION_BLOCKS["2.2.10 Piper and lightweight on-gateway synthesis"] = """\
Piper and similar compact engines enable on-gateway speech without shipping audio back to a third party—useful for air-gapped labs.

Voice quality may be lower than cloud neural voices; acceptability depends on scenario.

ESP fetch endpoints (`/esp/tts/{filename}`) pair naturally with pre-synthesized or cached clips."""

SECTION_BLOCKS["2.2.11 Dialog state tracking for navigation sessions"] = """\
Navigation as a dialog requires explicit state: active session id, current step index, cancellation, and replanning after detours.

State machines are easier to test than implicit prompt-only memory.

`navigation_service` stores sessions in an in-memory dict—great for coursework, noted as a limitation for multi-instance deployments."""

SECTION_BLOCKS["2.2.12 Evaluation metrics: WER, SER, task success"] = """\
Word error rate measures transcription fidelity; semantic error rate or slot F1 measures intent extraction; task success measures end-to-end goal completion.

Navigation should log where users drop off (timeout vs wrong step).

Chapter 4 should report whichever metrics your pilot actually measured."""

SECTION_BLOCKS["2.2.13 Privacy of voice biometrics"] = """\
Voiceprints can identify or re-identify users; storage and comparison require consent and retention limits in many jurisdictions.

Even without explicit voiceprint features, raw audio is sensitive.

Project documentation should state retention defaults for logs and whether transcripts are persisted."""

SECTION_BLOCKS["2.2.14 Multilingual classrooms and code-switching"] = """\
Campus speech mixes languages mid-utterance; monolingual ASR models degrade. Language-id gating or multilingual models add cost.

Navigation prompts may need localized strings separate from LLM answers.

`metadata.yaml` and client i18n hooks are the right place to demonstrate awareness even if the demo stays English-first."""

SECTION_BLOCKS["2.2.15 Comparison to general assistants (Siri, Assistant, Alexa)"] = """\
Consumer assistants optimize for music, smart home, and web search—not authored indoor graphs tied to a lab gateway.

They also hide integration details behind opaque SDKs.

This work’s differentiation is inspectable HTTP routes, reproducible tests, and campus-specific navigation sessions under team control."""

# --- 2.3 Clients / wearables ---
SECTION_BLOCKS["2.3.1 Smart glasses form factors and optics"] = """\
Smart glasses vary from monocular HUDs to binocular AR with waveguides. Optics drive field of view, brightness outdoors, and comfort for long wear.

Battery and thermal limits cap continuous camera streaming.

In this repository, glasses-class experiences are treated as one client profile; the primary engineering artifact remains the gateway and service modules."""

SECTION_BLOCKS["2.3.2 AR headsets and scene understanding"] = """\
Headset SLAM and scene meshes unlock occlusion and anchoring, but require runtime permissions, calibration, and developer tooling.

Unity-based clients can visualize navigation cues aligned to spatial maps when assets exist.

`hololens2-campus-nav` / Unity clients in the wider workspace narrative consume gateway commands rather than replacing server-side orchestration."""

SECTION_BLOCKS["2.3.3 Companion phone apps as hybrid architecture"] = """\
Phones supply compute, radios, and batteries while wearables stay lightweight. The hybrid pattern is common when glasses stream sensors uplink.

Bluetooth/Wi-Fi handoff and background execution limits shape reliability.

Expo and React Native clients in `clients/` exemplify the companion role calling the same REST API surface."""

SECTION_BLOCKS["2.3.4 ESP32 as voice peripheral"] = """\
ESP32 boards can capture audio, show minimal UI, and stream or post to a gateway. PSRAM variants help buffering.

Firmware profiles in `firmware/platformio.ini` document staged capability builds.

`/esp/process` and `/esp/tts/{filename}` document the contract students should defend as “embedded-friendly API design.”"""

SECTION_BLOCKS["2.3.5 Real-time operating constraints on MCUs"] = """\
MCUs prioritize deterministic ISRs and bounded heap use versus garbage-collected servers. Wi-Fi stack activity can starve audio pipelines without careful task priorities.

Watchdog resets and brownouts appear under heavy simultaneous capture.

Firmware documentation should mention tested profiles rather than claiming all features concurrently on minimal silicon."""

SECTION_BLOCKS["2.3.6 HTTP as lingua franca for student projects"] = """\
HTTP/JSON tooling is universal across Python, mobile, and embedded HTTP clients. It trades binary efficiency for debuggability and rapid iteration.

WebSockets remain optional for streaming events when polling is insufficient.

The gateway’s REST-first approach keeps integration grades transparent to examiners reading `app/api/gateway.py`."""

SECTION_BLOCKS["2.3.7 Unity as client runtime for spatial UI"] = """\
Unity provides mature 3D pipelines for AR navigation cues, asset bundles, and cross-platform export. Build sizes and IL2CPP compile times are practical costs.

Scene graphs should remain thin; business logic belongs server-side where possible.

Unity voice command routes in the gateway show how spatial clients still authenticate like other HTTP clients."""

SECTION_BLOCKS["2.3.8 React Native and Expo for rapid mobile iteration"] = """\
Expo accelerates UI iteration with OTA updates and managed workflows, while still allowing native modules when required.

Networking stacks must handle LAN IPs and TLS lab quirks.

`clients/Expo` integrates navigation MVP libraries and companion capture helpers tied to the gateway."""

SECTION_BLOCKS["2.3.9 QR codes for provisioning and context jumps"] = """\
QR codes bridge physical places to digital state: join a room session, fetch a floorplan, or mark lab equipment context.

They are weak secrets unless rotated; treat encoded tokens as capabilities with TTL.

`qr_service` implements visibility toggles and telemetry suitable for demo analytics extensions."""

SECTION_BLOCKS["2.3.10 Field studies of wearable assistants"] = """\
Wearable field studies emphasize ecological validity: walking speed, sunlight, social embarrassment, and audio noise.

Sample sizes in student projects are small; qualitative codes still help.

Pilot notes for Chapter 4 should cite observed failure modes (network drop, wrong wake) not only happy-path screenshots."""

SECTION_BLOCKS["2.3.11 Cognitive load and attention models"] = """\
Glanceable UI reduces fixation time compared to phone map apps; voice prompts add auditory load that competes with conversation.

Designers should chunk instructions and offer repetition commands.

Gateway sentence caps (`MAX_ANSWER_SENTENCES`) align answers with low-attention contexts."""

SECTION_BLOCKS["2.3.12 Comparison matrix: proposed vs prior architectures"] = """\
Prior architectures often split per client (separate Flask + Unity + ESP endpoints) or hide logic inside vendor SDKs.

The proposed system centralizes orchestration behind FastAPI with explicit models and tests.

Chapter 2’s comparison table should be updated whenever routes change—keep it aligned with `SOURCE_ALIGNMENT.md`."""

# --- Supplementary engineering topics (shorter) ---
_SUP_KEYS = [
    ("Supplementary topic: reproducible ML ops for student projects", "Pin Python dependencies, record `pip freeze` or lockfiles for demos, and snapshot model weights used during evaluation. Small teams benefit more from repeatable `pytest` gates than from exotic MLOps platforms."),
    ("Supplementary topic: containerization vs bare-metal in lab gateways", "Containers improve parity across laptops but add USB/audio forwarding pain. Bare-metal venvs are simpler for microphone access during voice demos. Choose based on demo machine constraints."),
    ("Supplementary topic: rate limiting and backoff on free-tier STT", "Free tiers throttle concurrent streams; exponential backoff prevents thundering herds when multiple phones reconnect. Surface user-visible “try again” states instead of silent hangs."),
    ("Supplementary topic: structured logging with correlation ids", "Assign each request a correlation id propagated to STT, LLM, and TTS subcalls to debug tail latency. JSON logs parse better than ad-hoc print statements during overnight soak tests."),
    ("Supplementary topic: feature flags and staged rollouts", "Gate experimental tools (MCP, vision) behind settings so advisors can run stable mode. Flags belong in `settings` with defaults documented for reproducibility."),
    ("Supplementary topic: contract testing between Expo and FastAPI", "Consumer-driven contract tests catch renamed JSON fields before mobile release. Even a handful of golden-file fixtures beats manual tapping before demos."),
    ("Supplementary topic: protobuf vs JSON for embedded (thesis discussion only)", "Protobuf saves bandwidth on paper, but embedded HTTP stacks and human debuggability often favor JSON for coursework. Document the tradeoff; pick JSON unless bandwidth is measured as a bottleneck."),
    ("Supplementary topic: WebSockets vs polling for session updates", "WebSockets reduce latency for push updates but complicate load balancers and reconnect logic. Polling is crude yet easy to reason about in student timelines."),
    ("Supplementary topic: offline-first caches on mobile clients", "Cache last successful navigation graph and TTS clips for corridor dead zones. Invalidate caches when `navigation.json` version bumps."),
    ("Supplementary topic: accessibility (screen reader + voice)", "Screen reader users need semantic labels on buttons that trigger recording. Voice-only flows should expose repeatable prompts and cancel words."),
    ("Supplementary topic: internationalization of navigation strings", "Separate translatable resource bundles from route ids. RTL layouts and concatenated English strings do not mix."),
    ("Supplementary topic: localization of date/time answers", "LLMs may hallucinate time zones; anchor schedule answers to server clock and explicit campus timezone configuration."),
    ("Supplementary topic: static analysis (ruff/mypy) adoption", "Ruff catches unused imports and risky patterns quickly; mypy catches pydantic model drift. Both reduce demo-week surprises."),
    ("Supplementary topic: security scanners in CI", "Dependency scanners flag CVEs in transitive packages. Treat alerts as triage items, not automatic upgrades, to avoid breaking pins."),
    ("Supplementary topic: secrets scanning (gitleaks)", "Prevent accidental commits of `.env` API keys. Rotate keys immediately if leaks occur, even on private repos."),
    ("Supplementary topic: dependency pinning and SBOM", "Graduation reviewers appreciate pinned requirements and a short SBOM table listing major libraries and versions used at submission time."),
    ("Supplementary topic: disaster recovery for demo laptops", "Keep a USB stick with venv instructions, model cache notes, and offline TTS assets. Assume conference Wi-Fi will fail."),
    ("Supplementary topic: battery profiling on Android clients", "Continuous microphone and camera preview drain batteries fast. Measure mAh impact when claiming “all-day” use."),
    ("Supplementary topic: thermal throttling on ESP32 when Wi-Fi active", "Wi-Fi transmit bursts heat the module; audio + Wi-Fi concurrently can trigger brownouts if power supply traces are thin."),
    ("Supplementary topic: memory fragmentation on long-running Python", "Long-running demo servers may grow RSS due to caches; cap cache sizes (as with TTS TTL) and restart between multi-hour events."),
    ("Supplementary topic: garbage collection pauses and ASR tail latency", "GC pauses hit tail latency for streaming audio pipelines. Preallocate buffers where possible and avoid huge allocations per request."),
    ("Supplementary topic: campus IT firewall rules for LAN demos", "Some universities block device-to-device Wi-Fi. Pre-approve MAC addresses or use a dedicated router segment for demos."),
    ("Supplementary topic: TLS termination strategies", "Terminate TLS at nginx for public demos while keeping plain HTTP inside the lab VLAN if appropriate—document threat model assumptions."),
    ("Supplementary topic: reverse proxy with nginx for public demos", "Reverse proxies add rate limits, gzip, and request logging. They also become a single point of failure unless health-checked."),
    ("Supplementary topic: load testing with k6 (future work)", "k6 scripts can hammer `/process` with canned JSON to find saturation points. Pair with CPU profiling to locate Python hotspots."),
]
for _k, _v in _SUP_KEYS:
    SECTION_BLOCKS[_k] = _v

# --- Inline chapter expansions (formerly long lit_block calls) ---
SECTION_BLOCKS["1.5.1 Traceability from template sections to this repository"] = """\
Faculty templates usually mandate chapters for introduction, related work, methodology, results, discussion, and conclusions. This repository maps those chapters to Markdown sources under `docs/16_submission_package/full_documentation/` generated by `build/generate_expanded_docs.py` and aligned in `SOURCE_ALIGNMENT.md`.

Traceability rows should cite concrete paths: `app/api/gateway.py` for routes, `app/services/*` for domain logic, `tests/*` for acceptance of behaviors claimed in Chapter 4.

When the Word template adds local formatting, keep numbering synchronized by regenerating Markdown before the final Pandoc export."""

SECTION_BLOCKS["2.3.1 Architectural rationale for a single gateway"] = """\
A single FastAPI application keeps authentication, logging, model routing, and navigation session state in one process for demos. It avoids distributed tracing complexity while the team is small.

The modular monolith still enforces separation of concerns via `app/services` modules and pydantic models.

Horizontal scaling is explicitly out of scope; mention in limitations that multiple workers would need external session storage."""

SECTION_BLOCKS["2.3.2 Failure modes and how the proposed design mitigates them"] = """\
Common failures include STT timeouts, LLM refusals, MCP unreachable, and navigation sessions abandoned mid-route. The design mitigates via structured JSON errors, `/debug` probes, and navigation cancel endpoints.

Opaque client crashes are reduced because clients render server messages instead of guessing failures.

Chapter 5 should enumerate observed failures from pilots with severity and mitigation status."""

SECTION_BLOCKS["2.3.3 Positioning relative to microservices versus modular monolith"] = """\
Microservices shine when independent teams scale independently; they hurt small teams with network chatter and deployment overhead.

The codebase follows a modular monolith: clear boundaries without container sprawl.

If future work splits audio streaming or vision into separate services, document the operational cost trade explicitly."""

SECTION_BLOCKS["3.1.3 Requirements elicitation and iteration log"] = """\
Requirements emerged from faculty briefings, advisor checkpoints, and integration pain discovered while wiring Expo to LAN IPs. Non-functional requirements (latency, wake-word annoyance) appeared only after live walkthroughs.

Each iteration should be recoverable in Git tags or short notes in the team log—not only in chat histories.

Requirements trace to pytest cases where possible to prevent silent regressions during “quick fixes.”"""

SECTION_BLOCKS["3.2.7 Design tradeoffs captured in code"] = """\
Notable tradeoffs include in-memory navigation sessions, optional MCP calls with local Moondream fallback, and sentence caps on assistant answers. Each encodes a preference for demo stability over maximal cleverness.

CORS wide-open settings may exist for LAN demos; tighten for any public exposure.

Document tradeoffs beside the code blocks you show in the thesis to satisfy methodology rubrics."""

SECTION_BLOCKS["3.3.1 Operational notes for gateway deployment"] = """\
Run `python start.py` from the repo root after activating the virtual environment. Verify `GET /` health, then `GET /network/info` for LAN discovery.

When MCP is unavailable, disable it in settings so clients do not block on long timeouts.

Rotate API keys between development machines; never reuse production keys in screenshots."""

SECTION_BLOCKS["3.3.2 Implementation lessons learned"] = """\
Wake-word segmentation across streaming STT chunks required explicit follow-up windows rather than naive substring checks. Vision shortcuts needed guardrails to avoid calling heavy models on unrelated text.

pytest fixtures that mirror gateway JSON payloads caught mobile contract drift early.

The largest schedule risk was integration latency, not algorithm novelty—plan demos accordingly."""

SECTION_BLOCKS["3.4.1 Continuous integration and release hygiene"] = """\
A minimal CI pipeline should run `pytest tests/ -q` on pull requests and block merges on failures. Optional jobs can run ruff or mypy if configured.

Tag submission builds with the commit hash printed in the report appendix.

Keep release notes short: what changed in routes, settings, and client environment variables."""

SECTION_BLOCKS["4.2.1 Qualitative observations from pilot users"] = """\
Pilot users often mention confidence after the first successful navigation loop, frustration with false wake events, and surprise at LAN-only setup steps.

Capture anonymized quotes (with consent) and map them to UX changes implemented before defense.

Qualitative themes complement—not replace—latency tables."""

SECTION_BLOCKS["4.3 Instrumentation methodology"] = """\
Instrumentation should record wall-clock timings per pipeline stage and basic counters (sessions started, cancellations). Use consistent units (ms) in tables.

For audio, log buffer sizes and sample rates whenever comparing devices.

Describe hardware (phone model, ESP board, router) beside any numbers so results are reproducible."""

SECTION_BLOCKS["5.4 Comparison back to related work claims"] = """\
Related work claimed broader indoor positioning accuracy than this project attempts. The discussion should honestly separate literature capabilities from implemented scope.

Emphasize engineering contributions: explicit REST contracts, multimodal orchestration, embedded audio fetch path, and automated tests.

Future citations should prioritize peer-reviewed sources over blog posts when advisors demand rigor."""

SECTION_BLOCKS["6.1 Closing reflections"] = """\
The team learned that integration and validation are first-class deliverables, not polish at the end. A working gateway with tests outlives a flashy one-off demo that cannot be reproduced the next semester.

Wearables are one presentation layer; maintainability lives in services, models, and documentation.

Future teams should start measurement notebooks early rather than adding metrics after the final demo week."""


def render_section(title: str, _paragraphs: int = 0) -> str:
    """Return a markdown subsection heading plus unique body."""
    body = SECTION_BLOCKS.get(title) or _default(title)
    return f"### {title}\n\n{body.strip()}\n\n"
