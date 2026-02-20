import streamlit as st
import requests
import numpy as np
import pygame
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, AudioProcessorBase

from tools.speech.tts import stop_tts


# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Camera MCP Interface", layout="wide")

api_key = "http://localhost:8000/run"


# ===============================
# VIDEO PROCESSOR
# ===============================
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return frame.from_ndarray(img, format="bgr24")


# ===============================
# AUDIO PROCESSOR (INTERRUPT LOGIC)
# ===============================
class AudioProcessor(AudioProcessorBase):
    def recv(self, frame):
        audio = frame.to_ndarray()

        # نحسب مستوى الصوت
        volume = np.abs(audio).mean()

        # لو Nova شغالة وإنتي بدأتي تتكلمي
        if pygame.mixer.get_init():
            if pygame.mixer.music.get_busy() and volume > 0.02:
                print(" User interrupted Nova")
                stop_tts()

        return frame


# ===============================
# UI
# ===============================
st.title(" Live Camera + MCP Controls")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Camera Feed")

    webrtc_ctx = webrtc_streamer(
        key="camera",
        video_processor_factory=VideoProcessor,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={
            "video": True,
            "audio": True
        },
        async_processing=True
    )

with col2:
    st.subheader("Controls")

    text_input = st.text_area(" Write command")

    if st.button("Send Text"):
        if text_input.strip():
            with st.spinner("Running LLM..."):
                r = requests.post(api_key, json={"text": text_input}, timeout=300)
                result = r.json()["response"]

            st.success("LLM Response:")
            st.write(result)
