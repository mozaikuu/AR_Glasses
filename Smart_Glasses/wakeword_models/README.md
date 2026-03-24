# Wake-Word Activation System

This directory contains the wake-word activation system for the Smart Glasses AI Assistant.

## Overview

The wake-word system provides hands-free activation of the AI assistant using voice commands. It continuously listens for wake words ("Nova" or "Hey Nova") and transitions the system from IDLE to ACTIVE state for command processing.

## Architecture

### State Machine
- **IDLE**: Continuously listening for wake words only
- **ACTIVE**: Wake word detected, listening for command
- **PROCESSING**: Command received, being processed by AI

### Components
- `wakeword_system.py`: Main wake-word detection and state management
- `train_wakeword.py`: Utility for testing wake-word detection
- `demo_wakeword.py`: Complete system demonstration

## Usage

### Basic Usage
```python
from tools.wakeword.wakeword_system import create_wakeword_system

# Create system
system = create_wakeword_system()

# Set callbacks
def on_wake_word(wake_word, confidence, text):
    print(f"Wake word: {wake_word}")

def on_command(command_text):
    print(f"Command: {command_text}")
    # Process with AI here
    system.return_to_idle()

system.set_callbacks(
    wake_word_callback=on_wake_word,
    command_callback=on_command
)

# Start listening
system.start()
```

### Streamlit Integration
The system is fully integrated with the Streamlit app (`app.py`) and provides:
- Real-time status updates
- Visual feedback for wake word detection
- Automatic command processing
- Manual recording fallback

## Configuration

### Wake Words
- Primary: "Nova"
- Alternative: "Hey Nova"
- Both trigger the same activation sequence

### Sensitivity
- Default: 0.5 (0.0-1.0 range)
- Lower values = more sensitive (more false activations)
- Higher values = less sensitive (may miss wake words)

### Audio Settings
- Sample rate: 16kHz
- Channels: Mono
- Recognition: Google Speech API
- Timeout: 3 seconds for commands

## Audio Acknowledgment

When a wake word is detected, the system plays a short beep sound to confirm activation. This uses pygame for audio playback with a fallback to console notification.

## Error Handling

- Network timeouts for speech recognition
- Microphone calibration issues
- Audio playback failures
- Automatic recovery and state management

## Performance

- Low CPU usage in IDLE state
- Fast wake word detection (< 1 second latency)
- Minimal false activations through confidence thresholding
- Efficient state transitions

## Testing

### Quick Test
```bash
python wakeword_models/train_wakeword.py test
```

### Full Demo
```bash
python demo_wakeword.py
```

### Streamlit App
```bash
streamlit run app.py
```

## Dependencies

- `speech_recognition`: Google Speech API integration
- `pyaudio`: Audio input/output
- `pygame`: Audio playback for acknowledgments
- `numpy`: Audio processing

## Troubleshooting

### No Microphone Detected
- Check microphone permissions
- Verify audio device is connected
- Try different audio devices

### High False Activations
- Increase sensitivity threshold
- Check for background noise
- Consider microphone positioning

### Wake Words Not Detected
- Lower sensitivity threshold
- Speak clearly and closer to microphone
- Check internet connection (Google Speech API)

### Audio Playback Issues
- pygame mixer initialization problems
- Fallback to console notifications
- Check audio output device

## Future Enhancements

- Custom wake word model training
- Offline wake word detection
- Multiple language support
- Voice activity detection (VAD) optimization
- Energy-based wake word detection