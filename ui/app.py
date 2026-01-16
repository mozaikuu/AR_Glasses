"""Streamlit app for Smart Glasses with multimodal input support."""
import streamlit as st
import requests
import numpy as np
import base64
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, AudioProcessorBase
from config.settings import API_URL
from shared.utils import image_to_base64

# Page config
st.set_page_config(page_title="Smart Glasses Interface", layout="wide")

# Initialize session state
if "captured_frame" not in st.session_state:
    st.session_state.captured_frame = None
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = []
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "is_recording_audio" not in st.session_state:
    st.session_state.is_recording_audio = False
if "recording_start_frame" not in st.session_state:
    st.session_state.recording_start_frame = 0


# ==================== VIDEO PROCESSOR ====================
class VideoProcessor(VideoProcessorBase):
    """Process video frames from WebRTC stream."""
    def __init__(self):
        super().__init__()
        self.current_frame = None
    
    def recv(self, frame):
        """Receive and store current frame."""
        img = frame.to_ndarray(format="bgr24")
        self.current_frame = img
        return frame.from_ndarray(img, format="bgr24")


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
        # Only buffer if we're in recording mode
        # Store frame count with audio for tracking
        self.audio_buffer.append((self.frame_count, audio))
        # Keep only last 5 seconds of audio (approximately 220 frames at 44.1kHz)
        max_frames = 220
        if len(self.audio_buffer) > max_frames:
            self.audio_buffer = self.audio_buffer[-max_frames:]
        return frame
    
    def get_audio_since(self, start_frame):
        """Get audio frames since a specific frame number."""
        return [audio for frame_num, audio in self.audio_buffer if frame_num >= start_frame]
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        self.audio_buffer = []
        self.frame_count = 0


# ==================== UI ====================
st.title("🤖 Smart Glasses Interface")

# Mode selection and gateway status
col_mode, col_status, col_spacer = st.columns([1, 1, 3])
with col_mode:
    mode = st.selectbox("Mode", ["thinking", "quick"], help="Thinking mode loops until satisfied, quick mode is faster")
with col_status:
    # Check gateway status
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("🟢 Gateway Online")
        else:
            st.warning("🟡 Gateway Unstable")
    except (requests.exceptions.RequestException, Exception):
        st.error("🔴 Gateway Offline")
        with st.expander("How to start"):
            st.code("""
# Activate virtual environment first:
.venv\\Scripts\\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Then start gateway:
python start_gateway.py
# or use: start_gateway.bat (Windows)
            """, language="bash")

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Live Camera Feed")
    
    # WebRTC streamer
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
    
    # Capture frame button
    if webrtc_ctx.video_processor:
        if st.button("📸 Capture Frame", key="capture_frame"):
            if webrtc_ctx.video_processor.current_frame is not None:
                st.session_state.captured_frame = webrtc_ctx.video_processor.current_frame
                st.success("Frame captured!")
            else:
                st.warning("No frame available. Make sure camera is active.")
    
    # Show captured frame
    if st.session_state.captured_frame is not None:
        st.image(st.session_state.captured_frame, caption="Captured Frame", use_container_width=True)

with col2:
    st.subheader("🎛️ Controls")
    
    # Text input
    text_input = st.text_area("✍️ Text Input", placeholder="Type your question here...", height=100)
    
    # Audio controls
    st.write("🎤 Audio Input")
    if webrtc_ctx.audio_processor:
        if not st.session_state.is_recording_audio:
            if st.button("🎙️ Start Recording", key="start_recording"):
                st.session_state.is_recording_audio = True
                st.session_state.recording_start_frame = webrtc_ctx.audio_processor.frame_count
                st.session_state.audio_buffer = []  # Clear previous capture
                st.success("Recording started! Click 'Stop Recording' when done.")
        else:
            if st.button("⏹️ Stop Recording", key="stop_recording"):
                # Capture audio from when recording started
                captured_audio = webrtc_ctx.audio_processor.get_audio_since(
                    st.session_state.recording_start_frame
                )
                if captured_audio:
                    st.session_state.audio_buffer = captured_audio
                    st.success(f"Captured {len(captured_audio)} audio frames!")
                else:
                    st.warning("No audio captured. Make sure microphone is active.")
                st.session_state.is_recording_audio = False
        
        # Show recording status
        if st.session_state.is_recording_audio:
            st.info("🔴 Recording... Click 'Stop Recording' when done.")
        elif len(st.session_state.audio_buffer) > 0:
            st.info(f"✅ {len(st.session_state.audio_buffer)} audio frames ready to send")
    
    # Transcribed text display
    if st.session_state.transcribed_text:
        st.write("**Transcribed:**")
        st.write(st.session_state.transcribed_text)
    
    # Send button
    st.divider()
    if st.button("🚀 Send Request", type="primary", use_container_width=True):
        # Prepare multimodal request
        has_text = bool(text_input.strip())
        has_image = st.session_state.captured_frame is not None
        has_audio = len(st.session_state.audio_buffer) > 0
        
        if not (has_text or has_image or has_audio):
            st.error("Please provide at least one input: text, image, or audio.")
        else:
            with st.spinner("Processing request..."):
                try:
                    # Prepare request data
                    request_data = {
                        "mode": mode,
                        "text": text_input if has_text else None,
                    }
                    
                    # Add image if captured
                    if has_image:
                        img_base64 = image_to_base64(st.session_state.captured_frame)
                        request_data["image"] = img_base64
                    
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
                                    
                                    # Limit audio to reasonable size (max 10 seconds at 44.1kHz = 441000 samples)
                                    max_samples = 441000
                                    if len(audio_array) > max_samples:
                                        audio_array = audio_array[-max_samples:]
                                        st.warning(f"⚠️ Audio truncated to last 10 seconds ({len(audio_array)} samples)")
                                    
                                    # Convert to bytes for transmission
                                    audio_bytes = audio_array.tobytes()
                                    request_data["audio"] = base64.b64encode(audio_bytes).decode("utf-8")
                                    request_data["audio_dtype"] = "float32"  # Pass dtype info
                                    st.info(f"📤 Sending {len(audio_array)} audio samples ({len(audio_bytes) / 1024:.1f} KB)")
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
        "has_frame": st.session_state.captured_frame is not None,
        "audio_frames": len(st.session_state.audio_buffer),
        "transcribed": st.session_state.transcribed_text,
        "text_input": text_input[:50] if text_input else None
    })

