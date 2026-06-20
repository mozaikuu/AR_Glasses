# Chapter 2 — RELATED WORK (continued)

## 2.3 Comparison Between Existing and Proposed Method

Table 2.1 summarizes how Smart Glasses Distilled positions relative to common alternatives. The “Proposed system” column reflects
the **implemented** repository rather than a hypothetical design.

| Dimension | Typical phone map app | General voice assistant | Research indoor SLAM stack | **Smart Glasses Distilled (this work)** |
|-----------|----------------------|---------------------------|----------------------------|----------------------------------------|
| Primary modality | Visual map + GPS/Wi-Fi outdoors | Cloud voice loop | Sensors + offline map | **HTTP gateway + multimodal `/process`** |
| Indoor graph ownership | Often proprietary / campus partnership | Not first-class | Custom lab maps | **Server session steps + client-side assets (Expo GLB / JSON)** |
| Embedded friendliness | N/A | Limited | Rare in student scope | **`/esp/process` + `/esp/tts/{filename}` contract** |
| Testability in CI | Limited without device farms | Black-box | Bag-of-scripts risk | **`pytest` across gateway and services** |
| Extensibility | SDK-bound | Skill store | Research code | **FastAPI routes + `app/services` modules** |

### 2.3.1 Architectural rationale for a single gateway

A single FastAPI application keeps authentication, logging, model routing, and navigation session state in one process for demos. It avoids distributed tracing complexity while the team is small.

The modular monolith still enforces separation of concerns via `app/services` modules and pydantic models.

Horizontal scaling is explicitly out of scope; mention in limitations that multiple workers would need external session storage.

### 2.3.2 Failure modes and how the proposed design mitigates them

Common failures include STT timeouts, LLM refusals, MCP unreachable, and navigation sessions abandoned mid-route. The design mitigates via structured JSON errors, `/debug` probes, and navigation cancel endpoints.

Opaque client crashes are reduced because clients render server messages instead of guessing failures.

Chapter 5 should enumerate observed failures from pilots with severity and mitigation status.

### 2.3.3 Positioning relative to microservices versus modular monolith

Microservices shine when independent teams scale independently; they hurt small teams with network chatter and deployment overhead.

The codebase follows a modular monolith: clear boundaries without container sprawl.

If future work splits audio streaming or vision into separate services, document the operational cost trade explicitly.
