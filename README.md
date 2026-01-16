# Smart Glasses Project

Your AI companion and navigation in Smart Glasses - A multimodal LLM agent with vision, voice, and text capabilities.

## Project Structure

The project follows a domain-driven architecture:

```
Smart_Glasses/
├── ui/                    # Streamlit frontend
│   ├── app.py            # Main Streamlit app
│   ├── components/       # UI components
│   └── utils/            # UI utilities
├── agent/                # LLM agent logic
│   ├── llm.py           # LLM model handling & generation
│   ├── agent_loop.py    # Main agent reasoning loop
│   └── modes.py         # Quick/thinking mode logic
├── tools/                # MCP tools
│   ├── vision/          # Computer vision tools (YOLO)
│   ├── search/          # Web search tools
│   ├── speech/          # Speech recognition & TTS
│   └── navigation/      # GPS/navigation tools
├── server/               # MCP server
│   ├── server.py        # FastMCP server definition
│   └── gateway.py       # HTTP gateway for Streamlit
├── models/               # Data models
│   └── requests.py      # Pydantic models for API
├── config/               # Configuration
│   ├── settings.py      # App settings
│   └── model_config.py  # LLM model configuration
└── shared/               # Shared utilities
    └── utils.py         # Common utilities
```

## Features

-  **Multimodal Input**: Support for text, voice, and image inputs
-  **Two Agent Modes**:
   -  **Quick Mode**: Fast single-pass responses
   -  **Thinking Mode**: Deep reasoning with history looping until satisfied
-  **MCP Tools**:
   -  `VisionDetect`: Real-time object detection using camera and YOLO model
   -  `search_web`: Web search and context retrieval
-  **Streamlit UI**: Interactive web interface with live camera and audio capture

## Quickstart

### 1. Install Dependencies

**Important**: You must install dependencies before running the application!

**Option A: Using `uv` (Recommended)**

```bash
uv sync
```

**Option B: Using `pip`**

```bash
pip install -r requirements.txt
```

### 2. Activate Virtual Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
source .venv/bin/activate
```

### 3. Start the HTTP Gateway

**Open a terminal** (with venv activated) and run:

**Windows (using batch file):**

```bash
start_gateway.bat
```

**Linux/Mac (using shell script):**

```bash
chmod +x start_gateway.sh
./start_gateway.sh
```

**Or manually:**

```bash
python start_gateway.py
```

You should see:

```
🚀 Starting gateway server on localhost:8000
INFO:     Uvicorn running on http://localhost:8000
```

**⚠️ Keep this terminal open!** The gateway must be running for the Streamlit app to work.

The gateway will be available at `http://localhost:8000`

### 4. Start the Streamlit App

**Open a NEW terminal**, activate the virtual environment, and run:

**Windows (using batch file):**

```bash
start_streamlit.bat
```

**Linux/Mac (using shell script):**

```bash
chmod +x start_streamlit.sh
./start_streamlit.sh
```

**Or manually:**

```bash
# Activate venv first
streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`

### Troubleshooting

**"ModuleNotFoundError" or "No module named 'fastapi'"**

-  Solution: Install dependencies first with `uv sync` or `pip install -r requirements.txt`

**"Connection refused" or "Gateway Offline"**

-  Solution: Make sure the gateway server is running (Step 2). Check that you see the startup message in the gateway terminal.

See `QUICKSTART.md` for more detailed troubleshooting.

## Usage

1. **Text Input**: Type your question in the text area
2. **Image Input**: Click "Capture Frame" to capture the current camera frame
3. **Voice Input**: Click "Capture Audio" to capture audio from your microphone
4. **Send Request**: Click "Send Request" to process all inputs together
5. **Mode Selection**: Choose between "quick" (fast) or "thinking" (deep reasoning) mode

The agent will:

-  Transcribe audio if provided
-  Combine text + transcribed audio + image into a unified prompt
-  Process through the LLM agent with available MCP tools
-  Return a response

## Configuration

Edit `config/settings.py` or set environment variables:

-  `MODEL_ID`: LLM model identifier (default: "google/gemma-3-4b-it")
-  `DEVICE`: "cuda" or "cpu" (default: auto-detected)
-  `API_HOST`: Gateway host (default: "localhost")
-  `API_PORT`: Gateway port (default: 8000)
-  `MAX_LOOPS`: Maximum agent loop iterations (default: 8)

## MCP Server

The MCP server can be used independently with Claude Desktop or other MCP clients.

### Claude Desktop Configuration

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
	"mcpServers": {
		"smart-glasses": {
			"command": "uv",
			"args": [
				"--directory",
				"D:\\0_code\\New_ideas\\1_Coding_Now\\Smart_Glasses",
				"run",
				"fastmcp",
				"run",
				"server.server:mcp",
				"--transport",
				"stdio"
			]
		}
	}
}
```

### Debugging with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv --directory D:\0_code\New_ideas\1_Coding_Now\Smart_Glasses run fastmcp run server.server:mcp --transport stdio
```

## Development

### Project Scripts

-  `start_gateway.py`: Start the HTTP gateway server
-  `server/server.py`: MCP server entry point
-  `ui/app.py`: Streamlit application

### Testing

Test the end-to-end flow:

1. Start the gateway
2. Start the Streamlit app
3. Try different input combinations (text, image, audio)
4. Test both quick and thinking modes
5. Verify MCP tool calls work (vision detection, web search)

## Migration Notes

See `MIGRATION_NOTES.md` for details about the refactoring from the old structure.

## Dependencies

Key dependencies:

-  `fastmcp`: MCP server framework
-  `streamlit`: Web UI framework
-  `streamlit-webrtc`: WebRTC for camera/audio
-  `transformers`: LLM models
-  `torch`: Deep learning framework
-  `ultralytics`: YOLO object detection
-  `whisper`: Speech recognition
-  `edge-tts`: Text-to-speech
-  `fastapi`: HTTP API framework

See `pyproject.toml` for the complete list.
