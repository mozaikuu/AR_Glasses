"""Simple Voice Assistant for Smart Glasses."""

import streamlit as st

import requests

import numpy as np

import base64

# Simple pyaudio-based recording

from config.settings import API_URL



# Page config

st.set_page_config(page_title="Voice Assistant", page_icon="🎤", layout="centered")



# Initialize session state

if "captured_audio" not in st.session_state:

    st.session_state.captured_audio = None










def process_text_only(text):
    """Process text-only request and send to AI."""
    try:
        # Prepare request data
        request_data = {
            "mode": st.session_state.get('current_mode', 'quick'),
            "text": text
        }

        # Send request
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=300)

        if response.status_code == 200:
            response_data = response.json()
            result = response_data["response"]
            transcription = response_data.get("transcription")

            st.success("✅ Text request processed!")

            # Show transcription if available (though unlikely for text-only)
            if transcription and transcription != "[Audio transcription failed]":
                st.write("**🎤 Context:**")
                st.info(f'"{text}"')
                st.divider()

            st.write("**🤖 AI Response:**")
            st.write(result)

        else:
            st.error(f"❌ Processing failed: {response.status_code}")
            print(f"Error response: {response.text}", file=__import__('sys').stderr)

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to AI assistant")
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        print(f"Processing error: {e}", file=__import__('sys').stderr)


def record_and_process_audio():
    """Record audio using pyaudio and process it."""
    try:
        import pyaudio
        import numpy as np

        # Audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = 3

        # Initialize pyaudio
        p = pyaudio.PyAudio()

        # Try different devices if needed
        device_index = None
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels', 0) > 0:
                device_index = i
                print(f"Using audio device: {device_info.get('name')}", file=__import__('sys').stderr)
                break

        if device_index is None:
            st.error("❌ No microphone found!")
            return

        # Open audio stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )

        st.info("🎤 Recording for 3 seconds...")

        frames = []

        # Record audio
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        st.success("✅ Recording complete!")

        # Stop and close stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Convert to numpy array
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_array = audio_array.astype(np.float32) / 32767.0  # Normalize to [-1, 1]

        print(f"Recorded audio: {len(audio_array)} samples, range: [{audio_array.min():.3f}, {audio_array.max():.3f}]", file=__import__('sys').stderr)

        # Process with AI
        with st.spinner("🎯 Transcribing and processing..."):
            process_captured_audio(audio_array)

    except Exception as e:
        st.error(f"❌ Recording failed: {str(e)}")
        print(f"Recording error: {e}", file=__import__('sys').stderr)


def process_captured_audio(audio_data):
    """Process captured audio data and send to AI."""
    try:
        # Prepare request data
        request_data = {"mode": st.session_state.get('current_mode', 'quick')}

        # Add text if provided
        text_input_val = st.session_state.get('text_input', '')
        if text_input_val and text_input_val.strip():
            request_data["text"] = text_input_val.strip()

        # Process audio
        if audio_data is not None and len(audio_data) > 0:
            # Ensure proper format and normalize to [-1, 1]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize to [-1, 1] range for Whisper
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            print(f"DEBUG: Audio range after normalization: [{audio_data.min():.3f}, {audio_data.max():.3f}]", file=__import__('sys').stderr)

            # Convert to base64
            audio_bytes = audio_data.tobytes()
            request_data["audio"] = base64.b64encode(audio_bytes).decode("utf-8")
            request_data["audio_dtype"] = "float32"

            print(f"🎵 Sending audio: {len(audio_data)} samples, {len(audio_bytes)} bytes", file=__import__('sys').stderr)

        # Send request
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=300)

        if response.status_code == 200:
            response_data = response.json()
            result = response_data["response"]
            transcription = response_data.get("transcription")

            st.success("✅ Voice command processed!")

            # Show transcription if available
            if transcription and transcription != "[Audio transcription failed]":
                st.write("**🎤 You said:**")
                st.info(f'"{transcription}"')
                st.divider()

            st.write("**🤖 AI Response:**")
            st.write(result)

            # Clear captured audio
            if 'captured_audio' in st.session_state:
                del st.session_state.captured_audio
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to AI assistant")
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        print(f"Processing error: {e}", file=__import__('sys').stderr)

# Simple audio recording section
st.subheader("🎤 Voice Recording")

st.markdown("**Click the button below to record audio**")

# Simple record button
if st.button("🎤 **RECORD AUDIO**", type="primary"):
    with st.spinner("🎯 Recording... (speak now, will stop automatically in 3 seconds)"):
        record_and_process_audio()

