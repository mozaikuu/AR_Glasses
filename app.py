"""Smart Glasses AI Assistant with Wake-Word Activation."""

import streamlit as st

import requests

import numpy as np

import base64

import time

import threading

# Wake-word system and AI processing

from config.settings import API_URL

from tools.wakeword.wakeword_system import create_wakeword_system, SystemState



# Page config

st.set_page_config(page_title="Voice Assistant", page_icon="🎤", layout="centered")



# Initialize session state

if "captured_audio" not in st.session_state:
    st.session_state.captured_audio = None

# Initialize wake-word system and event queue
if "wakeword_system" not in st.session_state:
    st.session_state.wakeword_system = create_wakeword_system()
    st.session_state.wakeword_initialized = False

if "wakeword_events" not in st.session_state:
    import queue
    st.session_state.wakeword_events = queue.Queue()

# Initialize wakeword results dictionary for shared state
if "wakeword_results" not in st.session_state:
    st.session_state.wakeword_results = {
        'wake_word_detected': False,
        'last_wake_word': None,
        'wake_confidence': 0.0,
        'wake_text': None,
        'command_received': False,
        'command_text': None,
        'system_state': 'idle',
        'last_update': 0
    }

# Initialize wake-word callbacks (thread-safe)
if not st.session_state.wakeword_initialized:
    wakeword_system = st.session_state.wakeword_system
    event_queue = st.session_state.wakeword_events

    def on_wake_word_detected(wake_word, confidence, text):
        """Handle wake word detection (thread-safe)"""
        event_queue.put({
            'type': 'wake_word_detected',
            'wake_word': wake_word,
            'confidence': confidence,
            'text': text
        })

    def on_command_received(command_text):
        """Handle command received after wake word (thread-safe)"""
        print(f"WAKEWORD CALLBACK: on_command_received('{command_text}')", file=__import__('sys').stderr)
        # Only use event queue for thread communication (thread-safe)
        event_queue.put({
            'type': 'command_received',
            'command_text': command_text
        })

    def on_state_changed(old_state, new_state):
        """Handle state changes (thread-safe)"""
        event_queue.put({
            'type': 'state_changed',
            'old_state': old_state,
            'new_state': new_state
        })

    wakeword_system.set_callbacks(
        wake_word_callback=on_wake_word_detected,
        command_callback=on_command_received,
        state_callback=on_state_changed
    )

    st.session_state.wakeword_initialized = True

def process_wakeword_command(command_text):
    """Process command received from wake-word system"""
    print(f"process_wakeword_command called with: '{command_text}'", file=__import__('sys').stderr)
    try:
        # Check if command text is empty or unintelligible
        if not command_text or not command_text.strip():
            print("Empty command text detected", file=__import__('sys').stderr)
            st.session_state.error_message = "❌ Sorry, I couldn't understand your command. Please try again."
            st.session_state.wakeword_system.return_to_idle()
            st.session_state.processing_command = False
            return

        print(f"Processing command: '{command_text.strip()}'", file=__import__('sys').stderr)

        # Create temporary audio data for processing (empty since we have text)
        # The backend will handle text-only processing
        request_data = {
            "mode": st.session_state.get('current_mode', 'quick'),
            "text": command_text.strip()
        }

        # Add any existing text context
        text_input_val = st.session_state.get('text_input', '')
        if text_input_val and text_input_val.strip():
            request_data["text"] = f"{text_input_val.strip()}. {command_text.strip()}"

        print(f"Sending request to AI: {request_data}", file=__import__('sys').stderr)
        st.session_state.processing_command = True

        # Send request
        print(f"Making HTTP request to {API_URL}/process", file=__import__('sys').stderr)
        try:
            response = requests.post(f"{API_URL}/process", json=request_data, timeout=30)
            print(f"HTTP request completed with status: {response.status_code}", file=__import__('sys').stderr)
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}", file=__import__('sys').stderr)
            st.session_state.error_message = f"❌ Failed to connect to AI service: {str(e)}"
            st.session_state.processing_command = False
            return

        print(f"AI response status: {response.status_code}", file=__import__('sys').stderr)

        if response.status_code == 200:
            response_data = response.json()
            result = response_data["response"]
            transcription = response_data.get("transcription", command_text)

            print(f"AI response: '{result}'", file=__import__('sys').stderr)

            st.session_state.ai_response = result
            st.session_state.transcription = transcription
            st.session_state.command_processed = True

            # Return wake-word system to idle
            st.session_state.wakeword_system.return_to_idle()

        else:
            error_msg = f"AI Error: {response.status_code} - {response.text}"
            print(f"Error: {error_msg}", file=__import__('sys').stderr)
            st.session_state.error_message = error_msg

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Cannot connect to AI assistant: {str(e)}"
        print(f"Connection error: {error_msg}", file=__import__('sys').stderr)
        st.session_state.error_message = f"❌ {error_msg}"
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        print(f"Wake-word processing error: {error_msg}", file=__import__('sys').stderr)
        st.session_state.error_message = f"❌ {error_msg}"
    finally:
        st.session_state.processing_command = False

# Process wake-word events (in main thread)
events_processed = 0
while not st.session_state.wakeword_events.empty():
    event = st.session_state.wakeword_events.get()
    events_processed += 1

    if event['type'] == 'wake_word_detected':
        st.session_state.wake_word_detected = True
        st.session_state.last_wake_word = event['wake_word']
        st.session_state.wake_confidence = event['confidence']
        st.session_state.wake_text = event['text']

    elif event['type'] == 'command_received':
        print(f"EVENT RECEIVED: command_received - '{event['command_text']}'", file=__import__('sys').stderr)
        st.session_state.command_received = True
        st.session_state.command_text = event['command_text']
        # Process the command automatically
        print(f"About to call process_wakeword_command with: '{event['command_text']}'", file=__import__('sys').stderr)
        process_wakeword_command(event['command_text'])
        print(f"process_wakeword_command call completed", file=__import__('sys').stderr)

    elif event['type'] == 'state_changed':
        st.session_state.system_state = event['new_state']

# Use a counter to trigger UI updates when events are processed
if 'wakeword_event_counter' not in st.session_state:
    st.session_state.wakeword_event_counter = 0

if events_processed > 0:
    st.session_state.wakeword_event_counter += events_processed
    print(f"Processed {events_processed} wakeword events, counter now {st.session_state.wakeword_event_counter}", file=__import__('sys').stderr)

# Time-based trigger for periodic updates (every 1.5 seconds)
current_time = __import__('time').time()
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = current_time

time_since_last_update = current_time - st.session_state.last_update_time
if time_since_last_update > 1.5:
    st.session_state.last_update_time = current_time
    # Force a minor UI update to check for wake-word events
    if 'update_trigger' not in st.session_state:
        st.session_state.update_trigger = 0
    st.session_state.update_trigger += 1
    print(f"Periodic update trigger: {st.session_state.update_trigger} (every {time_since_last_update:.1f}s)", file=__import__('sys').stderr)

# Auto-start wake-word system if not running
if not st.session_state.wakeword_system.is_running and st.session_state.wakeword_initialized:
    try:
        st.session_state.wakeword_system.start()
    except Exception as e:
        print(f"Failed to auto-start wake-word system: {e}", file=__import__('sys').stderr)










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

            # Check if transcription indicates unclear audio
            if transcription == "[Audio transcription failed]" or "[Voice input: (unclear audio)]" in result:
                st.error("❌ Sorry, I couldn't understand the audio. Please try speaking more clearly or check your microphone.")
                return

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

# Wake-word activation section
st.subheader("🎯 Wake-Word Voice Assistant")

# Wake-word system controls
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.session_state.wakeword_system.is_idle():
        st.markdown("**🎤 Status: Listening for wake words**")
        st.info("Say **'Nova'** or **'Hey Nova'** to activate")
    elif st.session_state.wakeword_system.is_active():
        st.markdown("**🎯 Status: Listening for command**")
        st.warning("Speak your command now...")
    elif st.session_state.wakeword_system.is_processing():
        st.markdown("**⚙️ Status: Processing command**")
        st.info("AI is thinking...")

    # Show auto-update indicator
    update_count = st.session_state.get('update_trigger', 0)
    if update_count > 0:
        st.caption(f"🔄 Auto-checking for updates (#{update_count})")

with col2:
    if not st.session_state.wakeword_system.is_running:
        if st.button("▶️ **START**", type="primary"):
            st.session_state.wakeword_system.start()
            st.rerun()
    else:
        if st.button("⏹️ **STOP**", type="secondary"):
            st.session_state.wakeword_system.stop()
            st.rerun()

with col3:
    # Manual recording fallback
    if st.button("🎤 **RECORD**", help="Manual recording (fallback)"):
        with st.spinner("🎯 Recording... (speak now, will stop automatically in 3 seconds)"):
            record_and_process_audio()

# Wake-word detection feedback
if st.session_state.get('wake_word_detected', False):
    wake_word = st.session_state.get('last_wake_word', 'unknown')
    confidence = st.session_state.get('wake_confidence', 0)
    st.success(f"🔔 Wake word '**{wake_word}**' detected! (confidence: {confidence:.1f})")

    # Clear the detection flag
    st.session_state.wake_word_detected = False

# Command processing feedback
if st.session_state.get('command_received', False):
    command = st.session_state.get('command_text', '')
    st.success(f"🎤 I heard: **'{command}'**")
    st.info("🤖 Processing your command...")

    # Clear the received flag
    st.session_state.command_received = False

# AI Response display
if st.session_state.get('command_processed', False):
    transcription = st.session_state.get('transcription', '')
    ai_response = st.session_state.get('ai_response', '')

    st.success("✅ Command processed!")

    if transcription:
        st.write("**🎤 You said:**")
        st.info(f'"{transcription}"')
        st.divider()

    if ai_response:
        st.write("**🤖 AI Response:**")
        st.write(ai_response)

    # Clear the processed flag
    st.session_state.command_processed = False

# Error display
if st.session_state.get('error_message'):
    st.error(st.session_state.error_message)
    st.session_state.error_message = None

# Hidden element to trigger reruns on wake-word events
st.empty()  # This will trigger reruns when the counter changes
if st.session_state.get('wakeword_event_counter', 0) > 0:
    # This ensures the UI updates when wake-word events occur
    pass

# Show update trigger for debugging (can be removed later)
update_trigger = st.session_state.get('update_trigger', 0)
# st.caption(f"🔄 Auto-update: {update_trigger}")  # Uncomment for debugging
