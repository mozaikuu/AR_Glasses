from __future__ import annotations

import base64
import hashlib
import io
import queue
import wave
from typing import Any

import httpx
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from app.config.settings import settings

try:
    from streamlit_webrtc import WebRtcMode, webrtc_streamer

    WEBRTC_AVAILABLE = True
except Exception:
    WEBRTC_AVAILABLE = False


def _gateway_host() -> str:
    return "127.0.0.1" if settings.api_host == "0.0.0.0" else settings.api_host


def _gateway_base() -> str:
    return f"http://{_gateway_host()}:{settings.api_port}"


def _api_get(path: str, timeout: float = 8.0) -> tuple[dict[str, Any], int]:
    url = f"{_gateway_base()}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
        data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        if not isinstance(data, dict):
            data = {"raw": str(data)}
        return data, response.status_code
    except Exception as exc:
        return {"error": str(exc)}, 0


def _api_post(path: str, payload: dict[str, Any], timeout: float = 45.0) -> tuple[dict[str, Any], int]:
    url = f"{_gateway_base()}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
        data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        if not isinstance(data, dict):
            data = {"raw": str(data)}
        return data, response.status_code
    except Exception as exc:
        return {"error": str(exc)}, 0


def _normalize_tts_url(tts_url: str) -> str:
    if tts_url.startswith("http://") or tts_url.startswith("https://"):
        return tts_url
    return f"{_gateway_base()}{tts_url}"


def _autoplay_tts(tts_url: str) -> None:
    safe_url = _normalize_tts_url(tts_url)
    # Streamlit's st.audio doesn't autoplay consistently; inject a minimal audio element.
    components.html(
        f"""
        <audio autoplay controls style=\"width:100%\">
          <source src=\"{safe_url}\" type=\"audio/wav\" />
        </audio>
        """,
        height=56,
    )


def _last_audio_signature(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _pcm16_mono_to_wav_bytes(pcm_bytes: bytes, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_writer:
        wav_writer.setnchannels(1)
        wav_writer.setsampwidth(2)
        wav_writer.setframerate(sample_rate)
        wav_writer.writeframes(pcm_bytes)
    return buffer.getvalue()


def _render_voice_result(data: dict[str, Any], code: int) -> None:
    if code != 200:
        st.error(f"Audio request failed ({code}): {data.get('error', data)}")
        return

    answer = str(data.get("text") or "")
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    ignored_audio = bool(metadata.get("ignored_audio"))

    if not ignored_audio:
        st.session_state.messages.append({"role": "user", "text": "[Voice input]"})
        st.session_state.messages.append({"role": "assistant", "text": answer})

    if metadata.get("wakeword_triggered"):
        st.success("Wake word triggered: Computer")
    elif ignored_audio:
        st.info("Listening... wake word not detected yet.")

    transcript = metadata.get("transcript")
    if isinstance(transcript, str) and transcript.strip():
        st.caption(f"Transcript: {transcript}")

    st.caption(
        f"Pipeline: STT={metadata.get('stt_provider', '') or 'n/a'} -> LLM={metadata.get('llm_provider', '') or 'n/a'}"
    )

    tts_url = data.get("metadata", {}).get("tts_url") if isinstance(data.get("metadata"), dict) else None
    if isinstance(tts_url, str) and tts_url:
        _autoplay_tts(tts_url)


st.set_page_config(page_title="Smart Glasses Distilled", layout="wide")
st.title("Smart Glasses Distilled")
st.caption("Primary interface migrated to Streamlit")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "mic_enabled" not in st.session_state:
    st.session_state.mic_enabled = True
if "last_audio_sig" not in st.session_state:
    st.session_state.last_audio_sig = ""
if "webrtc_pcm_buffer" not in st.session_state:
    st.session_state.webrtc_pcm_buffer = b""
if "webrtc_sample_rate" not in st.session_state:
    st.session_state.webrtc_sample_rate = 16000
if "webrtc_audio_tasks" not in st.session_state:
    st.session_state.webrtc_audio_tasks = []
if "webrtc_dropped_tasks" not in st.session_state:
    st.session_state.webrtc_dropped_tasks = 0
if "wakeword_required" not in st.session_state:
    st.session_state.wakeword_required = True

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"Gateway: {_gateway_base()}")

    health, health_code = _api_get("/")
    mcp, mcp_code = _api_get("/mcp-status")

    st.write(f"Gateway status: {health_code}")
    st.json(health)
    st.write(f"MCP status: {mcp_code}")
    st.json(mcp)

    st.markdown(f"Mic diagnostics: {_gateway_base()}/mic-test")

    st.subheader("Listening")
    new_mic_enabled = st.toggle("Always listen", value=st.session_state.mic_enabled)
    st.session_state.wakeword_required = st.toggle(
        "Require wake word ('Computer')",
        value=st.session_state.wakeword_required,
        help="Disable for debugging so audio is sent directly to the assistant without wake-word gating.",
    )
    if new_mic_enabled != st.session_state.mic_enabled:
        st.session_state.mic_enabled = new_mic_enabled
        if new_mic_enabled:
            _api_post("/control/start", {})
        else:
            _api_post("/control/stop", {})

left, right = st.columns([2, 1])

with left:
    st.subheader("Assistant")
    mode = st.segmented_control("Mode", options=["quick", "thinking"], default="quick")

    user_text = st.text_area("Text prompt", placeholder="Type your request")
    if st.button("Send Text", type="primary"):
        prompt = (user_text or "").strip()
        if not prompt:
            st.warning("Enter a prompt first.")
        else:
            data, code = _api_post(
                "/process",
                {
                    "text": prompt,
                    "mode": mode,
                    "client": "streamlit-main",
                    "metadata": {},
                },
            )
            if code != 200:
                st.error(f"Request failed ({code}): {data.get('error', data)}")
            else:
                answer = str(data.get("text") or "")
                st.session_state.messages.append({"role": "user", "text": prompt})
                st.session_state.messages.append({"role": "assistant", "text": answer})
                metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                if metadata.get("wakeword_triggered"):
                    st.success("Wake word triggered: Computer")
                tts_url = data.get("metadata", {}).get("tts_url") if isinstance(data.get("metadata"), dict) else None
                if isinstance(tts_url, str) and tts_url:
                    _autoplay_tts(tts_url)

    st.write("Conversation")
    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            st.markdown(f"You: {msg['text']}")
        else:
            st.markdown(f"Assistant: {msg['text']}")

with right:
    st.subheader("Microphone")
    st.caption("Browser-native recording path with always-listen workflow. Turn off in the sidebar if needed.")
    audio_clip = st.audio_input("Record voice")
    if audio_clip is not None:
        wav_bytes = audio_clip.getvalue()
        st.audio(wav_bytes, format="audio/wav")
        audio_sig = _last_audio_signature(wav_bytes)
        auto_send = st.session_state.mic_enabled and audio_sig != st.session_state.last_audio_sig

        if auto_send:
            st.session_state.last_audio_sig = audio_sig
            data, code = _api_post(
                "/process",
                {
                    "audio_base64": base64.b64encode(wav_bytes).decode("ascii"),
                    "mode": mode,
                    "client": "streamlit-main",
                    "metadata": {
                        "source": "streamlit_audio_input",
                        "always_listen": st.session_state.wakeword_required,
                    },
                },
            )
            _render_voice_result(data, code)

        if st.button("Send Audio", use_container_width=True, disabled=st.session_state.mic_enabled):
            data, code = _api_post(
                "/process",
                {
                    "audio_base64": base64.b64encode(wav_bytes).decode("ascii"),
                    "mode": mode,
                    "client": "streamlit-main",
                    "metadata": {"source": "streamlit_audio_input"},
                },
            )
            _render_voice_result(data, code)

    if st.session_state.mic_enabled:
        st.subheader("Continuous Mic (WebRTC)")
        if WEBRTC_AVAILABLE:
            st.caption("Click Start once, then the app will continuously stream mic chunks for wake-word-gated processing.")
            webrtc_ctx = webrtc_streamer(
                key="continuous-wakeword-listener",
                mode=WebRtcMode.SENDONLY,
                media_stream_constraints={"video": False, "audio": True},
                async_processing=True,
                desired_playing_state=True,
                # Larger receiver queue helps avoid overflow when network/API latency spikes.
                audio_receiver_size=8192,
            )

            if webrtc_ctx and webrtc_ctx.state.playing and webrtc_ctx.audio_receiver:
                frames = []
                dropped_frames = 0

                # Drain the receiver quickly to avoid queue overflow under load.
                while True:
                    try:
                        batch = webrtc_ctx.audio_receiver.get_frames(timeout=0.02)
                    except queue.Empty:
                        break

                    if not batch:
                        break

                    frames.extend(batch)
                    # Keep only the most recent frames if backlog spikes.
                    if len(frames) > 200:
                        dropped_frames += len(frames) - 120
                        frames = frames[-120:]

                if dropped_frames:
                    st.caption(f"Dropped stale frames: {dropped_frames}")

                if frames:
                    chunk_parts: list[bytes] = []
                    sample_rate = st.session_state.webrtc_sample_rate
                    for frame in frames:
                        arr = frame.to_ndarray()
                        if arr.ndim == 2:
                            mono = arr.mean(axis=0)
                        else:
                            mono = arr

                        if np.issubdtype(mono.dtype, np.floating):
                            mono = (mono * 32767.0).clip(-32768, 32767).astype(np.int16)
                        else:
                            mono = mono.astype(np.int16, copy=False)

                        chunk_parts.append(mono.tobytes())
                        if frame.sample_rate:
                            sample_rate = int(frame.sample_rate)

                    st.session_state.webrtc_sample_rate = sample_rate
                    st.session_state.webrtc_pcm_buffer += b"".join(chunk_parts)

                pcm_buffer = st.session_state.webrtc_pcm_buffer
                sr = int(st.session_state.webrtc_sample_rate)
                if pcm_buffer and sr > 0:
                    duration = len(pcm_buffer) / float(2 * sr)
                    st.caption(f"Continuous buffer: {duration:.1f}s")

                    # Use larger chunks to reduce API request rate and improve wake phrase detection.
                    if duration >= 2.4:
                        wav_bytes = _pcm16_mono_to_wav_bytes(pcm_buffer, sr)
                        sig = _last_audio_signature(wav_bytes)
                        if sig != st.session_state.last_audio_sig:
                            st.session_state.last_audio_sig = sig

                            # Bounded queue provides backpressure when API latency spikes.
                            max_tasks = 8
                            if len(st.session_state.webrtc_audio_tasks) >= max_tasks:
                                st.session_state.webrtc_audio_tasks = st.session_state.webrtc_audio_tasks[-(max_tasks - 1) :]
                                st.session_state.webrtc_dropped_tasks += 1

                            st.session_state.webrtc_audio_tasks.append(
                                {
                                    "audio_base64": base64.b64encode(wav_bytes).decode("ascii"),
                                    "mode": mode,
                                    "client": "streamlit-main",
                                    "metadata": {
                                        "source": "streamlit_webrtc",
                                        "always_listen": st.session_state.wakeword_required,
                                    },
                                }
                            )

                        st.session_state.webrtc_pcm_buffer = b""

                if st.session_state.webrtc_dropped_tasks:
                    st.caption(f"Dropped queued chunks: {st.session_state.webrtc_dropped_tasks}")

                # Process only one queued chunk per rerun to keep frame intake responsive.
                if st.session_state.webrtc_audio_tasks:
                    payload = st.session_state.webrtc_audio_tasks.pop(0)
                    data, code = _api_post("/process", payload, timeout=4.0)
                    _render_voice_result(data, code)
            else:
                st.info("Press Start above to begin continuous listening.")
        else:
            st.warning("Continuous WebRTC mode needs streamlit-webrtc. Install dependencies and restart.")

    st.subheader("Navigation")
    destination = st.text_input("Destination", value="Library")
    if st.button("Start Navigation", use_container_width=True):
        nav_data, nav_code = _api_post("/navigation/start", {"destination": destination})
        if nav_code != 200:
            st.error(f"Navigation failed ({nav_code}): {nav_data.get('detail', nav_data)}")
        else:
            st.success("Navigation started")
            st.json(nav_data)
