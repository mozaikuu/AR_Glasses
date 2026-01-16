"""Simple Streamlit app for Smart Glasses Voice Commands."""
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


# ==================== AUDIO PROCESSOR ====================
class AudioProcessor(AudioProcessorBase):
    """Process audio from WebRTC stream."""
    def __init__(self):
        super().__init__()
        self.audio_buffer = []
        self.frame_count = 0
    
    def recv(self, frame):
        """Receive and buffer audio frames."""
        audio = frame.to_ndarray()
        self.frame_count += 1
        # Store frame count with audio for tracking
        self.audio_buffer.append((self.frame_count, audio))
        # No size limit - buffer continuously until cleared
        return frame
    
    def get_audio_since(self, start_frame):
        """Get audio frames since a specific frame number."""
        return [audio for frame_num, audio in self.audio_buffer if frame_num >= start_frame]
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        self.audio_buffer = []
        self.frame_count = 0


# ==================== UI ====================
st.title("🎤 Smart Glasses Voice Assistant")

# Check gateway status (simple)
try:
    response = requests.get(f"{API_URL}/", timeout=2)
    if response.status_code == 200:
        st.success("✅ Connected to AI Assistant")
    else:
        st.warning("⚠️ AI Assistant may be busy")
except:
    st.error("❌ Cannot connect to AI Assistant")
    st.info("Start the gateway server first: `python start_gateway.py`")
    st.stop()

st.divider()

# Mode selection (simplified)
mode = st.radio("Response Mode", ["quick", "detailed"], horizontal=True,
                help="Quick: Fast responses | Detailed: More thorough analysis")

st.divider()

# WebRTC streamer for audio (improved)
webrtc_ctx = webrtc_streamer(
    key="audio",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={
        "video": False,
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True
        }
    },
    async_processing=True
)

# Main recording interface
st.header("🎙️ Voice Commands")

# Recording status
if webrtc_ctx.audio_processor:
        if not st.session_state.is_recording_audio:
            if st.button("🎙️ Start Recording", key="start_recording"):
                st.session_state.is_recording_audio = True
                st.session_state.recording_start_frame = webrtc_ctx.audio_processor.frame_count
                # Clear the processor buffer to start fresh
                webrtc_ctx.audio_processor.clear_buffer()
                st.session_state.audio_buffer = []  # Clear session state buffer
                st.success("🎤 Recording started! Speak now, then click 'Stop Recording' to send.")
        else:
            if st.button("⏹️ Stop Recording", key="stop_recording"):
                # Capture ALL audio from when recording started
                captured_audio = webrtc_ctx.audio_processor.get_audio_since(
                    st.session_state.recording_start_frame
                )
                if captured_audio:
                    st.session_state.audio_buffer = captured_audio
                    # Calculate approximate duration (44.1kHz sample rate)
                    total_samples = sum(len(audio) for audio in captured_audio)
                    duration_seconds = total_samples / 44100
                    st.success(f"🎤 Recording stopped! Captured {len(captured_audio)} audio frames ({duration_seconds:.1f}s, {total_samples:,} samples)")
                else:
                    st.warning("No audio captured. Make sure microphone is active.")
                    st.session_state.audio_buffer = []
                st.session_state.is_recording_audio = False
        
        # Show recording status
        if st.session_state.is_recording_audio:
            # Calculate current recording duration
            if webrtc_ctx.audio_processor:
                current_frames = webrtc_ctx.audio_processor.frame_count - st.session_state.recording_start_frame
                duration_seconds = (current_frames * 1024) / 44100  # Approximate duration
                st.info(f"🔴 Recording... ({duration_seconds:.1f}s) Click 'Stop Recording' when done.")
            else:
                st.info("🔴 Recording... Click 'Stop Recording' when done.")
        elif len(st.session_state.audio_buffer) > 0:
            # Calculate total duration of captured audio
            total_samples = sum(len(audio) for audio in st.session_state.audio_buffer)
            duration_seconds = total_samples / 44100
            st.info(f"✅ Audio ready: {len(st.session_state.audio_buffer)} frames ({duration_seconds:.1f}s, {total_samples:,} samples)")

with col2:
    st.subheader("📝 Text Input")
    text_input = st.text_area("Optional Context", placeholder="Add text context if needed...", height=100)

# Send button
st.divider()
if st.button("🚀 Send Voice Request", type="primary", use_container_width=True):
        # Prepare audio request
        has_text = bool(text_input.strip())
        has_audio = len(st.session_state.audio_buffer) > 0

        if not (has_text or has_audio):
            st.error("Please provide voice recording or text input.")
        else:
            with st.spinner("Processing request..."):
                try:
                    # Prepare request data
                    request_data = {
                        "mode": mode,
                        "text": text_input if has_text else None,
                    }

                    # Add audio if captured
                    if has_audio:
                        try:
                            # st.session_state.audio_buffer contains tuples of (frame_num, audio_array)
                            # Extract just the audio arrays
                            if st.session_state.audio_buffer and len(st.session_state.audio_buffer) > 0:
                                # Check if it's tuples or just arrays
                                if isinstance(st.session_state.audio_buffer[0], tuple):
                                    audio_arrays = [audio for _, audio in st.session_state.audio_buffer]
                                else:
                                    audio_arrays = st.session_state.audio_buffer
                                
                                if len(audio_arrays) > 0:
                                    # WebRTC audio frames are typically float32 arrays in range [-1, 1]
                                    # Concatenate all frames
                                    audio_array = np.concatenate(audio_arrays, axis=0)
                                    # Ensure it's float32 and in the correct range
                                    if audio_array.dtype != np.float32:
                                        audio_array = audio_array.astype(np.float32)
                                    # Normalize to [-1, 1] if needed (should already be normalized from WebRTC)
                                    if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                                        audio_array = np.clip(audio_array, -1.0, 1.0)
                                    
                                    # No size limit - send all recorded audio
                                    
                                    # Convert to bytes for transmission
                                    audio_bytes = audio_array.tobytes()
                                    request_data["audio"] = base64.b64encode(audio_bytes).decode("utf-8")
                                    request_data["audio_dtype"] = "float32"  # Pass dtype info
                                    duration_seconds = len(audio_array) / 44100
                                    st.info(f"📤 Sending {len(audio_array):,} audio samples ({duration_seconds:.1f}s, {len(audio_bytes) / 1024:.1f} KB)")
                                else:
                                    has_audio = False
                                    st.warning("No audio data in buffer")
                            else:
                                has_audio = False
                        except Exception as audio_error:
                            st.warning(f"⚠️ Error processing audio: {audio_error}. Skipping audio input.")
                            has_audio = False
                    
                    # Send request
                    response = requests.post(
                        f"{API_URL}/process",
                        json=request_data,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        result = response.json()["response"]
                        st.success("✅ Response received!")
                        st.write("**Agent Response:**")
                        st.write(result)

                        # Clear audio buffer after successful send
                        if has_audio:
                            st.session_state.audio_buffer = []
                            if webrtc_ctx.audio_processor:
                                webrtc_ctx.audio_processor.clear_buffer()
                            st.info("🔄 Audio buffer cleared. Ready for new recording.")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ **Connection Error**: Cannot connect to gateway server at {API_URL}")
                    st.info("💡 **Solution**: Make sure the gateway server is running.")
                    with st.expander("How to start the gateway"):
                        st.code("""
# 1. Activate virtual environment:
.venv\\Scripts\\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Start gateway:
python start_gateway.py
# or use: start_gateway.bat (Windows) / start_gateway.sh (Linux/Mac)
                        """, language="bash")
                except requests.exceptions.Timeout:
                    st.error("⏱️ **Timeout Error**: Request took too long (>5 minutes)")
                    st.info("The request may still be processing. Try again or check the gateway logs.")
                except Exception as e:
                    error_msg = str(e)
                    if "10061" in error_msg or "actively refused" in error_msg.lower():
                        st.error(f"❌ **Connection Refused**: Gateway server is not running at {API_URL}")
                        st.info("💡 **Solution**: Start the gateway server.")
                        with st.expander("How to start"):
                            st.code("""
# 1. Activate virtual environment:
.venv\\Scripts\\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Start gateway:
python start_gateway.py
# or use: start_gateway.bat (Windows) / start_gateway.sh (Linux/Mac)
                            """, language="bash")
                    else:
                        st.error(f"❌ **Error processing request**: {error_msg}")

# Debug section
with st.expander("🔍 Debug Info"):
    st.write("**Session State:**")
    st.json({
        "audio_frames": len(st.session_state.audio_buffer),
        "is_recording": st.session_state.is_recording_audio,
        "text_input": text_input[:50] if text_input else None,
        "mode": mode
    })

