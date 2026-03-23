# Quick Start Guide

## Prerequisites

1. Python 3.10 or higher
2. `uv` package manager (recommended) or `pip`
3. **Cerebras API Key** (for LLM functionality)

### Setting up Cerebras API (Required)

This application uses Cerebras API for fast, free LLM inference instead of local models.

1. Go to [https://cloud.cerebras.ai/](https://cloud.cerebras.ai/)
2. Sign up for a free account (no credit card required)
3. Get your API key from the dashboard
4. Set the environment variable:

**Windows:**

```bash
set CEREBRAS_API_KEY=your-api-key-here
```

**Linux/Mac:**

```bash
export CEREBRAS_API_KEY='your-api-key-here'
```

**To make it permanent:**

-  Windows: Add to System Environment Variables
-  Linux/Mac: Add to `~/.bashrc` or `~/.zshrc`

**Test your API key:**

```bash
python test_cerebras_api.py
```

## Installation

### Option 1: Using `uv` (Recommended)

```bash
# Install dependencies
uv sync

# This will install all dependencies from pyproject.toml
```

### Option 2: Using `pip`

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Step 1: Activate Virtual Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
source .venv/bin/activate
```

### Step 2: Start the Gateway Server

**Option A: Using the new startup script (Recommended for mobile access)**

```bash
python start_server.py
```

This will:

-  Automatically detect and display your local IP address
-  Start the FastAPI server on `0.0.0.0:8000` (accessible from mobile on local network)
-  Show connection info for configuring the mobile app

You'll see output like:

```
============================================================
  Smart Glasses Server - Starting Up
============================================================

📍 Local IP Address: 192.168.1.100

📱 Mobile App Configuration:
   Update mobile/lib/config.dart with:
   static const String serverUrl = 'http://192.168.1.100:8001';

🌐 Access URLs:
   • API Server:     http://192.168.1.100:8000
   • Web Dashboard:  http://192.168.1.100:5000
   • Health Check:    http://192.168.1.100:8000/health
   • API v2 Root:     http://192.168.1.100:8000/v2/
```

**Option B: Using the activation script**

**Windows:**

```bash
start_gateway.bat
```

**Linux/Mac:**

```bash
chmod +x start_gateway.sh
./start_gateway.sh
```

**Option C: Manual activation then run**

```bash
# Activate venv first (see Step 1)
python start_gateway.py
```

You should see:

```
🚀 Starting gateway server on localhost:8000
📝 Press Ctrl+C to stop the server

INFO:     Uvicorn running on http://localhost:8000
INFO:     Application startup complete.
```

**Keep this terminal open!** The gateway must be running for the Streamlit app to work.

### Step 3: Start the Streamlit App

**Open a NEW terminal** and activate the virtual environment again, then:

**Option A: Using the activation script (Recommended)**

**Windows:**

```bash
start_streamlit.bat
```

**Linux/Mac:**

```bash
chmod +x start_streamlit.sh
./start_streamlit.sh
```

**Option B: Manual activation then run**

```bash
# Activate venv first (see Step 1)
streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Install dependencies first:

```bash
uv sync
# or
pip install -r requirements.txt
```

### "Connection refused" or "Gateway Offline"

**Solution**: Make sure the gateway server is running:

1. Check if you see the gateway startup message in the terminal
2. Verify it's running on `http://localhost:8000`
3. Try accessing `http://localhost:8000/` in your browser - you should see `{"status":"ok"}`

### Port Already in Use

If port 8000 is already in use, you can change it:

1. Edit `config/settings.py`:

   ```python
   API_PORT = int(os.getenv("API_PORT", "8001"))  # Change to 8001 or another port
   ```

2. Or set environment variable:
   ```bash
   set API_PORT=8001
   python start_gateway.py
   ```

### Audio/Video Not Working

-  Make sure you've granted browser permissions for camera and microphone
-  Check that your camera/microphone are not being used by another application
-  Try refreshing the Streamlit page

## Usage

1. **Text Input**: Type your question in the text area
2. **Image Input**:
   -  Make sure camera is active (green indicator)
   -  Click "📸 Capture Frame" to capture current frame
3. **Voice Input**:
   -  Click "🎙️ Start Recording"
   -  Speak into your microphone
   -  Click "⏹️ Stop Recording" when done
4. **Send Request**: Click "🚀 Send Request" to process all inputs

## Stopping the Application

1. Press `Ctrl+C` in the gateway terminal to stop the server
2. Press `Ctrl+C` in the Streamlit terminal to stop the app

## Mobile App Configuration

### Accessing from Mobile Phone (No ngrok needed!)

The server now runs on `0.0.0.0` which means it's accessible from your local network.

1. **Start the server** using `python start_server.py`
2. **Note the Local IP Address** displayed in the terminal (e.g., `192.168.1.100`)
3. **Update mobile config**: Edit `mobile/lib/config.dart`:

```dart
class Config {
  // Replace YOUR_PC_IP with your computer's IP address
  static const String serverUrl = 'http://192.168.1.100:8001';
}
```

4. **Run the mobile app** on your phone (connected to the same WiFi network)

### Why Mobile Mic Might Not Work

If the microphone works on PC but not on phone:

1. **Server not accessible**: Ensure the server IP in `mobile/lib/config.dart` is correct
2. **Different network**: Phone and PC must be on the same WiFi network
3. **Firewall**: Ensure Windows Firewall allows Python through:
   -  Go to Windows Security → Firewall & Network Protection
   -  Allow an app through firewall
   -  Find Python and check both Private and Public
4. **Manual input fallback**: The mobile app has a "Type instead" button if voice doesn't work

## Moondream Vision Model

The application now uses **Moondream** for enhanced vision-language understanding instead of YOLO.

### What Moondream Provides:

-  Detailed scene descriptions (not just object labels)
-  Activity recognition (what people are doing)
-  Text extraction from images
-  Context-aware understanding

### Fallback to YOLO:

If Moondream fails to load (due to GPU/memory constraints), the system automatically falls back to YOLO.

### Installation:

Moondream uses 4-bit quantization to run efficiently on consumer GPUs:

```bash
pip install bitsandbytes  # Already included in dependencies
```

### Troubleshooting Vision:

-  **No GPU**: Moondream will fall back to YOLO
-  **Out of memory**: Reduce batch size or use YOLO
-  **First run slow**: Moondream downloads model on first use (~2GB)
