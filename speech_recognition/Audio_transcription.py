import os
import tempfile
import requests
import ffmpeg
import torch
import whisper
from icecream import ic

# Define lists of video and audio file extensions
video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.waptt']

output_audio = "test_audio.mp3"


def extract_audio(file_name, audio_path):
    ffmpeg.input(file_name).output(audio_path).run()


def check_file_type(file_name):
    if any(file_name.lower().endswith(ext) for ext in video_extensions):
        print("This file is a video.")
        extract_audio(file_name, output_audio)
        return output_audio
    elif any(file_name.lower().endswith(ext) for ext in audio_extensions):
        print("This file is an audio.")
        return file_name
    else:
        print("This file is neither a video nor an audio. Please check the file type.")
        return None


def delete_file(path):
    try:
        os.remove(path)
        print(f"File {path} has been deleted.")
    except FileNotFoundError:
        print(f"File {path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def init():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("large").to(device)
    return model


def transcribe(model, file_name):
    result = model.transcribe(file_name, language="ar")
    print(result["text"])
    with open("speech_recognition/transcription.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])

model = init()

def transcribe_video_or_audio(media_files):
    """
    media_files: list of dicts like
        [{'url': 'https://api.twilio.com/…', 'type': 'audio/ogg'}, …]
    """
    ic(torch.cuda.is_available())
    ic(torch.cuda.device_count())
    ic(torch.cuda.get_device_name(0))
    
    file_to_test = media_files
    Voice = ""  # <-- initialize empty string to store text
    tmp_path = tempfile.mkstemp()

    path_to_audio = check_file_type(file_to_test)
    # path_to_audio = check_file_type(tmp_path)
    if path_to_audio:
        # print("Transcribing...")
        result = model.transcribe(path_to_audio, language="ar")
        # print("Transcription complete.")
        # Voice += result["text"] + "\n"  # <-- store text
        # print(result["text"])
        print("Transcription written to file.")
        # delete_file(path_to_audio)

    delete_file(tmp_path)

    return Voice   # <-- return it

transcribe_video_or_audio("speech_recognition/Test_audio.mp3")