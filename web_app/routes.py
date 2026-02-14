from flask import Blueprint, render_template, jsonify, request
from web_app.services import wakeword_service
from config.settings import API_URL, WAKE_WORDS
import requests
import sys
import base64
import numpy as np
import time

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/config')
def get_config():
    return jsonify({
        'wake_words': WAKE_WORDS
    })

@main.route('/status')
def status():
    status_data = wakeword_service.get_status()
    if request.args.get('consume') == 'true':
        wakeword_service.clear_flags()
    return jsonify(status_data)

@main.route('/control/start', methods=['POST'])
def start_listening():
    wakeword_service.start_listening()
    return jsonify({'status': 'started'})

@main.route('/control/stop', methods=['POST'])
def stop_listening():
    wakeword_service.stop_listening()
    return jsonify({'status': 'stopped'})

@main.route('/process', methods=['POST'])
def process_text():
    data = request.json
    text = data.get('text')
    mode = data.get('mode', 'quick')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    was_running = wakeword_service.wakeword_system and wakeword_service.wakeword_system.is_running
    if was_running:
        pass

    try:
        request_data = {
            "mode": mode,
            "text": text
        }
        
        print(f"Sending request to AI: {request_data}", file=sys.stderr)
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            result["response"] = result.get("response") or result.get("answer") or ""
            return jsonify(result)
        else:
            return jsonify({'error': f"AI Error: {response.status_code} - {response.text}"}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if wakeword_service.wakeword_system:
             wakeword_service.wakeword_system.return_to_idle()

@main.route('/record', methods=['POST'])
def record_audio():
    """Record audio and process with AI."""
    was_running = False
    if wakeword_service.wakeword_system and wakeword_service.wakeword_system.is_running:
        wakeword_service.pause()
        was_running = True
        time.sleep(0.5)

    try:
        import pyaudio
        
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = 5
        
        p = pyaudio.PyAudio()
        
        device_index = None
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels', 0) > 0:
                device_index = i
                break
        
        if device_index is None:
            return jsonify({'error': 'No microphone found'}), 404
            
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_array = audio_array.astype(np.float32) / 32767.0
        
        if np.max(np.abs(audio_array)) > 1.0:
            audio_array = audio_array / np.max(np.abs(audio_array))
            
        audio_bytes = audio_array.tobytes()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        request_data = {
            "mode": "quick",
            "audio": b64_audio,
            "audio_dtype": "float32"
        }
        
        response = requests.post(f"{API_URL}/process", json=request_data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            result["response"] = result.get("response") or result.get("answer") or ""
            return jsonify(result)
        else:
            return jsonify({'error': f"Processing failed: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        if was_running:
            wakeword_service.resume()
