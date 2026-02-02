import queue
import threading
import sys
import time
from tools.wakeword.wakeword_system import create_wakeword_system, SystemState

class WakeWordService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WakeWordService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.wakeword_system = None
        self.event_queue = queue.Queue()
        self.results = {
            'wake_word_detected': False,
            'last_wake_word': None,
            'wake_confidence': 0.0,
            'wake_text': None,
            'command_received': False,
            'command_text': None,
            'system_state': 'idle',
            'ai_response': None,
            'transcription': None,
            'error_message': None
        }
        self.device_index = None
        self._initialized = True

    def initialize(self):
        if self.wakeword_system is None:
            self.device_index = self._get_valid_audio_device_index()
            self.wakeword_system = create_wakeword_system(device_index=self.device_index)
            self._setup_callbacks()
            print("WakeWordService initialized", file=sys.stderr)
            
            # Auto-start listening by default
            self.start_listening()

    def _get_valid_audio_device_index(self):
        """Find a valid audio input device index."""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            device_index = None
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info.get('maxInputChannels', 0) > 0:
                    device_index = i
                    print(f"Found audio device: {device_info.get('name')}", file=sys.stderr)
                    break
            p.terminate()
            return device_index
        except Exception as e:
            print(f"Error finding audio device: {e}", file=sys.stderr)
            return None

    def _setup_callbacks(self):
        def on_wake_word_detected(wake_word, confidence, text):
            self.event_queue.put({
                'type': 'wake_word_detected',
                'wake_word': wake_word,
                'confidence': confidence,
                'text': text
            })

        def on_command_received(command_text):
            self.event_queue.put({
                'type': 'command_received',
                'command_text': command_text
            })

        def on_state_changed(old_state, new_state):
            self.event_queue.put({
                'type': 'state_changed',
                'old_state': old_state,
                'new_state': new_state
            })

        self.wakeword_system.set_callbacks(
            wake_word_callback=on_wake_word_detected,
            command_callback=on_command_received,
            state_callback=on_state_changed
        )

    def start_listening(self):
        if self.wakeword_system and not self.wakeword_system.is_running:
            self.wakeword_system.start()

    def stop_listening(self):
        if self.wakeword_system and self.wakeword_system.is_running:
            self.wakeword_system.stop()

    def pause(self):
        if self.wakeword_system:
            self.wakeword_system.pause()

    def resume(self):
        if self.wakeword_system:
            self.wakeword_system.resume()

    def process_events(self):
        """Process events from the queue and update results state."""
        processed_count = 0
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                processed_count += 1
                
                if event['type'] == 'wake_word_detected':
                    self.results['wake_word_detected'] = True
                    self.results['last_wake_word'] = event['wake_word']
                    self.results['wake_confidence'] = event['confidence']
                    self.results['wake_text'] = event['text']
                    
                elif event['type'] == 'command_received':
                    self.results['command_received'] = True
                    self.results['command_text'] = event['command_text']
                    
                elif event['type'] == 'state_changed':
                    # Convert Enum to string if needed
                    state = event['new_state']
                    if hasattr(state, 'value'):
                        state = state.value
                    self.results['system_state'] = state
            except queue.Empty:
                break
        
        return processed_count

    def get_status(self):
        self.process_events()
        
        # Add runtime status
        is_running = False
        if self.wakeword_system:
            is_running = self.wakeword_system.is_running
            
        return {
            **self.results,
            'is_running': is_running
        }

    def clear_flags(self):
        """Clear one-time flags after reading."""
        self.results['wake_word_detected'] = False
        self.results['command_received'] = False
        self.results['ai_response'] = None
        self.results['transcription'] = None
        self.results['error_message'] = None

# Global instance
wakeword_service = WakeWordService()
