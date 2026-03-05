import streamlit as st
import requests
import numpy as np
import pygame
import threading

from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, AudioProcessorBase
from tools.speech.tts import stop_tts
from tools.speech.transcription import transcribe_audio_array


# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Nova Interface", layout="wide")

API_URL = "http://localhost:8000/run"


# ===============================
# VIDEO PROCESSOR
# ===============================
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        return frame


# ===============================
# AUDIO PROCESSOR (Interrupt + STT)
# ===============================
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = []
        self.silence_counter = 0

    def recv(self, frame):
        audio = frame.to_ndarray()
        volume = np.abs(audio).mean()

        # =====================
        # INTERRUPT LOGIC
        # =====================
        if pygame.mixer.get_init():
            if pygame.mixer.music.get_busy() and volume > 0.02:
                print("User interrupted Nova")
                stop_tts()

        # =====================
        # RECORDING LOGIC
        # =====================
        if volume > 0.02:
            self.audio_buffer.append(audio)
            self.silence_counter = 0
        else:
            self.silence_counter += 1

        # لو حصل صمت بعد الكلام → نعمل STT
        if self.silence_counter > 20 and len(self.audio_buffer) > 10:
            full_audio = np.concatenate(self.audio_buffer, axis=0)
            self.audio_buffer = []
            self.silence_counter = 0

            threading.Thread(
                target=process_audio,
                args=(full_audio,),
                daemon=True
            ).start()

        return frame


# ===============================
# PROCESS AUDIO → STT → API
# ===============================
def process_audio(audio_array):
    text = transcribe_audio_array(audio_array)

    if text and text.strip():
        print("User said:", text)

        try:
            response = requests.post(
                API_URL,
                json={"text": text},
                timeout=300
            )

            result = response.json()["response"]
            print("Nova replied:", result)

        except Exception as e:
            print("API error:", e)


# ===============================
# UI
# ===============================
st.title("🎙 Nova Live Interface")

webrtc_ctx = webrtc_streamer(
    key="nova",
    video_processor_factory=VideoProcessor,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={
        "video": True,
        "audio": True
    },
    async_processing=True
)

st.info("Talk normally. Nova will interrupt and respond automatically.")
