"""Check if all required dependencies are installed."""
import sys

required_packages = [
    "fastapi",
    "uvicorn",
    "streamlit",
    "streamlit_webrtc",
    "pydantic",
    "torch",
    "transformers",
    "PIL",
    "numpy",
    "cv2",
    "ultralytics",
    "whisper",
    "edge_tts",
    "mutagen",
    "pygame",
    "pyaudio",
    "ddgs",
    "bs4",
    "requests",
    "fastmcp",
]

missing_packages = []

print("🔍 Checking dependencies...\n")

for package in required_packages:
    try:
        if package == "PIL":
            __import__("PIL")
        elif package == "cv2":
            __import__("cv2")
        elif package == "bs4":
            __import__("bs4")
        elif package == "streamlit_webrtc":
            __import__("streamlit_webrtc")
        else:
            __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - MISSING")
        missing_packages.append(package)

print("\n" + "="*50)

if missing_packages:
    print(f"\n❌ {len(missing_packages)} package(s) missing:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    print("\n💡 Install dependencies with:")
    print("   uv sync")
    print("   or")
    print("   pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✅ All dependencies are installed!")
    print("🚀 You can now start the gateway with: python start_gateway.py")
    sys.exit(0)

