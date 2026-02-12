from flask import Blueprint, render_template, jsonify, request, send_file
from web_app.services import wakeword_service
from config.settings import API_URL, WAKE_WORDS
import requests
import sys
import base64
import numpy as np
import time
import os
import tempfile
from tools.speech.tts import text_to_speech_sync

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
            
            # Generate TTS on SERVER and return audio
            answer_text = result.get('answer', '')
            if answer_text:
                # Generate TTS audio on server
                audio_path = generate_tts_audio(answer_text)
                result['audio_url'] = f"/tts/{audio_path}"
            
            return jsonify(result)
        else:
            return jsonify({'error': f"AI Error: {response.status_code} - {response.text}"}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if wakeword_service.wakeword_system:
             wakeword_service.wakeword_system.return_to_idle()

def generate_tts_audio(text):
    """Generate TTS audio file and return the filename."""
    # Create temp file for TTS output
    temp_dir = tempfile.gettempdir()
    filename = f"tts_{int(time.time())}.mp3"
    filepath = os.path.join(temp_dir, filename)
    
    # Generate TTS audio (this plays locally on server too)
    text_to_speech_sync(text)
    
    # Return just the filename for URL construction
    return filename

@main.route('/tts/<filename>')
def serve_tts(filename):
    """Serve generated TTS audio file."""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    if os.path.exists(filepath):
        return send_file(
            filepath,
            mimetype='audio/mp3',
            as_attachment=False
        )
    else:
        return jsonify({'error': 'Audio file not found'}), 404

@main.route('/speak', methods=['POST'])
def speak_text():
    """Endpoint to trigger TTS on server."""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Play TTS on server
        text_to_speech_sync(text)
        return jsonify({'status': 'playing', 'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            
            # Generate TTS on SERVER
            answer_text = result.get('answer', '')
            if answer_text:
                audio_path = generate_tts_audio(answer_text)
                result['audio_url'] = f"/tts/{audio_path}"
            
            return jsonify(result)
        else:
            return jsonify({'error': f"Processing failed: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        if was_running:
            wakeword_service.resume()
