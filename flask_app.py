from __future__ import annotations

import importlib
import sys
from pathlib import Path

import httpx

_project_root = Path(__file__).resolve().parent
_removed_paths: list[str] = []
for _path in list(sys.path):
  try:
    if Path(_path).resolve() == _project_root:
      sys.path.remove(_path)
      _removed_paths.append(_path)
  except Exception:
    continue

_flask_pkg = importlib.import_module("flask")

for _path in _removed_paths:
  sys.path.insert(0, _path)

Flask = _flask_pkg.Flask
jsonify = _flask_pkg.jsonify
render_template_string = _flask_pkg.render_template_string
request = _flask_pkg.request
Response = _flask_pkg.Response

from app.models.requests import ProcessRequest
from app.config.settings import settings
from app.services.assistant_service import assistant_service


def create_app() -> Flask:
    app = Flask(__name__)

    def _gateway_base_url() -> str:
        gateway_host = "127.0.0.1" if settings.api_host == "0.0.0.0" else settings.api_host
        return f"http://{gateway_host}:{settings.api_port}"

    def _gateway_process(payload: dict[str, object]) -> dict[str, object] | None:
        url = f"{_gateway_base_url()}/process"
        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data
        except Exception:
            return None
        return None

    @app.get("/")
    def home() -> str:
        return render_template_string(
            """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Smart Glasses Distilled</title>
    <style>
      body { font-family: Segoe UI, Tahoma, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
      .card { max-width: 760px; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08); padding: 1.25rem; }
      textarea { width: 100%; min-height: 90px; margin: 0.5rem 0; }
      button { background: #0f766e; color: white; border: none; padding: 0.6rem 1rem; border-radius: 8px; cursor: pointer; }
      button.secondary { background: #334155; margin-left: 0.5rem; }
      pre { background: #0f172a; color: #e2e8f0; padding: 0.75rem; border-radius: 8px; overflow: auto; }
      .row { margin-top: 0.5rem; }
      #micStatus { color: #0f766e; font-weight: 600; }
      #chat { margin-top: 1rem; border-top: 1px solid #cbd5e1; padding-top: 0.75rem; }
      .bubble { margin: 0.4rem 0; padding: 0.5rem 0.7rem; border-radius: 8px; }
      .user { background: #e2e8f0; }
      .assistant { background: #ccfbf1; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Smart Glasses Distilled</h1>
      <p>Primary Flask interface restored per docs. Use this for quick manual validation.</p>
      <textarea id="prompt" placeholder="Type a prompt..."></textarea>
      <div class="row">
        <button onclick="runProcess()">Send</button>
        <button class="secondary" onclick="toggleVoiceMode()" id="voiceToggle">Disable Voice</button>
        <button class="secondary" onclick="enableMic()">Enable Mic</button>
      </div>
      <div class="row" id="micStatus">Mic status: starting...</div>
      <div class="row" id="micHelp"></div>
      <pre id="out">{"status":"ready"}</pre>
      <div id="chat"></div>
    </div>
    <script>
      let alwaysListening = true;
      let recognition = null;
      let micActive = false;
      let micStarting = false;
      let reconnectTimer = null;
      let reconnectDelayMs = 700;
      let lastFinalTranscript = '';
      let lastFinalAtMs = 0;
      let lastStatusText = '';
      let requestInFlight = false;
      const wakeWords = ['computer', 'hey computer', 'ok computer', 'okay computer'];

      function wakeRegex(wake) {
        const words = wake.trim().split(/\s+/).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        const phrase = `\\b${words.join('[\\s,;:_-]*')}\\b`;
        return new RegExp(`(?:^|[.!?]\\s*|[,;:]\\s*)${phrase}`, 'i');
      }

      function hasWakeword(text) {
        return wakeWords.some((wake) => wakeRegex(wake).test(text || ''));
      }

      function removeWakeword(text) {
        let cleaned = (text || '').trim();
        for (const wake of wakeWords) {
          const words = wake.trim().split(/\s+/).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
          const phrase = `\\b${words.join('[\\s,;:_-]*')}\\b`;
          const pattern = new RegExp(`(?:^|[.!?]\\s*|[,;:]\\s*)${phrase}[,:;\\s-]*`, 'ig');
          cleaned = cleaned.replace(pattern, ' ');
        }
        return cleaned.replace(/\\s+/g, ' ').trim();
      }

      function beepWakeword() {
        try {
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          const oscillator = audioContext.createOscillator();
          const gain = audioContext.createGain();

          oscillator.type = 'sine';
          oscillator.frequency.value = 880;
          gain.gain.value = 0.001;

          oscillator.connect(gain);
          gain.connect(audioContext.destination);

          const now = audioContext.currentTime;
          gain.gain.exponentialRampToValueAtTime(0.15, now + 0.01);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
          oscillator.start(now);
          oscillator.stop(now + 0.2);
        } catch (_err) {
          // Ignore beep failures on browsers that block audio context creation.
        }
      }

      function speechNetworkHint() {
        const reasons = [];
        if (!navigator.onLine) {
          reasons.push('device appears offline');
        }
        if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
          reasons.push('non-secure context (phone/LAN HTTP is blocked for speech APIs; use HTTPS or localhost)');
        }
        reasons.push('browser speech service unavailable or blocked');
        return reasons.join('; ');
      }

      function setMicStatus(text) {
        if (text === lastStatusText) return;
        lastStatusText = text;
        document.getElementById('micStatus').textContent = `Mic status: ${text}`;
      }

      function setMicHelp(html) {
        document.getElementById('micHelp').innerHTML = html || '';
      }

      function clearReconnectTimer() {
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
          reconnectTimer = null;
        }
      }

      function scheduleReconnect(reason) {
        if (!alwaysListening || !recognition) return;
        clearReconnectTimer();
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          startListening(reason);
        }, reconnectDelayMs);
      }

      function startListening(reason = 'manual') {
        if (!recognition || !alwaysListening) return;
        if (micStarting || micActive) return;

        micStarting = true;
        try {
          recognition.start();
        } catch (err) {
          micStarting = false;
          const msg = String(err || '').toLowerCase();
          if (msg.includes('invalidstateerror')) {
            // Browser still tearing down previous session; retry later.
            scheduleReconnect('busy');
            return;
          }
          setMicStatus(`start failed (${err})`);
          reconnectDelayMs = Math.min(reconnectDelayMs * 2, 5000);
          scheduleReconnect('error');
          return;
        }

        if (reason === 'manual') {
          setMicStatus('listening...');
        }
      }

      function appendChat(role, text) {
        const chat = document.getElementById('chat');
        const bubble = document.createElement('div');
        bubble.className = `bubble ${role}`;
        bubble.textContent = `${role === 'user' ? 'You' : 'Assistant'}: ${text}`;
        chat.appendChild(bubble);
      }

      async function runProcess() {
        const text = document.getElementById('prompt').value;
        if (!text || !text.trim()) {
          return;
        }
        if (requestInFlight) {
          setMicStatus('waiting for previous response...');
          return;
        }

        requestInFlight = true;
        setMicStatus('sending...');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 45000);

        try {
          const response = await fetch('/api/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text, mode: 'quick', client: 'flask-ui'}),
            signal: controller.signal,
          });

          let data = {};
          try {
            data = await response.json();
          } catch (_ignored) {
            data = { error: 'Invalid JSON response from server.' };
          }

          if (!response.ok) {
            const errText = data.error || `HTTP ${response.status}`;
            appendChat('assistant', `Request failed: ${errText}`);
            document.getElementById('out').textContent = JSON.stringify(data, null, 2);
            setMicStatus('request failed');
            return;
          }

          appendChat('user', text);
          appendChat('assistant', data.text || '');
          document.getElementById('out').textContent = JSON.stringify(data, null, 2);
          const ttsUrl = data?.metadata?.tts_url;
          if (ttsUrl) {
            try {
              const audio = new Audio(ttsUrl);
              audio.play().catch(() => {});
            } catch (_err) {}
          }
          setMicStatus('listening...');
        } catch (err) {
          const isTimeout = err && (err.name === 'AbortError');
          const isNetwork = err && /failed to fetch|networkerror|network request failed/i.test(String(err));
          if (isTimeout) {
            setMicStatus('request timeout (45s)');
            appendChat('assistant', 'Request timed out. Check server load and try again.');
          } else if (isNetwork) {
            setMicStatus('gateway unreachable');
            appendChat('assistant', 'Cannot reach backend. Verify the gateway is running.');
          } else {
            setMicStatus('request error');
            appendChat('assistant', `Request error: ${err}`);
          }
        } finally {
          clearTimeout(timeoutId);
          requestInFlight = false;
        }
      }

      function startAlwaysOnMic() {
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!Recognition) {
          setMicStatus('browser does not support SpeechRecognition API');
          return;
        }

        if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
          alwaysListening = false;
          setMicStatus('speech mic blocked on HTTP LAN. Open via HTTPS, or use localhost on the same device.');
          return;
        }

        recognition = new Recognition();
        recognition.lang = 'en-US';
        recognition.interimResults = true;
        recognition.continuous = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
          micStarting = false;
          micActive = true;
          reconnectDelayMs = 700;
          setMicStatus('listening...');
        };

        recognition.onresult = async function(event) {
          const result = event.results[event.results.length - 1];
          if (!result.isFinal) {
            setMicStatus(`hearing ${result[0].transcript}`);
            return;
          }
          const transcript = result[0].transcript;
          const now = Date.now();
          // Deduplicate duplicate final events emitted by some browsers.
          if (transcript === lastFinalTranscript && now - lastFinalAtMs < 1200) {
            return;
          }
          lastFinalTranscript = transcript;
          lastFinalAtMs = now;

          const wakewordDetected = hasWakeword(transcript);
          const cleanedTranscript = removeWakeword(transcript);
          if (wakewordDetected) {
            beepWakeword();
            if (!cleanedTranscript) {
              setMicStatus('wakeword detected - waiting for command...');
              return;
            }
          }

          const effectiveText = cleanedTranscript || transcript;
          document.getElementById('prompt').value = effectiveText;
          setMicStatus(`heard "${effectiveText}"`);
          await runProcess();
        };

        recognition.onerror = function(event) {
          micStarting = false;
          if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            alwaysListening = false;
            clearReconnectTimer();
            setMicStatus(`blocked (${event.error}) - click Enable Mic`);
            setMicHelp('Tip: test microphone outside Flask at <a href="http://127.0.0.1:8000/mic-test" target="_blank">Gateway Mic Diagnostics</a>.');
            return;
          }

          if (event.error === 'aborted' || event.error === 'no-speech') {
            // Avoid noisy error states for normal speech timeouts.
            return;
          }

          if (event.error === 'network') {
            setMicStatus(`speech network error: ${speechNetworkHint()}`);
            setMicHelp('Raw mic may still work. Open <a href="http://127.0.0.1:8000/mic-test" target="_blank">Gateway Mic Diagnostics</a> to test capture vs speech service.');
            reconnectDelayMs = Math.min(reconnectDelayMs * 2, 8000);
            scheduleReconnect('network');
            return;
          }

          setMicStatus(`error (${event.error})`);
        };

        recognition.onend = function() {
          micStarting = false;
          micActive = false;
          if (alwaysListening) {
            scheduleReconnect('keepalive');
          } else {
            clearReconnectTimer();
            setMicStatus('idle');
          }
        };

        startListening('manual');
      }

      function toggleVoiceMode() {
        const toggle = document.getElementById('voiceToggle');
        alwaysListening = !alwaysListening;
        if (!alwaysListening) {
          clearReconnectTimer();
          if (recognition) {
            try { recognition.stop(); } catch (err) {}
          }
          micActive = false;
          micStarting = false;
          setMicStatus('idle');
          setMicHelp('');
          toggle.textContent = 'Enable Voice';
        } else {
          toggle.textContent = 'Disable Voice';
          if (!recognition) {
            startAlwaysOnMic();
          } else {
            reconnectDelayMs = 700;
            startListening('resume');
          }
        }
      }

      async function enableMic() {
        try {
          if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach((track) => track.stop());
          }
          alwaysListening = true;
          document.getElementById('voiceToggle').textContent = 'Disable Voice';
          reconnectDelayMs = 700;
          if (!recognition) {
            startAlwaysOnMic();
          } else {
            startListening('resume');
          }
        } catch (err) {
          setMicStatus(`mic permission failed (${err})`);
        }
      }

      // Voice is on by default so user interaction is mostly hands-free.
      if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        setMicStatus('warning: HTTP LAN page detected; speech mic likely blocked. Use HTTPS for phone mic.');
      }
      startAlwaysOnMic();
    </script>
  </body>
</html>
            """
        )

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok", "service": "flask-interface"}, 200

    @app.get("/esp/tts/<path:filename>")
    def proxy_tts(filename: str) -> Response:
        url = f"{_gateway_base_url()}/esp/tts/{filename}"
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(url)
            content_type = response.headers.get("content-type", "audio/wav")
            return Response(response.content, status=response.status_code, content_type=content_type)
        except Exception:
            return Response(b"", status=502, content_type="text/plain")

    @app.post("/api/process")
    def process() -> tuple[dict[str, object], int]:
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "")
        mode = str(payload.get("mode") or "quick")
        client = str(payload.get("client") or "flask")

        relay_payload: dict[str, object] = {
            "text": text,
            "mode": mode,
            "client": client,
            "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        }
        relayed = _gateway_process(relay_payload)
        if relayed is not None:
            relayed_metadata = relayed.get("metadata") if isinstance(relayed.get("metadata"), dict) else {}
            tts_url = relayed_metadata.get("tts_url")
            if isinstance(tts_url, str) and tts_url.startswith("/esp/tts/"):
                relayed_metadata["tts_url"] = tts_url
            relayed_metadata["processed_by"] = "gateway"
            relayed["metadata"] = relayed_metadata
            return jsonify(relayed), 200

        req = ProcessRequest(text=text, mode=mode, client=client)
        result = assistant_service.process(req)
        result_metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        result_metadata["processed_by"] = "flask-local-fallback"
        result["metadata"] = result_metadata
        return jsonify(result), 200

    return app


app = create_app()
