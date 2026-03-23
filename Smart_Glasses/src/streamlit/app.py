import streamlit as st
import requests
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, AudioProcessorBase

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Camera MCP Interface", layout="wide")

api_key = "http://localhost:8000/run"  # MCP Server URL

st.text_area("✍️ Write command", key="text_input")

if st.button("Send Text", key="send_text"):
    text = st.session_state["text_input"]

    if text.strip():
        with st.spinner("Running LLM..."):
            r = requests.post(api_key, json={"text": text}, timeout=300)
            result = r.json()["response"]

        st.success("LLM Response:")
        st.write(result)

    
# ----------------------------
# VIDEO PROCESSOR
# ----------------------------
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return frame.from_ndarray(img, format="bgr24")
    
# images
class ImageProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return frame.from_ndarray(img, format="bgr24")

# ----------------------------
# AUDIO PROCESSOR
# ----------------------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = []

    def recv(self, frame):
        audio = frame.to_ndarray()
        self.audio_buffer.append(audio)
        return frame

# ----------------------------
# UI
# ----------------------------
st.title("📱 Live Camera + MCP Controls")

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

    # -------- WRITE INPUT --------
    text_input = st.text_area("✍️ Write command")

    if st.button("Send Text"):
        if text_input.strip():
            st.success("Text captured")
            st.session_state["last_text"] = text_input

            # SEND TO MCP (explained below)
            # requests.post(MCP_SERVER_URL, json={"type": "text", "data": text_input})

    # -------- SPEAK INPUT --------
    if st.button("🎤 Speak"):
        if webrtc_ctx.audio_processor:
            audio_data = webrtc_ctx.audio_processor.audio_buffer
            st.success(f"Captured {len(audio_data)} audio frames")

            # SEND TO MCP (explained below)
            # requests.post(MCP_SERVER_URL, files={"audio": audio_bytes})

# ----------------------------
# DEBUG VIEW
# ----------------------------
with st.expander("Debug"):
    st.write("Last text:", st.session_state.get("last_text"))
