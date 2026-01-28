#!/usr/bin/env python3
"""Test transcription with debug output to see what's happening."""

import sys
import os
sys.path.append('.')

from tools.speech.transcription import transcribe_audio_bytes
import numpy as np

# Create some test audio data - simulate what comes from Streamlit
print("Testing transcription with synthetic audio...")

# Generate a simple sine wave that should transcribe to something
sample_rate = 16000
duration = 2.0  # 2 seconds
frequency = 440  # A note
t = np.linspace(0, duration, int(sample_rate * duration), False)

# Create a sine wave
audio_array = np.sin(frequency * 2 * np.pi * t)
audio_array = audio_array.astype(np.float32)

# Convert to bytes as it would come from Streamlit
audio_bytes = audio_array.tobytes()

print(f"Test audio: {len(audio_bytes)} bytes, dtype=float32")
print(f"Audio array shape: {audio_array.shape}, range: [{audio_array.min():.3f}, {audio_array.max():.3f}]")

# Test transcription
try:
    result = transcribe_audio_bytes(audio_bytes, dtype="float32")
    print(f"Transcription result: '{result}'")
except Exception as e:
    print(f"Error: {e}")
