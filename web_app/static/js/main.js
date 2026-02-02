let isPolling = true;
let lastStatus = "unknown";
let wakeWords = ["Computer"]; // Default

document.addEventListener("DOMContentLoaded", () => {
	fetchConfig();
	pollStatus();
	// Poll every 1 second
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
	} catch (error) {
		console.error("Failed to fetch config:", error);
	}
}

function updateWelcomeMessage() {
	const welcomeMsg = document.querySelector(".welcome-message p");
	if (welcomeMsg) {
		const words = wakeWords
			.map((w) => `<strong>"${w}"</strong>`)
			.join(" or ");
		welcomeMsg.innerHTML = `👋 Welcome! Say ${words} to activate.`;
	}
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
		updateStatusDisplay(
			"error",
			"Connection Lost",
			"Failed to connect to server",
		);
	}
}

function updateUI(data) {
	const card = document.getElementById("statusCard");
	const btnStart = document.getElementById("btnStart");
	const btnStop = document.getElementById("btnStop");

	// Update running state controls
	if (data.is_running) {
		btnStart.classList.add("hidden");
		btnStop.classList.remove("hidden");
	} else {
		btnStart.classList.remove("hidden");
		btnStop.classList.add("hidden");
		updateStatusDisplay(
			"default",
			"System Stopped",
			"Wake word detection is off",
		);
		return; // Don't update status text if stopped
	}

	// Update status text based on system state
	const state = data.system_state;
	if (state === "idle") {
		const words = wakeWords.map((w) => `'${w}'`).join(" or ");
		updateStatusDisplay(
			"idle",
			"Ready & Listening",
			`Say ${words} to activate`,
		);
	} else if (state === "active") {
		updateStatusDisplay(
			"active",
			"Listening for Command",
			"Speak your command now...",
		);
	} else if (state === "processing") {
		updateStatusDisplay("processing", "Processing", "AI is thinking...");
	}
}

function updateStatusDisplay(className, title, message) {
	const card = document.getElementById("statusCard");
	const titleEl = document.getElementById("statusTitle");
	const msgEl = document.getElementById("statusMessage");

	// Remove all classes
	card.classList.remove("idle", "active", "processing", "error");
	if (className !== "default") {
		card.classList.add(className);
	}

	titleEl.textContent = title;
	msgEl.textContent = message;
}

function handleEvents(data) {
	// Wake word detected
	if (data.wake_word_detected) {
		addMessage("user", `🎤 Wake word detected: "${data.last_wake_word}"`);
	}

	// Command received -> Trigger processing
	if (data.command_received) {
		addMessage("user", data.command_text);
		processText(data.command_text);
	}

	// If we have AI response directly (e.g. from manual record)
	if (data.ai_response) {
		addMessage("ai", data.ai_response);
	}

	if (data.error_message) {
		addMessage("ai", `❌ ${data.error_message}`);
	}
}

async function startListening() {
	try {
		await fetch("/control/start", { method: "POST" });
		pollStatus();
	} catch (e) {
		console.error(e);
	}
}

async function stopListening() {
	try {
		await fetch("/control/stop", { method: "POST" });
		pollStatus();
	} catch (e) {
		console.error(e);
	}
}

async function manualRecord() {
	const btn = document.getElementById("btnRecord");
	const originalText = btn.innerHTML;

	btn.disabled = true;
	btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recording...';

	try {
		const response = await fetch("/record", { method: "POST" });
		const data = await response.json();

		if (data.error) {
			addMessage("ai", `❌ Error: ${data.error}`);
		} else {
			if (data.transcription) {
				addMessage("user", data.transcription);
			}
			addMessage("ai", data.response);
		}
	} catch (e) {
		addMessage("ai", `❌ Connection Error: ${e.message}`);
	} finally {
		btn.disabled = false;
		btn.innerHTML = originalText;
	}
}

async function sendText() {
	const input = document.getElementById("textInput");
	const text = input.value.trim();

	if (!text) return;

	input.value = "";
	addMessage("user", text);

	await processText(text);
}

async function processText(text) {
	// Show typing indicator?

	try {
		const response = await fetch("/process", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ text: text }),
		});

		const data = await response.json();

		if (data.error) {
			addMessage("ai", `❌ Error: ${data.error}`);
		} else {
			addMessage("ai", data.response);
		}
	} catch (e) {
		addMessage("ai", `❌ Error: ${e.message}`);
	}
}

function handleKeyPress(event) {
	if (event.key === "Enter") {
		sendText();
	}
}

function addMessage(type, text) {
	const container = document.getElementById("chatContainer");
	const welcome = container.querySelector(".welcome-message");
	if (welcome) welcome.remove();

	const div = document.createElement("div");
	div.className = `message ${type}`;

	const label = type === "user" ? "You" : "AI Assistant";

	// Convert newlines to <br> for AI response
	const formattedText = text.replace(/\n/g, "<br>");

	div.innerHTML = `
        <span class="message-label">${label}</span>
        ${formattedText}
    `;

	container.appendChild(div);
	container.scrollTop = container.scrollHeight;
}
