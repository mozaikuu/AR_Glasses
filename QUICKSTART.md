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

**Option A: Using the activation script (Recommended)**

**Windows:**

```bash
start_gateway.bat
```

**Linux/Mac:**

```bash
chmod +x start_gateway.sh
./start_gateway.sh
```

**Option B: Manual activation then run**

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
