import os
import ffmpeg
import torch
import whisper


# --------------------------
# File Extension Definitions
# --------------------------
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.aac', '.ogg', '.flac']

EXTRACTED_AUDIO_NAME = "extracted_audio.mp3"


# --------------------------
# Helper: Convert paths to absolute
# --------------------------
def to_abs(path):
    return os.path.abspath(path)


# --------------------------
# Extract audio from video
# --------------------------
def extract_audio(video_path, output_path):
    """
    Converts a video file into an audio file using ffmpeg.
    """
    ffmpeg.input(video_path).output(output_path).run()
    return output_path


# --------------------------
# Determine if file is audio or video
# --------------------------
def get_audio_path(input_path):
    """
    Returns a valid audio file path.
    - If input is video → extract audio.
    - If input is audio → return it.
    """
    path = to_abs(input_path)

    # Video file
    if any(path.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
        print("Detected: Video file → extracting audio...")
        return extract_audio(path, EXTRACTED_AUDIO_NAME)

    # Audio file
    if any(path.lower().endswith(ext) for ext in AUDIO_EXTENSIONS):
        print("Detected: Audio file.")
        return path

    # Neither
    print("Error: File is not a supported audio or video type.")
    return None


# --------------------------
# Whisper initialization
# --------------------------
def load_whisper_model():
    """
    Loads Whisper (large model) on GPU if available.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model("large").to(device)


# --------------------------
# Transcription
# --------------------------
def transcribe_audio(model, audio_path, language="ar"):
    result = model.transcribe(audio_path, language=language)
    print(result["text"])
    return result


# --------------------------
# Top-level function
# --------------------------
def transcribe_media(input_file):
    """
    Full pipeline:
    1. Identify audio source
    2. (Extract if video)
    3. Transcribe
    4. Save output to TXT file
    """
    audio_path = get_audio_path(input_file)
    if audio_path is None:
        return

    print("Transcribing...")
    result = transcribe_audio(model, audio_path)

    # Save transcription
    out_name = f"transcription_{os.path.basename(audio_path)}.txt"
    with open("./speech_recognition/" + out_name, "w", encoding="utf-8") as f:
        f.write(result["text"])

    print("✓ Transcription saved:", out_name)


# --------------------------
# Run the script
# --------------------------
model = load_whisper_model()
# transcribe_media("./speech_recognition/Test_audio.mp3")
transcribe_media("./Todo/waleed.aac")
transcribe_media("./Todo/handosa1.aac")
transcribe_media("./Todo/handosa2.aac")
