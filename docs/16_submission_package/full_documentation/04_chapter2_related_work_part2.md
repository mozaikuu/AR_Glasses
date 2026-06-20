# Chapter 2 — RELATED WORK (continued)

## 2.1 Existing Systems (continued)

### 2.2.1 Cloud ASR latency budgets

Cloud ASR adds network round trips and queueing variance on top of model compute. Interactive assistants need budgets for partial results, endpointing, and barge-in cancellation.

Campus Wi-Fi contention during events can dominate tail latency.

The gateway’s audio path should log timestamps per stage (upload, transcribe, LLM, TTS) when advisors request quantitative tables in Chapter 4.


### 2.2.2 Streaming partial hypotheses and barge-in

Streaming ASR emits partial transcripts that fluctuate before finalization; dialog managers must avoid acting prematurely while still feeling responsive.

Barge-in requires echo cancellation discipline and rapid cancellation of pending TTS playback.

`AssistantService` implements wake-follow windows and transcript normalization—document these behaviors when discussing streaming UX.


### 2.2.3 Wake-word detection and false accepts

Wake-word engines trade false accepts (accidental triggers) against false rejects (missed commands). Public demos suffer from background speech and TV audio.

Rollout policy belongs in configuration (`settings.wakeword_rollout_scope`) rather than hard-coded client forks.

Tests should include negative audio cases where no wake word appears to guard regressions.


### 2.2.4 On-device keyword spotting

Tiny keyword spotters run continuously at milliwatts, gating uplink to heavier cloud models. Vocabulary is limited compared to full LVCSR.

Hybrid designs keep privacy-sensitive always-listening stages local.

ESP-class peripherals in this project are better matched to button/wake flows unless a dedicated DSP front-end is added.


### 2.2.5 LLM tool use and grounding

Tool-augmented LLMs route user intents to APIs (navigation, vision, calendars). Reliability hinges on schema design, argument validation, and refusal when tools disagree.

Grounding reduces hallucinated campus facts by retrieving snippets (RAG) or executing structured queries.

Optional MCP integration in the repo illustrates the tool-call pattern without mandating a specific vendor model.


### 2.2.6 Retrieval-augmented generation for campus FAQs

RAG pairs a retriever (vector or keyword index) with a generator to cite local policies, exam rules, or building hours. Chunking and metadata filters dominate quality.

Stale embeddings misinform users; refresh pipelines matter.

For Smart Glasses Distilled, small curated JSON or markdown corpora may outperform large uncurated scrapes during demos.


### 2.2.7 Multimodal models combining vision and language

Vision-language models can answer “what is on this poster?” from a captured frame. Latency and privacy move to the forefront versus text-only chat.

Moondream or MCP vision tools in this codebase exemplify optional multimodal paths gated by heuristics and client capabilities.

Advisors often ask for explicit consent flows when cameras are involved.


### 2.2.8 Safety alignment and refusal policies

Assistants should refuse unsafe instructions (e.g., disabling lab safety interlocks) and avoid leaking secrets from prompts. Alignment techniques vary by provider.

Campus deployments still need institutional policy: the model is not the compliance officer.

Document which provider safety filters are enabled and known gaps for your defense Q&A.


### 2.2.9 TTS quality versus latency (neural vs classical)

Neural TTS sounds natural but costs GPU time or remote API fees; classical concatenative/parametric systems are cheaper but robotic.

Caching frequent phrases (“Turn left”) improves perceived speed.

The gateway implements in-memory TTS clip caching for repeated prompts during demos.


### 2.2.10 Piper and lightweight on-gateway synthesis

Piper and similar compact engines enable on-gateway speech without shipping audio back to a third party—useful for air-gapped labs.

Voice quality may be lower than cloud neural voices; acceptability depends on scenario.

ESP fetch endpoints (`/esp/tts/{filename}`) pair naturally with pre-synthesized or cached clips.


### 2.2.11 Dialog state tracking for navigation sessions

Navigation as a dialog requires explicit state: active session id, current step index, cancellation, and replanning after detours.

State machines are easier to test than implicit prompt-only memory.

`navigation_service` stores sessions in an in-memory dict—great for coursework, noted as a limitation for multi-instance deployments.


### 2.2.12 Evaluation metrics: WER, SER, task success

Word error rate measures transcription fidelity; semantic error rate or slot F1 measures intent extraction; task success measures end-to-end goal completion.

Navigation should log where users drop off (timeout vs wrong step).

Chapter 4 should report whichever metrics your pilot actually measured.


### 2.2.13 Privacy of voice biometrics

Voiceprints can identify or re-identify users; storage and comparison require consent and retention limits in many jurisdictions.

Even without explicit voiceprint features, raw audio is sensitive.

Project documentation should state retention defaults for logs and whether transcripts are persisted.


### 2.2.14 Multilingual classrooms and code-switching

Campus speech mixes languages mid-utterance; monolingual ASR models degrade. Language-id gating or multilingual models add cost.

Navigation prompts may need localized strings separate from LLM answers.

`metadata.yaml` and client i18n hooks are the right place to demonstrate awareness even if the demo stays English-first.


### 2.2.15 Comparison to general assistants (Siri, Assistant, Alexa)

Consumer assistants optimize for music, smart home, and web search—not authored indoor graphs tied to a lab gateway.

They also hide integration details behind opaque SDKs.

This work’s differentiation is inspectable HTTP routes, reproducible tests, and campus-specific navigation sessions under team control.
