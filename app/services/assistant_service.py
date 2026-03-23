from __future__ import annotations

import datetime
import json
import re
from urllib.request import Request, urlopen

from app.agent.llm import complete
from app.config.settings import settings
from app.models.requests import ProcessRequest, TextRequest
from tools.speech.transcription import transcribe_audio


class AssistantService:
    _wake_words = ("hey Computer", "Computer")

    def __init__(self) -> None:
        self._wake_context_by_client: dict[str, str] = {}

    def _check_wakeword(self, text: str) -> tuple[bool, str]:
        if not text:
            return False, ""

        last_match: re.Match[str] | None = None
        for wake in self._wake_words:
            words = wake.split()
            if not words:
                continue
            sep = r"[\s,;:\-_]*"
            pattern = r"\b" + sep.join(re.escape(word) for word in words) + r"\b"
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if last_match is None or match.start() >= last_match.start():
                    last_match = match

        if last_match is not None:
            cleaned = text[last_match.end() :]
            cleaned = re.sub(r"^[\s,;:\-_]+", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return True, cleaned

        return False, text

    def _append_wake_context(self, client: str, chunk: str) -> str:
        previous = self._wake_context_by_client.get(client, "")
        merged = f"{previous} {chunk}".strip()
        # Keep a short rolling tail so wake detection can bridge chunk boundaries.
        merged = merged[-240:]
        self._wake_context_by_client[client] = merged
        return merged

    def _clear_wake_context(self, client: str) -> None:
        self._wake_context_by_client.pop(client, None)

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

    def _mcp_post_json(self, path: str, payload: dict[str, object]) -> dict[str, object] | None:
        if not settings.enable_mcp_server:
            return None

        base = f"http://{settings.mcp_host}:{settings.mcp_port}"
        url = f"{base}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=8.0) as response:
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
            "what is in front",
            "describe what you see",
            "look at this",
            "identify this",
        )
        return any(cue in lowered for cue in cues)

    def _run_mcp_vision_from_image(self, image_base64: str, prompt: str) -> str | None:
        result = self._mcp_post_json(
            "/tools/vision/analyze-image-moondream",
            {"image_base64": image_base64, "prompt": prompt or "Read and describe this image."},
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

        text = request.text or ""
        raw_transcript = ""
        transcript_used = ""
        wakeword_triggered = False
        always_listen = bool(request.metadata.get("always_listen")) if isinstance(request.metadata, dict) else False
        client_key = (request.client or "default").strip() or "default"
        if not text and request.audio_base64:
            raw_transcript = transcribe_audio(request.audio_base64)
            if raw_transcript:
                wake_check_source = raw_transcript
                if always_listen:
                    wake_check_source = self._append_wake_context(client_key, raw_transcript)

                wakeword_triggered, stripped = self._check_wakeword(wake_check_source)

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
                            "stt_provider": "google_speech_recognition",
                            "llm_provider": "",
                            "ignored_audio": True,
                        },
                    }

                if wakeword_triggered:
                    self._clear_wake_context(client_key)

                text = stripped if wakeword_triggered and stripped else raw_transcript
                transcript_used = text.strip()

                # Wake word may be detected before the spoken command arrives.
                if always_listen and wakeword_triggered and not transcript_used:
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
                            "stt_provider": "google_speech_recognition",
                            "llm_provider": "",
                            "ignored_audio": True,
                        },
                    }
            else:
                if always_listen:
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
                            "stt_provider": "google_speech_recognition",
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
                        "stt_provider": "google_speech_recognition",
                        "llm_provider": "",
                        "ignored_audio": True,
                    },
                }
        else:
            if text:
                self._clear_wake_context(client_key)
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
                    "stt_provider": "google_speech_recognition" if request.audio_base64 else "",
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
                        "stt_provider": "google_speech_recognition" if request.audio_base64 else "",
                        "llm_provider": settings.model_provider,
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
                        "stt_provider": "google_speech_recognition" if request.audio_base64 else "",
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
                "stt_provider": "google_speech_recognition" if request.audio_base64 else "",
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
        lowered = command.lower()
        if "ta" in lowered and "office" in lowered:
            return "TA_Office"
        if "entrance" in lowered:
            return "Entrance"
        if "stairs" in lowered:
            return "Stairs_G"
        if "elevator" in lowered:
            return "Elevator"
        if "library" in lowered:
            return "Library"
        return "Entrance"

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
            destination = self.resolve_destination_from_command(command)
            unknown_markers = ["mars", "moon", "jupiter"]
            if any(marker in lowered for marker in unknown_markers):
                return {
                    "action": "speak",
                    "intent": "navigation_unknown_destination",
                    "response_text": "I could not map that destination to known campus locations.",
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
