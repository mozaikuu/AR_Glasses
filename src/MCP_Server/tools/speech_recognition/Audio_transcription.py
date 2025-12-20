import ffmpeg
import torch
import whisper
import pyaudio
import wave
import numpy as np

# the file name output you want to record into
filename = "recorded.wav"

FORMAT = pyaudio.paInt32
channels = 1
sample_rate = 44100        # MUST match device
chunk = 1024
record_seconds = 5
device_index = 1   # Realtek Mic

_model = None

def get_model():
    global _model
    if _model is None:
        import whisper
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = whisper.load_model("large").to(device)
    return _model

def record_audio():
    p = pyaudio.PyAudio()
    # open stream object as input
    stream = p.open(format=FORMAT,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=False,
                    input_device_index=device_index,
                    frames_per_buffer=chunk)
    frames = []
    print("Recording...")
    for i in range(int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        # if you want to hear your voice while recording
        # stream.write(data)
        frames.append(data)
    print("Finished recording.")
    # stop and close stream
    stream.stop_stream()
    stream.close()
    # terminate pyaudio object
    p.terminate()
   
    # Convert audio frames to numpy array
    audio_data = b''.join(frames)
    audio_array = np.frombuffer(audio_data, dtype=np.int32)
    
    # Normalize to float32 in range [-1, 1] (Whisper expects this format)
    audio_array = audio_array.astype(np.float32) / np.iinfo(np.int32).max
    
    return audio_array

# --------------------------
# Top-level function
# --------------------------
def transcribe_audio():
    """
    Full pipeline:
    1. Identify audio source
    2. (Extract if video)
    3. Transcribe
    4. Save output to TXT file
    """
    audio_array = record_audio()
   
    model = get_model()
    print("Transcribing...")
    result = model.transcribe(audio_array, fp16=False)
    print("Transcription complete.")
   
    return result["text"]

# --------------------------
# Run the script
# --------------------------
if __name__ == "__main__":

    result_text = transcribe_audio()
    print("\nTranscription Result:")
    print(result_text)