from __future__ import annotations

import io
import math
import wave
from datetime import datetime
from pathlib import Path

import streamlit as st


def _pcm_rms(frames: bytes, sample_width: int) -> float:
    """Compute RMS from PCM bytes without audioop (removed in newer Python)."""
    if not frames or sample_width <= 0:
        return 0.0

    total = 0.0
    count = 0

    if sample_width == 1:
        # 8-bit PCM is typically unsigned.
        for b in frames:
            v = float(b - 128)
            total += v * v
            count += 1
    else:
        for i in range(0, len(frames) - sample_width + 1, sample_width):
            chunk = frames[i : i + sample_width]
            v = float(int.from_bytes(chunk, byteorder="little", signed=True))
            total += v * v
            count += 1

    if count == 0:
        return 0.0
    return math.sqrt(total / count)


st.set_page_config(page_title="Mic Test", layout="wide")
st.title("Microphone Test (Streamlit)")
st.caption("Use this page to verify browser microphone capture outside Flask voice logic.")

st.markdown(
    "Run with: `uv run streamlit run tests/streamlit_mic_test.py --server.port 8502`"
)

left, right = st.columns([2, 1])

with right:
    st.subheader("Environment")
    st.write(f"Python: {st.__version__}")
    st.info("If recording works here, your microphone path is healthy and Flask speech issues are browser speech-service related.")

with left:
    st.subheader("Record")
    audio_file = st.audio_input("Click to record from microphone")

    if audio_file is None:
        st.warning("No recording yet. Press the recorder and speak.")
    else:
        payload = audio_file.getvalue()
        st.success("Audio captured")
        st.audio(payload, format="audio/wav")

        try:
            with wave.open(io.BytesIO(payload), "rb") as wav_reader:
                channels = wav_reader.getnchannels()
                sample_width = wav_reader.getsampwidth()
                sample_rate = wav_reader.getframerate()
                frame_count = wav_reader.getnframes()
                duration_seconds = frame_count / float(sample_rate) if sample_rate else 0.0
                frames = wav_reader.readframes(frame_count)

            rms = _pcm_rms(frames, sample_width) if frames else 0.0

            st.subheader("Audio Stats")
            st.write(f"Channels: {channels}")
            st.write(f"Sample rate: {sample_rate} Hz")
            st.write(f"Sample width: {sample_width * 8} bits")
            st.write(f"Duration: {duration_seconds:.2f} s")
            st.write(f"RMS level: {rms:.2f}")

            if rms < 50:
                st.error("Very low signal detected. Check microphone level/mute settings.")
            elif rms < 250:
                st.warning("Low signal level. Speak closer or increase mic gain.")
            else:
                st.success("Signal level looks good.")

            if st.button("Save sample to assets/mic_samples"):
                output_dir = Path("assets/mic_samples")
                output_dir.mkdir(parents=True, exist_ok=True)
                name = datetime.now().strftime("mic_%Y%m%d_%H%M%S.wav")
                out_path = output_dir / name
                out_path.write_bytes(payload)
                st.success(f"Saved: {out_path.as_posix()}")
        except Exception as exc:
            st.exception(exc)
