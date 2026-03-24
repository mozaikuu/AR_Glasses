🎯 Smart Glasses AI Assistant - Complete Project Walkthrough
🏗️ Project Overview
This is a sophisticated multimodal AI assistant designed specifically for smart glasses, featuring voice-activated interactions, real-time object detection, web search capabilities, and intelligent conversation modes. The system combines cutting-edge AI technologies with an intuitive hands-free interface.
🏛️ Core Architecture
📊 High-Level Architecture
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│ Streamlit │────│ FastAPI │────│ Cerebras ││ Frontend │ │ Gateway │ │ LLM API ││ (UI + Wake) │ │ (HTTP Bridge) │ │ │└─────────────────┘ └─────────────────┘ └─────────────────┘ │ │ │ │ │ │ ▼ ▼ ▼┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│ Wake-Word │ │ MCP Server │ │ Agent Loop ││ Detection │ │ (Tools) │ │ (Reasoning) │└─────────────────┘ └─────────────────┘ └─────────────────┘
🔧 Technology Stack
Frontend: Streamlit (Web UI + Wake-Word)
Backend: FastAPI (HTTP Gateway)
AI Model: Cerebras Llama-3.3-70B (Cloud API)
Speech: Google Speech Recognition + OpenAI Whisper (Fallback)
Vision: YOLOv8 (Real-time Object Detection)
Search: DuckDuckGo Search API
Audio: PyAudio + PyGame (Recording & Playback)
Protocol: MCP (Model Context Protocol) for Tool Integration
⚙️ Component Deep Dive

1. 🤖 AI Agent Core (agent/)
   The intelligent brain of the system, implementing two distinct reasoning modes:
   📝 Agent Loop (agent_loop.py)

# Main reasoning engineasync def agent_loop(client, user_input: str, mode: str, image: str = None): history = [] used_tools = set() for loop_num in range(1, MAX_LOOPS + 1): # Get AI decision (reasoning + tool selection) decision = await decide(user_input, history, used_tools, client, mode, image) if decision["is_satisfied"]: return decision["answer"] # Final answer elif decision["tool"]: # Execute tool and continue reasoning result = await execute_tool(decision["tool"], decision["args"]) history.append(f"Tool result: {result}")

🎯 Decision Making (api_llm.py)
async def decide(query, history, used_tools, client, mode, image=None): # Build comprehensive prompt with tool information tools_info = "\n".join(f"- {t.name}: {t.description}" for t in client.list_tools()) prompt = f""" You are an intelligent agent running in {mode} mode. Available tools: {tools_info} History: {history} Query: {query} Respond with JSON: {{"reasoning": "...", "tool": "...", "args": {{}}, "is_satisfied": false, "answer": ""}} """ # Get structured response from LLM response = await generate_chat([{"role": "user", "content": prompt}]) return extract_json(response)
🔀 Operating Modes (modes.py)
Quick Mode: Single-pass responses, fast but limited reasoning
Thinking Mode: Multi-loop reasoning until satisfaction, better for complex tasks 2. 🎤 Speech Processing (tools/speech/)
Multi-layered speech recognition with accuracy fallbacks:
🎯 Primary: Google Speech Recognition

# Fast, accurate, cloud-basedresult = recognizer.recognize_google(audio_data, language="en-US")

🔄 Fallback: OpenAI Whisper

# Local, privacy-focused, handles edge casesresult = whisper_model.transcribe(audio_array)["text"]

📊 Audio Pipeline
Audio Input → Normalization → Format Conversion → Google API → Success? ↓ No ↓ YesWhisper Fallback → Final Transcription → Result 3. 👁️ Computer Vision (tools/vision/)
Real-time object detection for smart glasses:
🎯 YOLO Object Detection (yolo.py)
def infer(): # Load YOLO model model = YOLO('yolo11n.pt') # Capture camera frame cap = cv2.VideoCapture(0) ret, frame = cap.read() # Detect objects results = model(frame) # Extract detections detections = [] for result in results: for box in result.boxes: class_name = model.names[int(box.cls)] confidence = float(box.conf) detections.append(f"{class_name} ({confidence:.1f})") return ", ".join(detections) 4. 🔍 Web Search (tools/search/)
Intelligent web research capabilities:
🦆 DuckDuckGo Integration (search_web.py)
def retrieve_web_context(query: str, max_results: int = 5): results = [] with DDGS() as ddgs: for result in ddgs.text(query, max_results=max_results): results.append({ "title": result["title"], "body": result["body"], "url": result["href"] }) return results 5. 🚨 Wake-Word System (tools/wakeword/)
Hands-free activation system:
🔄 State Machine
class SystemState(Enum): IDLE = "idle" # Listening for wake words ACTIVE = "active" # Processing command PROCESSING = "processing" # Waiting for AI response
🎤 Continuous Listening
def \_listen_for_wake_words(self): while self.is_running and self.state == SystemState.IDLE: with self.microphone as source: audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2) # Check for wake words text = self.recognizer.recognize_google(audio).lower() for wake_word in self.wake_words: if wake_word in text and confidence >= self.sensitivity: self.\_play_acknowledgment() # Audio feedback self.\_change_state(SystemState.ACTIVE) self.\_listen_for_command() # Switch to command mode 6. 🌐 Server Architecture (server/)
HTTP bridge connecting frontend to AI backend:
🚪 FastAPI Gateway (gateway.py)
@app.post("/process")async def process_multimodal(req: MultimodalRequest): # 1. Transcribe audio if provided if req.audio: transcribed_text = transcribe_audio_bytes(audio_bytes, dtype=audio_dtype) # 2. Combine inputs (text + transcribed audio + image) combined_text = f"{req.text} [Voice: {transcribed_text}]" # 3. Call AI with tools result = await generate_chat(messages, max_tokens=512) return {"response": result, "transcription": transcribed_text}
🔧 MCP Server (server.py)
mcp = FastMCP(name="smart-glasses")@mcp.tool()def VisionDetect() -> str: """Detect objects in camera view using YOLO.""" return infer()@mcp.tool() def search_web(query: str) -> dict: """Perform web search and return results.""" return retrieve_web_context(query) 7. 🎨 User Interface (app.py)
Streamlit-based web interface with real-time features:
🎯 Wake-Word Integration

# Initialize wake-word systemwakeword_system = create_wakeword_system()# Event-driven UI updateswhile not st.session_state.wakeword_events.empty(): event = st.session_state.wakeword_events.get() if event['type'] == 'command_received': st.session_state.command_text = event['command_text'] process_wakeword_command(event['command_text'])

📱 UI Components
Wake-Word Status: Real-time system state display
Command Recognition: Shows what was heard
AI Response Display: Formatted output with transcriptions
Manual Controls: Fallback recording options
🔄 Data Flow Walkthrough
🎤 Voice Command Flow
User says "Nova, what's the weather?"1. Wake-Word Detection ↓2. Audio Acknowledgment (beep) ↓ 3. Command Listening Mode ↓4. Speech Recognition → "what's the weather" ↓5. UI Update → "🎤 I heard: 'what's the weather'" ↓6. AI Processing Request → Gateway ↓7. Agent Reasoning → Tool Selection ↓8. Web Search Tool Execution ↓9. Response Formatting ↓10. UI Display → "🤖 AI Response: [weather info]"
📸 Vision + Text Flow
User: "What animal is this?" + [uploads cat photo]1. Image Processing ↓2. YOLO Object Detection → "cat" ↓3. Agent Reasoning → "User asking about cat" ↓4. Tool Selection → VisionDetect + Web Search ↓5. Combined Results ↓6. Final Answer → "That's a cat! Here's more info..."
🛠️ Development Workflow
🚀 Quick Start Process

# 1. Install dependenciespip install -r requirements.txt# 2. Set API keyexport CEREBRAS_API_KEY="your-key-here"# 3. Start backend server python start_gateway.py# 4. Start frontend (new terminal)streamlit run app.py

🧪 Testing Infrastructure
Audio Testing: test_microphone.py - Records and transcribes speech
Wake-Word Testing: demo_wakeword.py - Tests voice activation
API Testing: Direct endpoint testing with curl/Postman
Integration Testing: Full end-to-end workflows
🔧 Configuration Management

# config/settings.py - Centralized configurationAPI_KEY = "csk-..." # Cerebras API keyMODEL_ID = "llama3.3-70b" # AI model selectionAUDIO_SAMPLE_RATE = 44100 # Audio settingsVISION_MODEL_PATH = "src/.../yolo11n.pt" # Model paths

📦 Dependency Management

# requirements.txt - All project dependenciesfastmcp==2.14.1 # MCP protocolfastapi # Web framework streamlit # UI frameworktorch # ML frameworkopenai-whisper # Speech recognitionultralytics # YOLO visionduckduckgo-search # Web searchpyaudio # Audio I/O

🎯 Key Features & Capabilities
✨ Multimodal Input
Text: Direct typing or voice transcription
Voice: Real-time speech recognition with wake-word activation
Vision: Live camera object detection and image analysis
Combined: Multi-input processing (text + voice + image)
🧠 Intelligent Agent
Context Awareness: Maintains conversation history
Tool Integration: Uses appropriate tools based on query
Reasoning Modes: Quick responses vs. deep analysis
Error Handling: Graceful fallbacks and user feedback
🔧 Advanced Tools
VisionDetect: Real-time object recognition
search_web: Intelligent web research
Speech Recognition: Multi-engine with accuracy fallbacks
Audio Processing: Professional-grade recording and playback
📱 User Experience
Hands-Free: Wake-word activation ("Nova", "Hey Nova")
Real-Time Feedback: Live status updates and progress indicators
Professional UI: Clean, intuitive interface
Cross-Platform: Works on desktop and mobile browsers
🔮 Future Enhancements
🚀 Planned Features
GPS Navigation: Real-time location and routing
TTS Output: Voice responses for truly hands-free operation
Multi-Language: Support for additional languages
Offline Mode: Local model fallback when network unavailable
Wearable Integration: Direct smart glasses hardware support
⚡ Performance Optimizations
Edge Computing: On-device processing for privacy
Model Optimization: Quantized models for faster inference
Caching: Intelligent response caching and context preservation
Streaming: Real-time response streaming
🎉 Project Impact
This Smart Glasses AI Assistant represents a cutting-edge fusion of:
🤖 Advanced AI: State-of-the-art language models and computer vision
🎤 Natural Interaction: Hands-free voice control with wake-word activation
🔧 Practical Tools: Real-world utility through integrated search and detection
📱 Modern UX: Intuitive web interface accessible anywhere
The system successfully demonstrates how AI can be seamlessly integrated into daily life through wearable technology, providing intelligent assistance that's both powerful and effortless to use.
Ready for production deployment with professional-grade reliability and user experience! 🚀✨
