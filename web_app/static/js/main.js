let isPolling = true;
let wakeWords = ["computer"];
let browserWakewordEnabled = false;
let browserRecognition = null;
let browserAwaitingCommand = false;
let selectedMicIndex = null;
let activeProcessController = null;

document.addEventListener("DOMContentLoaded", () => {
	fetchConfig();
	loadMicrophones();
	startListening();
	pollStatus();
	setInterval(pollStatus, 1000);
});

async function fetchConfig() {
	try {
		const response = await fetch("/config");
		const data = await response.json();
		if (data.wake_words) {
			wakeWords = data.wake_words;
			updateWelcomeMessage();
		}
		if (Number.isInteger(data.selected_mic_index)) {
			selectedMicIndex = data.selected_mic_index;
		}
	} catch (error) {
		console.error("Failed to fetch config:", error);
	}
}

async function loadMicrophones() {
	const select = document.getElementById("micSelect");
	if (!select) return;

	try {
		const resp = await fetch("/audio/devices");
		const data = await resp.json();
		const devices = Array.isArray(data.devices) ? data.devices : [];
		if (Number.isInteger(data.selected_index)) {
			selectedMicIndex = data.selected_index;
		}

		select.innerHTML = "";
		if (!devices.length) {
			const opt = document.createElement("option");
			opt.value = "";
			opt.textContent = "No input microphones found";
			select.appendChild(opt);
			select.disabled = true;
			return;
		}

		select.disabled = false;
		for (const dev of devices) {
			const opt = document.createElement("option");
			opt.value = String(dev.index);
			opt.textContent = `[${dev.index}] ${dev.name}`;
			select.appendChild(opt);
		}

		if (selectedMicIndex !== null) {
			select.value = String(selectedMicIndex);
		} else if (devices.length) {
			select.value = String(devices[0].index);
		}

		select.onchange = applySelectedMicrophone;
	} catch (e) {
		console.error("Failed to load microphones:", e);
	}
}

async function applySelectedMicrophone() {
	const select = document.getElementById("micSelect");
	if (!select || !select.value) return;

	const nextIndex = Number.parseInt(select.value, 10);
	if (!Number.isInteger(nextIndex)) return;

	try {
		const resp = await fetch("/audio/select", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ device_index: nextIndex }),
		});
		const data = await resp.json();
		if (!data.success) {
			addMessage("ai", `Microphone select failed: ${data.error || "Unknown error"}`);
			return;
		}

		selectedMicIndex = nextIndex;
		addMessage("ai", `Microphone set to device #${nextIndex}.`);
	} catch (e) {
		addMessage("ai", `Microphone select error: ${e.message}`);
	}
}

function updateWelcomeMessage() {
	const welcomeMsg = document.querySelector(".welcome-message p");
	if (!welcomeMsg) return;
	const words = wakeWords.map((w) => `<strong>"${w}"</strong>`).join(" or ");
	welcomeMsg.innerHTML = `Welcome! Say ${words} to activate.`;
}

async function pollStatus() {
	if (!isPolling) return;
	try {
		const response = await fetch("/status?consume=true");
		const data = await response.json();
		updateUI(data);
		handleEvents(data);
	} catch (error) {
		console.error("Status poll failed:", error);
		updateStatusDisplay("error", "Connection Lost", "Failed to connect to server");
	}
}

function updateUI(data) {
	const card = document.getElementById("statusCard");
	const btnStart = document.getElementById("btnStart");
	const btnStop = document.getElementById("btnStop");
	if (!card || !btnStart || !btnStop) return;

	if (data.is_running || browserWakewordEnabled) {
		btnStart.classList.add("hidden");
		btnStop.classList.remove("hidden");
	} else {
		btnStart.classList.remove("hidden");
		btnStop.classList.add("hidden");
		updateStatusDisplay("default", "System Stopped", "Wake word detection is off");
		return;
	}

	if (browserWakewordEnabled) {
		if (browserAwaitingCommand) {
			updateStatusDisplay("active", "Listening for Command", "Speak your command now...");
		} else {
			updateStatusDisplay("idle", "Ready & Listening", "Browser wakeword mode active");
		}
		return;
	}

	const state = data.system_state;
	if (state === "idle") {
		const words = wakeWords.map((w) => `'${w}'`).join(" or ");
		updateStatusDisplay("idle", "Ready & Listening", `Say ${words} to activate`);
	} else if (state === "active") {
		updateStatusDisplay("active", "Listening for Command", "Speak your command now...");
	} else if (state === "processing") {
		updateStatusDisplay("processing", "Processing", "AI is thinking...");
	}
}

function updateStatusDisplay(className, title, message) {
	const card = document.getElementById("statusCard");
	const titleEl = document.getElementById("statusTitle");
	const msgEl = document.getElementById("statusMessage");
	if (!card || !titleEl || !msgEl) return;

	card.classList.remove("idle", "active", "processing", "error");
	if (className !== "default") card.classList.add(className);
	titleEl.textContent = title;
	msgEl.textContent = message;
}

function handleEvents(data) {
	if (data.wake_word_detected) {
		interruptActiveProcessing();
		addMessage("user", `Wake word detected: "${data.last_wake_word}"`);
	}
	if (data.command_received) {
		addMessage("user", data.command_text);
		processText(data.command_text);
	}
	if (data.ai_response) addMessage("ai", data.ai_response);
	if (data.error_message) addMessage("ai", `Error: ${data.error_message}`);
}

function interruptActiveProcessing() {
	if (activeProcessController) {
		try {
			activeProcessController.abort();
			addMessage("ai", "Interrupted. Listening for your new prompt.");
		} catch {
			// no-op
		}
		activeProcessController = null;
	}
}

async function startListening() {
	try {
		const resp = await fetch("/control/start", { method: "POST" });
		const data = await resp.json();
		if (data.status === "started") {
			browserWakewordEnabled = false;
			isPolling = true;
			pollStatus();
			return;
		}
		startBrowserWakewordFallback(data.error || "Server wakeword unavailable.");
	} catch (e) {
		console.error(e);
		startBrowserWakewordFallback("Server wakeword unavailable.");
	}
}

async function stopListening() {
	try {
		await fetch("/control/stop", { method: "POST" });
	} catch (e) {
		console.error(e);
	}
	stopBrowserWakewordFallback();
	isPolling = true;
	pollStatus();
}

function startBrowserWakewordFallback(reason) {
	const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
	if (!SR) {
		addMessage("ai", `${reason} Browser speech recognition is not supported.`);
		return;
	}

	stopBrowserWakewordFallback();
	browserWakewordEnabled = true;
	browserAwaitingCommand = false;
	isPolling = false;

	browserRecognition = new SR();
	browserRecognition.lang = "en-US";
	browserRecognition.continuous = true;
	browserRecognition.interimResults = false;

	browserRecognition.onresult = async (event) => {
		const last = event.results[event.results.length - 1];
		if (!last || !last[0]) return;
		const transcript = String(last[0].transcript || "").trim();
		if (!transcript) return;
		const lower = transcript.toLowerCase();

		if (!browserAwaitingCommand) {
			const matchedWake = wakeWords.find((w) => lower.includes(String(w).toLowerCase()));
			if (matchedWake) {
				browserAwaitingCommand = true;
				addMessage("user", `Wake word detected: "${matchedWake}"`);
				updateStatusDisplay("active", "Listening for Command", "Speak your command now...");
			}
			return;
		}

		browserAwaitingCommand = false;
		addMessage("user", transcript);
		updateStatusDisplay("processing", "Processing", "AI is thinking...");
		await processText(transcript);
		updateStatusDisplay("idle", "Ready & Listening", "Browser wakeword mode active");
	};

	browserRecognition.onerror = (e) => {
		console.warn("Browser wakeword error:", e);
	};

	browserRecognition.onend = () => {
		if (browserWakewordEnabled && browserRecognition) {
			try {
				browserRecognition.start();
			} catch {
				// no-op
			}
		}
	};

	try {
		browserRecognition.start();
		updateStatusDisplay("idle", "Ready & Listening", "Browser wakeword mode active");
		addMessage("ai", reason);
	} catch (e) {
		addMessage("ai", `Failed to start browser wakeword: ${e.message}`);
	}
}

function stopBrowserWakewordFallback() {
	browserWakewordEnabled = false;
	browserAwaitingCommand = false;
	if (browserRecognition) {
		try {
			browserRecognition.onend = null;
			browserRecognition.stop();
		} catch {
			// no-op
		}
	}
	browserRecognition = null;
}

async function manualRecord() {
	const btn = document.getElementById("btnRecord");
	const originalText = btn ? btn.innerHTML : "";
	if (btn) {
		btn.disabled = true;
		btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recording...';
	}

	try {
		let data = null;
		try {
			// Preferred path: Web Audio API capture from selected browser mic.
			// It keeps recording while speech is detected and stops after silence.
			data = await browserManualRecordWebAudio();
		} catch (browserErr) {
			console.warn("Web Audio manual record failed, trying browser speech recognition", browserErr);
			const transcript = await browserManualSpeechToText(6000);
			if (!transcript) {
				throw new Error("No speech recognized");
			}
			addMessage("user", transcript);
			await processText(transcript);
			return;
		}

		if (data.error) {
			addMessage("ai", `Error: ${data.error}`);
		} else {
			if (data._audio_debug) {
				addMessage(
					"ai",
					`Audio debug: in ${data._audio_debug.input_rate}Hz -> out ${data._audio_debug.output_rate}Hz, samples=${data._audio_debug.samples}, peak=${data._audio_debug.peak}`,
				);
			}
			if (data.transcription) addMessage("user", data.transcription);
			if (data.response) {
				addMessage("ai", data.response);
				speakInBrowser(data.response);
			}
		}
	} catch (e) {
		addMessage("ai", `Connection Error: ${e.message}`);
	} finally {
		if (btn) {
			btn.disabled = false;
			btn.innerHTML = originalText;
		}
	}
}

async function browserManualRecordWebAudio(options = {}) {
	if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
		throw new Error("Web Audio capture not supported");
	}

	const voiceThreshold = Number.isFinite(options.voiceThreshold) ? options.voiceThreshold : 0.012;
	const silenceMs = Number.isFinite(options.silenceMs) ? options.silenceMs : 1200;
	const noSpeechTimeoutMs = Number.isFinite(options.noSpeechTimeoutMs) ? options.noSpeechTimeoutMs : 7000;
	const maxRecordMs = Number.isFinite(options.maxRecordMs) ? options.maxRecordMs : 30000;

	const constraints = {
		audio: {
			channelCount: 1,
			echoCancellation: false,
			noiseSuppression: false,
			autoGainControl: false,
		},
	};

	const stream = await navigator.mediaDevices.getUserMedia(constraints);
	const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
	await audioCtx.resume();
	const source = audioCtx.createMediaStreamSource(stream);
	const processor = audioCtx.createScriptProcessor(4096, 1, 1);
	const mute = audioCtx.createGain();
	mute.gain.value = 0;

	const chunks = [];
	let peak = 0;
	let speakingStarted = false;
	let speakingStartAt = 0;
	let lastVoiceAt = 0;
	processor.onaudioprocess = (event) => {
		const input = event.inputBuffer.getChannelData(0);
		const copy = new Float32Array(input.length);
		copy.set(input);
		chunks.push(copy);
		let framePeak = 0;
		for (let i = 0; i < copy.length; i++) {
			const a = Math.abs(copy[i]);
			if (a > peak) peak = a;
			if (a > framePeak) framePeak = a;
		}

		const now = Date.now();
		if (framePeak >= voiceThreshold) {
			lastVoiceAt = now;
			if (!speakingStarted) {
				speakingStarted = true;
				speakingStartAt = now;
			}
		}
	};

	source.connect(processor);
	processor.connect(mute);
	mute.connect(audioCtx.destination);

	const startedAt = Date.now();
	while (true) {
		await new Promise((r) => setTimeout(r, 50));
		const now = Date.now();
		const elapsed = now - startedAt;

		if (elapsed >= maxRecordMs) break;
		if (!speakingStarted && elapsed >= noSpeechTimeoutMs) break;
		if (speakingStarted && lastVoiceAt > 0 && now - lastVoiceAt >= silenceMs) break;
	}

	try {
		processor.disconnect();
		source.disconnect();
		mute.disconnect();
	} catch {
		// no-op
	}
	stream.getTracks().forEach((t) => t.stop());

	const inputRate = audioCtx.sampleRate || 48000;
	await audioCtx.close();
	const merged = mergeFloat32Chunks(chunks);
	if (!speakingStarted || merged.length < 1600) {
		throw new Error("No speech detected");
	}
	const downsampled = downsampleTo16k(merged, inputRate);
	const b64Audio = float32ToBase64(downsampled);

	const response = await fetch("/process", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			mode: "quick",
			audio: b64Audio,
			audio_dtype: "float32",
		}),
	});
	const data = await response.json();
	data._audio_debug = {
		input_rate: inputRate,
		output_rate: 16000,
		samples: downsampled.length,
		peak: Number(peak.toFixed(4)),
		voice_threshold: voiceThreshold,
		speaking_duration_ms: speakingStarted ? Date.now() - speakingStartAt : 0,
	};
	return data;
}

function mergeFloat32Chunks(chunks) {
	let total = 0;
	for (const c of chunks) total += c.length;
	const out = new Float32Array(total);
	let offset = 0;
	for (const c of chunks) {
		out.set(c, offset);
		offset += c.length;
	}
	return out;
}

function downsampleTo16k(input, inputRate) {
	const targetRate = 16000;
	if (!input || !input.length) return new Float32Array(0);
	if (!inputRate || inputRate <= 0 || inputRate === targetRate) return input;

	const ratio = inputRate / targetRate;
	const outLength = Math.max(1, Math.floor(input.length / ratio));
	const out = new Float32Array(outLength);
	let pos = 0;
	for (let i = 0; i < outLength; i++) {
		const nextPos = Math.min(input.length, Math.floor((i + 1) * ratio));
		let sum = 0;
		let count = 0;
		for (let j = pos; j < nextPos; j++) {
			sum += input[j];
			count++;
		}
		out[i] = count > 0 ? sum / count : 0;
		pos = nextPos;
	}
	return out;
}

function float32ToBase64(float32Array) {
	const bytes = new Uint8Array(float32Array.buffer);
	let binary = "";
	const chunkSize = 0x8000;
	for (let i = 0; i < bytes.length; i += chunkSize) {
		const sub = bytes.subarray(i, i + chunkSize);
		binary += String.fromCharCode.apply(null, sub);
	}
	return btoa(binary);
}

function browserManualSpeechToText(timeoutMs = 6000) {
	return new Promise((resolve, reject) => {
		const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
		if (!SR) {
			reject(new Error("SpeechRecognition not supported"));
			return;
		}

		const rec = new SR();
		rec.lang = "en-US";
		rec.continuous = false;
		rec.interimResults = false;
		rec.maxAlternatives = 1;

		let settled = false;
		const finish = (fn, value) => {
			if (settled) return;
			settled = true;
			try {
				rec.onresult = null;
				rec.onerror = null;
				rec.onend = null;
				rec.stop();
			} catch {
				// no-op
			}
			fn(value);
		};

		const timer = setTimeout(() => {
			finish(reject, new Error("Speech recognition timeout"));
		}, timeoutMs);

		rec.onresult = (event) => {
			const last = event.results[event.results.length - 1];
			const transcript = String(last?.[0]?.transcript || "").trim();
			clearTimeout(timer);
			if (!transcript) {
				finish(reject, new Error("Empty transcript"));
				return;
			}
			finish(resolve, transcript);
		};

		rec.onerror = (event) => {
			clearTimeout(timer);
			finish(reject, event?.error ? new Error(event.error) : new Error("Speech recognition error"));
		};

		rec.onend = () => {
			// If ended without result, timer/error path will reject.
		};

		try {
			rec.start();
		} catch (e) {
			clearTimeout(timer);
			finish(reject, e);
		}
	});
}

async function browserManualRecord() {
	if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
		throw new Error("Browser recording not supported");
	}

	const constraints = { audio: true };
	const stream = await navigator.mediaDevices.getUserMedia(constraints);
	let mimeType = "";
	const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
	for (const t of preferred) {
		if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)) {
			mimeType = t;
			break;
		}
	}
	const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
	const chunks = [];

	const stopped = new Promise((resolve, reject) => {
		recorder.ondataavailable = (e) => {
			if (e.data && e.data.size > 0) chunks.push(e.data);
		};
		recorder.onerror = (e) => reject(e.error || new Error("MediaRecorder error"));
		recorder.onstop = () => resolve();
	});

	recorder.start();
	await new Promise((r) => setTimeout(r, 5000));
	recorder.stop();
	await stopped;
	stream.getTracks().forEach((t) => t.stop());

	const blob = new Blob(chunks, { type: recorder.mimeType || mimeType || "audio/webm" });
	const b64Audio = await audioBlobToFloat32Base64(blob);

	const response = await fetch("/process", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			mode: "quick",
			audio: b64Audio,
			audio_dtype: "float32",
		}),
	});
	return await response.json();
}

async function audioBlobToFloat32Base64(blob) {
	const arrayBuffer = await blob.arrayBuffer();
	const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
	const decoded = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
	const channelData = decoded.getChannelData(0);
	const float32 = new Float32Array(channelData.length);
	float32.set(channelData);

	const bytes = new Uint8Array(float32.buffer);
	let binary = "";
	for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);

	await audioCtx.close();
	return btoa(binary);
}

async function sendText() {
	const input = document.getElementById("textInput");
	if (!input) return;
	const text = input.value.trim();
	if (!text) return;

	input.value = "";
	addMessage("user", text);
	await processText(text);
}

async function processText(text) {
	try {
		if (activeProcessController) {
			try {
				activeProcessController.abort();
			} catch {
				// no-op
			}
		}
		activeProcessController = new AbortController();
		const response = await fetch("/process", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ text }),
			signal: activeProcessController.signal,
		});
		const data = await response.json();
		if (data.error) {
			addMessage("ai", `Error: ${data.error}`);
		} else {
			addMessage("ai", data.response);
			speakInBrowser(data.response);
		}
	} catch (e) {
		if (e && e.name === "AbortError") {
			return;
		}
		addMessage("ai", `Error: ${e.message}`);
	} finally {
		activeProcessController = null;
	}
}

function speakInBrowser(text) {
	// Browser voice intentionally disabled; server-side Piper TTS is used instead.
	return;
}

function handleKeyPress(event) {
	if (event.key === "Enter") sendText();
}

function addMessage(type, text) {
	const container = document.getElementById("chatContainer");
	if (!container) return;
	const welcome = container.querySelector(".welcome-message");
	if (welcome) welcome.remove();

	const div = document.createElement("div");
	div.className = `message ${type}`;
	const label = type === "user" ? "You" : "AI Assistant";
	const formattedText = String(text || "").replace(/\n/g, "<br>");

	div.innerHTML = `<span class="message-label">${label}</span>${formattedText}`;
	container.appendChild(div);
	container.scrollTop = container.scrollHeight;
}
