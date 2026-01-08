"""Simple Voice Assistant for Smart Glasses."""
import streamlit as st
import requests
import numpy as np
import base64
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from config.settings import API_URL

# Page config
st.set_page_config(page_title="Voice Assistant", page_icon="🎤", layout="centered")

# Initialize session state
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = []
if "is_recording_audio" not in st.session_state:
    st.session_state.is_recording_audio = False
if "recording_start_frame" not in st.session_state:
    st.session_state.recording_start_frame = 0

# Audio processor
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        self.audio_buffer = []
        self.frame_count = 0

    def recv(self, frame):
        audio = frame.to_ndarray()
        self.frame_count += 1
        self.audio_buffer.append((self.frame_count, audio))
        return frame

    def get_audio_since(self, start_frame):
        return [audio for frame_num, audio in self.audio_buffer if frame_num >= start_frame]

    def clear_buffer(self):
        self.audio_buffer = []
        self.frame_count = 0

# UI
st.title("🎤 Voice Assistant")

# Connection check
try:
    response = requests.get(f"{API_URL}/", timeout=2)
    if response.status_code != 200:
        raise Exception()
except:
    st.error("❌ AI Assistant not connected")
    st.info("Start server: `python start_gateway.py`")
    st.stop()

st.success("✅ Connected to AI Assistant")

# Response mode
mode = st.radio("Response Style", ["Quick", "Detailed"], horizontal=True)

st.divider()

# WebRTC audio
webrtc_ctx = webrtc_streamer(
    key="audio",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={
        "video": False,
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "sampleRate": 16000
        }
    },
    async_processing=True
)

# Main interface
st.header("🎙️ Speak Your Command")

if webrtc_ctx.audio_processor:
    if not st.session_state.is_recording_audio:
        # Record button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎙️ **TAP TO RECORD**", type="primary", use_container_width=True, height=70):
                st.session_state.is_recording_audio = True
                st.session_state.recording_start_frame = webrtc_ctx.audio_processor.frame_count
                webrtc_ctx.audio_processor.clear_buffer()
                st.session_state.audio_buffer = []
                st.rerun()
    else:
        # Recording active
        current_frames = webrtc_ctx.audio_processor.frame_count - st.session_state.recording_start_frame
        duration_seconds = (current_frames * 1024) / 44100

        st.error(f"🔴 **RECORDING** - {duration_seconds:.1f}s")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⏹️ **STOP & SEND**", type="primary", use_container_width=True, height=70):
                # Capture audio
                captured_audio = webrtc_ctx.audio_processor.get_audio_since(
                    st.session_state.recording_start_frame
                )

                if captured_audio:
                    st.session_state.audio_buffer = captured_audio
                    st.session_state.is_recording_audio = False

                    with st.spinner("🎯 Processing your voice command..."):
                        send_to_ai()
                else:
                    st.warning("⚠️ No audio captured. Try again.")
                    st.session_state.is_recording_audio = False
                    st.session_state.audio_buffer = []
                    st.rerun()
else:
    st.warning("🎤 Please allow microphone access")

# Optional text input
with st.expander("📝 Add Text Context (Optional)"):
    text_input = st.text_input("Additional context", placeholder="Any extra notes...")

# Manual send button
has_audio = len(st.session_state.audio_buffer) > 0 and not st.session_state.is_recording_audio
if has_audio:
    if st.button("🚀 **Send Audio Again**", type="secondary"):
        with st.spinner("🎯 Processing..."):
            send_to_ai()

def send_to_ai():
    """Send audio and text to AI assistant."""
    try:
        # Prepare request data
        request_data = {"mode": mode.lower()}

        # Add text if provided
        text_input = st.session_state.get('text_input', '')
        if text_input and text_input.strip():
            request_data["text"] = text_input.strip()

        # Process audio
        if st.session_state.audio_buffer:
            # Combine all audio frames
            audio_arrays = [audio for _, audio in st.session_state.audio_buffer]
            if audio_arrays:
                combined_audio = np.concatenate(audio_arrays, axis=0)

                # Ensure proper format
                if combined_audio.dtype != np.float32:
                    combined_audio = combined_audio.astype(np.float32)

                # Convert to base64
                audio_bytes = combined_audio.tobytes()
                request_data["audio"] = base64.b64encode(audio_bytes).decode("utf-8")
                request_data["audio_dtype"] = "float32"

        # Send request
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=300)

        if response.status_code == 200:
            result = response.json()["response"]
            st.success("✅ Response received!")
            st.write("**🤖 AI Response:**")
            st.write(result)

            # Clear audio buffer
            st.session_state.audio_buffer = []
            if webrtc_ctx.audio_processor:
                webrtc_ctx.audio_processor.clear_buffer()
        else:
            st.error(f"❌ Error: {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to AI assistant")
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
