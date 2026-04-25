from __future__ import annotations

import datetime
import json
import logging
import re
import time
from urllib.request import Request, urlopen

from app.agent.llm import complete
from app.config.settings import settings
from app.models.requests import ProcessRequest, TextRequest
from app.services.navigation_service import navigation_service
from tools.speech.transcription import transcribe_audio_detailed


logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self) -> None:
        configured_words = [w.strip().lower() for w in settings.wake_words if w.strip()]
        configured_aliases = [w.strip().lower() for w in settings.wake_word_aliases if w.strip()]
        wake_words = configured_words + configured_aliases
        if not wake_words:
            wake_words = ["computer", "hey computer", "ok computer", "okay computer"]

        self._wake_words: tuple[str, ...] = tuple(dict.fromkeys(wake_words))
        self._wake_patterns: tuple[tuple[str, re.Pattern[str]], ...] = self._compile_wake_patterns(self._wake_words)
        self._wake_context_chars = max(120, int(settings.wake_context_chars))
        self._wake_followup_window_seconds = max(2.0, float(settings.wake_followup_window_seconds))
        self._wake_min_transcript_chars = max(1, int(settings.wake_min_transcript_chars))
        self._wake_context_by_client: dict[str, str] = {}
        self._wake_armed_until_by_client: dict[str, float] = {}

    def _compile_wake_patterns(self, wake_words: tuple[str, ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
        compiled: list[tuple[str, re.Pattern[str]]] = []
        sep = r"[\s,;:\-_]*"
        for wake in wake_words:
            tokens = [tok for tok in re.findall(r"[a-z0-9']+", wake.lower()) if tok]
            if not tokens:
                continue
            phrase = r"\b" + sep.join(re.escape(token) for token in tokens) + r"\b"
            compiled.append((wake, re.compile(rf"(?<!\w)({phrase})(?!\w)", flags=re.IGNORECASE)))
        return tuple(compiled)

    def _normalize_transcript(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _is_transcript_useful(self, text: str) -> bool:
        normalized = self._normalize_transcript(text)
        if not normalized:
            return False
        signal = re.sub(r"[^a-zA-Z0-9]", "", normalized)
        return len(signal) >= self._wake_min_transcript_chars

    def _check_wakeword(self, text: str) -> tuple[bool, str]:
        normalized = self._normalize_transcript(text)
        if not normalized:
            return False, ""

        last_match: re.Match[str] | None = None
        for _wake, pattern in self._wake_patterns:
            for match in pattern.finditer(normalized):
                if last_match is None or match.start() >= last_match.start():
                    last_match = match

        if last_match is not None:
            phrase_match = last_match.group(1)
            phrase_end = last_match.start(1) + len(phrase_match)
            cleaned = normalized[phrase_end:]
            cleaned = re.sub(r"^[\s,;:\-_]+", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return True, cleaned

        return False, normalized

    def _append_wake_context(self, client: str, chunk: str) -> str:
        previous = self._normalize_transcript(self._wake_context_by_client.get(client, ""))
        merged = self._normalize_transcript(f"{previous} {chunk}")
        # Keep a rolling tail so wake detection can bridge chunk boundaries safely.
        if len(merged) > self._wake_context_chars:
            merged = merged[-self._wake_context_chars :]
            first_space = merged.find(" ")
            if 0 <= first_space < max(4, self._wake_context_chars // 3):
                merged = merged[first_space + 1 :]
        self._wake_context_by_client[client] = merged
        return merged

    def _clear_wake_context(self, client: str) -> None:
        self._wake_context_by_client.pop(client, None)

    def _arm_wake_followup(self, client: str) -> None:
        self._wake_armed_until_by_client[client] = time.monotonic() + self._wake_followup_window_seconds

    def _is_wake_followup_armed(self, client: str) -> bool:
        armed_until = self._wake_armed_until_by_client.get(client)
        if armed_until is None:
            return False
        if armed_until <= time.monotonic():
            self._wake_armed_until_by_client.pop(client, None)
            return False
        return True

    def _clear_wake_followup(self, client: str) -> None:
        self._wake_armed_until_by_client.pop(client, None)

    def _postprocess_answer(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()
        # Remove common planning/thought-process preambles.
        preamble_patterns = [
            r"^to help you[^\n]*[\n\r]+",
            r"^i('m| am) (going to|searching|looking for)[^\n]*[\n\r]+",
            r"^first,? [^\n]*[\n\r]+",
        ]
        for pattern in preamble_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Keep final answer concise and on-point.
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        capped = " ".join(parts[: max(1, settings.max_answer_sentences)]).strip()
        return capped or cleaned

    def _local_time_date_answer(self, text: str) -> str | None:
        q = (text or "").strip().lower()
        is_time = any(k in q for k in ("what time", "time", "clock"))
        is_day = any(k in q for k in ("what day", "what date", "today", "date"))
        if not (is_time or is_day):
            return None

        now = datetime.datetime.now().astimezone()
        parts: list[str] = []
        if is_day:
            parts.append(f"Today is {now.strftime('%A, %B %d, %Y')}.")
        if is_time:
            parts.append(f"The current time is {now.strftime('%I:%M %p %Z').lstrip('0')}.")
        return " ".join(parts)

    def _mcp_capability_context(self) -> str:
        if not settings.enable_mcp_server:
            return "MCP is disabled in configuration."

        mcp_url = f"http://{settings.mcp_host}:{settings.mcp_port}/"
        try:
            with urlopen(mcp_url, timeout=1.2) as response:
                if response.status != 200:
                    return "MCP is enabled but currently unavailable."
                data = json.loads(response.read().decode("utf-8"))
                tools = data.get("tools", []) if isinstance(data, dict) else []
                if isinstance(tools, list) and tools:
                    return f"Available MCP capabilities: {', '.join(str(t) for t in tools)}."
                return "MCP connected with unspecified capabilities."
        except Exception:
            return "MCP is enabled but currently unavailable."

    def _mcp_post_json(
        self,
        path: str,
        payload: dict[str, object],
        timeout_seconds: float = 8.0,
    ) -> dict[str, object] | None:
        if not settings.enable_mcp_server:
            return None

        base = f"http://{settings.mcp_host}:{settings.mcp_port}"
        url = f"{base}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=timeout_seconds) as response:
                if response.status != 200:
                    return None
                parsed = json.loads(response.read().decode("utf-8"))
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _vision_intent(self, text: str) -> bool:
        lowered = (text or "").strip().lower()
        if not lowered:
            return False
        cues = (
            "can you read this",
            "read this",
            "what do you see",
            "what am i looking at",
            "what i am looking at",
            "what i'm looking at",
            "what is in front",
            "what is in front of me",
            "describe what you see",
            "describe what i am looking at",
            "describe what i'm looking at",
            "look at this",
            "identify this",
        )
        return any(cue in lowered for cue in cues)

    def _run_mcp_vision_from_image(self, image_base64: str, prompt: str) -> str | None:
        result = self._mcp_post_json(
            "/tools/vision/analyze-image-moondream",
            {"image_base64": image_base64, "prompt": prompt or "Read and describe this image."},
            timeout_seconds=45.0,
        )
        if not result:
            return None
        text = str(result.get("text") or "").strip()
        return text or None

    def _run_mcp_vision_from_camera(self, prompt: str) -> str | None:
        result = self._mcp_post_json(
            "/tools/vision/capture-moondream",
            {
                "prompt": prompt or "Describe what you see.",
                "camera_index": None,
                "camera_candidates": [0, 1, 2],
                "include_image": False,
            },
            timeout_seconds=15.0,
        )
        if not result:
            return None
        text = str(result.get("text") or result.get("answer") or "").strip()
        return text or None

    def process(self, request: ProcessRequest) -> dict[str, object]:
        source_signals: list[str] = []
        if request.text:
            source_signals.append("text")
        if request.image_base64:
            source_signals.append("image")
        if request.audio_base64:
            source_signals.append("audio")

        request_metadata = request.metadata if isinstance(request.metadata, dict) else {}
        text = request.text or ""
        raw_transcript = ""
        transcript_used = ""
        wakeword_triggered = False
        stt_debug: dict[str, object] = {}
        always_listen = bool(request_metadata.get("always_listen"))
        client_key = (request.client or "default").strip() or "default"
        if not text and request.audio_base64:
            raw_transcript, stt_debug = transcribe_audio_detailed(request.audio_base64, metadata=request_metadata)
            if raw_transcript:
                normalized_transcript = self._normalize_transcript(raw_transcript)
                wake_check_source = normalized_transcript
                wake_followup_armed = False
                if always_listen:
                    wake_check_source = self._append_wake_context(client_key, normalized_transcript)
                    wake_followup_armed = self._is_wake_followup_armed(client_key)

                wakeword_triggered, stripped = self._check_wakeword(wake_check_source)

                if always_listen and not wakeword_triggered and wake_followup_armed and self._is_transcript_useful(normalized_transcript):
                    # Wake word landed on previous chunk; treat this transcript as command continuation.
                    wakeword_triggered = True
                    stripped = normalized_transcript
                    self._clear_wake_followup(client_key)
                    self._clear_wake_context(client_key)

                # In always-listen mode, only forward to LLM after wakeword trigger.
                if always_listen and not wakeword_triggered:
                    return {
                        "text": "Listening... say 'Computer' to trigger.",
                        "mode": request.mode,
                        "client": request.client,
                        "tool_calls": [],
                        "metadata": {
                            "inputs": source_signals,
                            "raw_transcript": raw_transcript,
                            "transcript": raw_transcript,
                            "wakeword_triggered": False,
                            "wakeword": "",
                            "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                            "ignored_audio_reason": "wakeword_not_detected",
                            "wakeword_candidates": list(self._wake_words),
                            "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition"),
                            "stt_debug": stt_debug,
                            "llm_provider": "",
                            "ignored_audio": True,
                        },
                    }

                if wakeword_triggered:
                    self._clear_wake_context(client_key)
                    self._clear_wake_followup(client_key)

                # After a wake-word hit, forward only the post-wake command segment.
                text = stripped if wakeword_triggered else raw_transcript
                transcript_used = text.strip()

                # Wake word may be detected before the spoken command arrives.
                if always_listen and wakeword_triggered and not transcript_used:
                    self._arm_wake_followup(client_key)
                    return {
                        "text": "Wake word detected. Listening for your command.",
                        "mode": request.mode,
                        "client": request.client,
                        "tool_calls": [],
                        "metadata": {
                            "inputs": source_signals,
                            "raw_transcript": raw_transcript,
                            "transcript": "",
                            "wakeword_triggered": True,
                            "wakeword": "Computer",
                            "wakeword_followup_armed": True,
                            "ignored_audio_reason": "wakeword_detected_waiting_command",
                            "wakeword_candidates": list(self._wake_words),
                            "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition"),
                            "stt_debug": stt_debug,
                            "llm_provider": "",
                            "ignored_audio": True,
                        },
                    }
            else:
                if always_listen:
                    if self._is_wake_followup_armed(client_key):
                        logger.debug("Waiting for post-wake command transcript for client=%s", client_key)
                    return {
                        "text": "Listening...",
                        "mode": request.mode,
                        "client": request.client,
                        "tool_calls": [],
                        "metadata": {
                            "inputs": source_signals,
                            "raw_transcript": "",
                            "transcript": "",
                            "wakeword_triggered": False,
                            "wakeword": "",
                            "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                            "ignored_audio_reason": "awaiting_followup_command"
                            if self._is_wake_followup_armed(client_key)
                            else "no_transcript",
                            "wakeword_candidates": list(self._wake_words),
                            "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition"),
                            "stt_debug": stt_debug,
                            "llm_provider": "",
                            "ignored_audio": True,
                        },
                    }

                return {
                    "text": "I could not transcribe the audio clearly.",
                    "mode": request.mode,
                    "client": request.client,
                    "tool_calls": [],
                    "metadata": {
                        "inputs": source_signals,
                        "raw_transcript": "",
                        "transcript": "",
                        "wakeword_triggered": False,
                        "wakeword": "",
                        "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                        "ignored_audio_reason": "stt_failed",
                        "wakeword_candidates": list(self._wake_words),
                        "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition"),
                        "stt_debug": stt_debug,
                        "llm_provider": "",
                        "ignored_audio": True,
                    },
                }
        else:
            if text:
                self._clear_wake_context(client_key)
                self._clear_wake_followup(client_key)
            transcript_used = text

        if not (text or "").strip():
            return {
                "text": "Listening...",
                "mode": request.mode,
                "client": request.client,
                "tool_calls": [],
                "metadata": {
                    "inputs": source_signals,
                    "raw_transcript": raw_transcript,
                    "transcript": "",
                    "wakeword_triggered": wakeword_triggered,
                    "wakeword": "Computer" if wakeword_triggered else "",
                    "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                    "ignored_audio_reason": "empty_transcript_after_filter",
                    "wakeword_candidates": list(self._wake_words),
                    "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition") if request.audio_base64 else "",
                    "stt_debug": stt_debug if request.audio_base64 else {},
                    "llm_provider": "",
                    "ignored_audio": True,
                },
            }

        if request.image_base64:
            vision_answer = self._run_mcp_vision_from_image(request.image_base64, text)
            if vision_answer:
                return {
                    "text": vision_answer,
                    "mode": request.mode,
                    "client": request.client,
                    "tool_calls": ["vision.analyze_image_moondream"],
                    "metadata": {
                        "inputs": source_signals,
                        "raw_transcript": raw_transcript,
                        "transcript": transcript_used,
                        "wakeword_triggered": wakeword_triggered,
                        "wakeword": "Computer" if wakeword_triggered else "",
                        "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                        "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition") if request.audio_base64 else "",
                        "stt_debug": stt_debug if request.audio_base64 else {},
                        "llm_provider": settings.model_provider,
                    },
                }
            return {
                "text": "I couldn't analyze the image from the camera. Please try again with better lighting or hold the scene steady.",
                "mode": request.mode,
                "client": request.client,
                "tool_calls": ["vision.analyze_image_moondream_failed"],
                "metadata": {
                    "inputs": source_signals,
                    "raw_transcript": raw_transcript,
                    "transcript": transcript_used,
                    "wakeword_triggered": wakeword_triggered,
                    "wakeword": "Computer" if wakeword_triggered else "",
                    "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                    "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition") if request.audio_base64 else "",
                    "stt_debug": stt_debug if request.audio_base64 else {},
                    "llm_provider": settings.model_provider,
                    "vision_error": "image_analysis_unavailable",
                },
            }

        if self._vision_intent(text):
            vision_answer = self._run_mcp_vision_from_camera(text)
            if vision_answer:
                return {
                    "text": vision_answer,
                    "mode": request.mode,
                    "client": request.client,
                    "tool_calls": ["vision.capture_moondream"],
                    "metadata": {
                        "inputs": source_signals,
                        "raw_transcript": raw_transcript,
                        "transcript": transcript_used,
                        "wakeword_triggered": wakeword_triggered,
                        "wakeword": "Computer" if wakeword_triggered else "",
                        "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                        "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition") if request.audio_base64 else "",
                        "stt_debug": stt_debug if request.audio_base64 else {},
                        "llm_provider": settings.model_provider,
                    },
                }

        answer = self.compose_answer(text=text, mode=request.mode)
        return {
            "text": answer,
            "mode": request.mode,
            "client": request.client,
            "tool_calls": [],
            "metadata": {
                "inputs": source_signals,
                "raw_transcript": raw_transcript,
                "transcript": transcript_used,
                "wakeword_triggered": wakeword_triggered,
                "wakeword": "Computer" if wakeword_triggered else "",
                "wakeword_followup_armed": self._is_wake_followup_armed(client_key),
                "stt_provider": str(stt_debug.get("provider") or "google_speech_recognition") if request.audio_base64 else "",
                "stt_debug": stt_debug if request.audio_base64 else {},
                "llm_provider": settings.model_provider,
            },
        }

    def run_text(self, request: TextRequest) -> dict[str, object]:
        answer = self.compose_answer(text=request.text, mode=request.mode)
        return {
            "text": answer,
            "mode": request.mode,
            "client": request.client,
            "tool_calls": [],
            "metadata": {"inputs": ["text"]},
        }

    def resolve_destination_from_command(self, command: str) -> str:
        return navigation_service.resolve_authoritative_destination_id(command)

    def _extract_navigation_query(self, command: str) -> str:
        normalized = re.sub(r"[^a-z0-9\s_-]", " ", command.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized:
            return ""

        cues = [
            "i want to go to",
            "take me to",
            "guide me to",
            "navigate to",
            "where is",
            "go to",
            "navigate",
        ]

        for cue in cues:
            if normalized.startswith(cue):
                candidate = normalized[len(cue) :].strip()
                if candidate:
                    return candidate

        for cue in cues:
            marker = f" {cue} "
            index = normalized.find(marker)
            if index >= 0:
                candidate = normalized[index + len(marker) :].strip()
                if candidate:
                    return candidate

        return normalized

    def route_unity_command(self, command: str, mode: str = "quick") -> dict[str, object]:
        lowered = command.strip().lower()

        # Navigation cancel path so Unity can stop active guidance quickly.
        if "stop navigation" in lowered or "cancel navigation" in lowered:
            return {
                "action": "cancel_navigation",
                "intent": "navigation_cancel",
                "response_text": "Navigation cancelled.",
                "mode": mode,
                "confidence": 0.95,
            }

        # Time and date queries are served as direct spoken responses.
        if "what day" in lowered or "what time" in lowered or "date" in lowered:
            return {
                "action": "speak",
                "intent": "time_date",
                "response_text": self.compose_answer(text="It is currently available from the server clock endpoint.", mode=mode),
                "mode": mode,
                "confidence": 0.85,
            }

        navigation_cues = ["take me", "go to", "navigate", "where is"]
        if any(cue in lowered for cue in navigation_cues):
            destination_query = self._extract_navigation_query(command)
            destination = self.resolve_destination_from_command(destination_query)
            if not destination and destination_query != command:
                destination = self.resolve_destination_from_command(command)
            if not destination:
                return {
                    "action": "speak",
                    "intent": "navigation_unknown_destination",
                    "response_text": "I could not map that destination to a known navigation ID.",
                    "mode": mode,
                    "confidence": 0.62,
                }

            return {
                "action": "navigate",
                "intent": "navigation_start",
                "destination": destination,
                "response_text": f"Starting navigation to {destination}.",
                "mode": mode,
                "confidence": 0.9,
            }

        return {
            "action": "speak",
            "intent": "general_query",
            "response_text": self.compose_answer(text=command, mode=mode),
            "mode": mode,
            "confidence": 0.7,
        }

    def compose_answer(self, text: str, mode: str) -> str:
        local_time_answer = self._local_time_date_answer(text)
        if local_time_answer is not None:
            return local_time_answer

        runtime_now = datetime.datetime.now().astimezone().strftime("%A, %B %d, %Y %I:%M %p %Z")
        prompt = text or "Ready."
        prompt = (
            "Runtime context for this request:\n"
            f"- Current date/time: {runtime_now}\n"
            "Use this context when answering. Do not claim lack of real-time access when context is present.\n"
            "Do not list tool capabilities unless the user explicitly asks for a capability list.\n\n"
            f"User request: {prompt}"
        )
        model_answer = complete(prompt=prompt, mode=mode)
        return self._postprocess_answer(model_answer)


assistant_service = AssistantService()
