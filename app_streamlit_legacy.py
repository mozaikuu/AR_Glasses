"""Smart Glasses AI Assistant with Wake-Word Activation."""

import streamlit as st
import requests
import numpy as np
import base64
import time
import threading
# Wake-word system and AI processing
from config.settings import API_URL, WAKE_WORDS
from tools.wakeword.wakeword_system import create_wakeword_system, SystemState

def get_valid_audio_device_index():
    """Find a valid audio input device index."""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_index = None
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels', 0) > 0:
                device_index = i
                print(f"Found audio device: {device_info.get('name')}", file=__import__('sys').stderr)
                break
        p.terminate()
        return device_index
    except Exception as e:
        print(f"Error finding audio device: {e}", file=__import__('sys').stderr)
        return None

# Page config
st.set_page_config(
    page_title="Smart Glasses AI Assistant",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .response-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🎤 Smart Glasses AI Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your hands-free AI companion powered by voice commands</p>', unsafe_allow_html=True)



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

if "wakeword_recording_active" not in st.session_state:
    st.session_state.wakeword_recording_active = False

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
    
    # Check if command text is empty or unintelligible
    if not command_text or not command_text.strip():
        print("Empty command text detected", file=__import__('sys').stderr)
        st.session_state.error_message = "❌ Sorry, I couldn't understand your command. Please try again."
        st.session_state.wakeword_system.return_to_idle()
        st.session_state.processing_command = False
        return

    try:
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
        print(f"Request data: {request_data}", file=__import__('sys').stderr)
        try:
            response = requests.post(f"{API_URL}/process", json=request_data, timeout=60)
            print(f"HTTP request completed with status: {response.status_code}", file=__import__('sys').stderr)
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}", file=__import__('sys').stderr)
            st.session_state.error_message = f"❌ Failed to connect to AI service: {str(e)}"
            return

        print(f"AI response status: {response.status_code}", file=__import__('sys').stderr)
        if response.status_code != 200:
            print(f"Error response: {response.text}", file=__import__('sys').stderr)
            error_msg = f"AI Error: {response.status_code} - {response.text}"
            print(f"Error: {error_msg}", file=__import__('sys').stderr)
            st.session_state.error_message = error_msg

        elif response.status_code == 200:
            response_data = response.json()
            result = response_data["response"]
            transcription = response_data.get("transcription", command_text)

            print(f"AI response: '{result}'", file=__import__('sys').stderr)

            st.session_state.ai_response = result
            st.session_state.transcription = transcription
            st.session_state.command_processed = True

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        print(f"Wake-word processing error: {error_msg}", file=__import__('sys').stderr)
        st.session_state.error_message = f"❌ {error_msg}"
    finally:
        # Return wake-word system to idle regardless of outcome
        if st.session_state.wakeword_system:
            st.session_state.wakeword_system.return_to_idle()
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
        command_text = event.get('command_text', '').strip()
        
        if not command_text:
            print("WARNING: Empty command text received, skipping processing", file=__import__('sys').stderr)
            st.session_state.wakeword_system.return_to_idle()
            # Skip processing for empty commands
        else:
            st.session_state.command_received = True
            st.session_state.command_text = command_text
            # Set flag to prioritize wakeword over manual recording
            st.session_state.wakeword_recording_active = True
            
            # Process the command automatically
            print(f"About to call process_wakeword_command with: '{command_text}'", file=__import__('sys').stderr)
            try:
                process_wakeword_command(command_text)
                print(f"process_wakeword_command call completed successfully", file=__import__('sys').stderr)
            except Exception as e:
                print(f"ERROR in process_wakeword_command: {e}", file=__import__('sys').stderr)
                import traceback
                traceback.print_exc(file=__import__('sys').stderr)
                st.session_state.error_message = f"Error processing command: {str(e)}"
                st.session_state.wakeword_system.return_to_idle()
            
            # Clear the priority flag after processing
            st.session_state.wakeword_recording_active = False

    elif event['type'] == 'state_changed':
        st.session_state.system_state = event['new_state']

# Use a counter to trigger UI updates when events are processed
if 'wakeword_event_counter' not in st.session_state:
    st.session_state.wakeword_event_counter = 0

if events_processed > 0:
    st.session_state.wakeword_event_counter += events_processed
    print(f"Processed {events_processed} wakeword events, counter now {st.session_state.wakeword_event_counter}", file=__import__('sys').stderr)

# Auto-refresh loop to process background events
# This keeps the script running/refreshing when the wakeword system is active
if st.session_state.wakeword_system.is_running:
    # Sleep briefly to avoid high CPU usage
    time.sleep(1)
    # Rerun the script to process any new events from the queue
    st.rerun()

# Auto-start wake-word system if not running
if not st.session_state.wakeword_system.is_running and st.session_state.wakeword_initialized:
    try:
        st.session_state.wakeword_system.start()
        print(f"Wake-word system auto-started successfully", file=__import__('sys').stderr)
    except Exception as e:
        print(f"Failed to auto-start wake-word system: {e}", file=__import__('sys').stderr)
        import traceback
        traceback.print_exc(file=__import__('sys').stderr)

# Verify wake-word system is running
if st.session_state.wakeword_initialized:
    if not st.session_state.wakeword_system.is_running:
        print(f"WARNING: Wake-word system is initialized but not running!", file=__import__('sys').stderr)
    else:
        print(f"Wake-word system is running. State: {st.session_state.wakeword_system.state}", file=__import__('sys').stderr)










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

            st.markdown('<div class="response-card">', unsafe_allow_html=True)
            
            st.markdown("**⌨️ Your Question:**")
            st.info(f'"{text}"')
            st.markdown("---")
            
            st.markdown("**🤖 AI Assistant:**")
            st.markdown(f'<div style="font-size: 1.1rem; line-height: 1.6; color: #333;">{result}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

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
        RECORD_SECONDS = 5

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

        st.info("🎤 Recording for 5 seconds...")

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
    
    finally:
        # Resume wakeword system
        if 'wakeword_system' in st.session_state and st.session_state.wakeword_system.is_running:
            print("Resuming wakeword system...", file=__import__('sys').stderr)
            st.session_state.wakeword_system.resume()


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

            print(f"[AUDIO] Sending audio: {len(audio_data)} samples, {len(audio_bytes)} bytes", file=__import__('sys').stderr)

        # Send request
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=300)

        if response.status_code == 200:
            response_data = response.json()
            result = response_data["response"]
            transcription = response_data.get("transcription")

            # Check if transcription indicates unclear audio
            if transcription == "[Audio transcription failed]" or "[Voice input: (unclear audio)]" in result:
                st.error("❌ **Sorry, I couldn't understand the audio.** Please try speaking more clearly or check your microphone.")
                return

            st.markdown('<div class="response-card">', unsafe_allow_html=True)
            
            # Show transcription if available
            if transcription and transcription != "[Audio transcription failed]":
                st.markdown("**🎤 You said:**")
                st.info(f'"{transcription}"')
                st.markdown("---")
            
            st.markdown("**🤖 AI Assistant:**")
            st.markdown(f'<div style="font-size: 1.1rem; line-height: 1.6; color: #333;">{result}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

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

# Main content area
st.markdown("---")

# Wake-word activation section
st.markdown("### 🎯 Voice Assistant Controls")

# Create main control panel
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # Status display card
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    
    if st.session_state.wakeword_system.is_idle():
        st.markdown("**🟢 Status: Ready & Listening**")
        words = ", ".join([f"**'{w}'**" for w in WAKE_WORDS])
        st.info(f"👂 The system is listening for wake words. Say {words} to activate.")
    elif st.session_state.wakeword_system.is_active():
        st.markdown("**🟡 Status: Listening for Command**")
        st.warning("🎤 Speak your command now. The system is recording...")
    elif st.session_state.wakeword_system.is_processing():
        st.markdown("**🔵 Status: Processing**")
        st.info("🤖 AI is thinking and processing your request...")
    
    st.markdown('</div>', unsafe_allow_html=True)

with main_col2:
    # Control buttons
    st.markdown("**Controls**")
    
    if not st.session_state.wakeword_system.is_running:
        if st.button("▶️ **Start Listening**", type="primary", use_container_width=True):
            st.session_state.wakeword_system.start()
            st.rerun()
        st.caption("Click to activate wake-word detection")
    else:
        if st.button("⏹️ **Stop Listening**", type="secondary", use_container_width=True):
            st.session_state.wakeword_system.stop()
            st.rerun()
        st.caption("Click to deactivate wake-word detection")

# Manual recording and text input section
st.markdown("---")

# Use a container for the manual recording to avoid layout shifts
with st.container():
    st.markdown("### ⌨️ Manual Input")
    
    # Text input
    st.text_input("Type your question here:", key="text_input", on_change=lambda: process_text_only(st.session_state.text_input) if st.session_state.text_input else None)
    
    st.markdown("**OR**")
    
    # Manual recording button
    # Disable manual recording if wakeword is active/recording to avoid resource conflict
    wakeword_active = st.session_state.wakeword_recording_active or (st.session_state.wakeword_system and st.session_state.wakeword_system.is_active())
    
    if st.button("🎤 **Record Audio (5s)**", type="primary", disabled=wakeword_active):
        # Pause wakeword system if running
        was_running = False
        if st.session_state.wakeword_system.is_running:
            st.session_state.wakeword_system.pause()
            was_running = True
            time.sleep(0.5) # Give it time to release the mic
            
        record_and_process_audio()
        
        # Resume wakeword system if it was running
        # Note: resume() is also called in finally block of record_and_process_audio
        # but we double check here just in case
        if was_running and not st.session_state.wakeword_system.is_running:
             st.session_state.wakeword_system.resume()
             
    if wakeword_active:
        st.caption("⚠️ Manual recording disabled while wake-word system is active")

