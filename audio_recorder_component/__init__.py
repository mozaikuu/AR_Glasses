"""
Custom Streamlit component for simple audio recording.
Records audio on button press, transcribes on release.
"""

import os
import streamlit.components.v1 as components
import base64

# Create a _RELEASE constant
_RELEASE = True

# Get the directory of this file
parent_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the build directory
build_dir = os.path.join(parent_dir, "frontend", "build")

# Declare the component
if _RELEASE:
    # For production, use the built component
    audio_recorder = components.declare_component(
        "audio_recorder",
        path=build_dir
    )
else:
    # For development, use the local server
    audio_recorder = components.declare_component(
        "audio_recorder",
        url="http://localhost:3001"
    )

def record_audio_button(key=None):
    """
    Create an audio recording button component.

    Returns:
        dict: Contains 'audio_data' (base64 encoded audio) and 'status' info
    """
    return audio_recorder(key=key, default={"audio_data": None, "status": "ready"})
