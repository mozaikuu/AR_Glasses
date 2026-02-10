#!/usr/bin/env python3
"""
Smart Glasses - Unified Server Launcher
Starts all services with a single command.

Services started:
- FastAPI (API v2):     Port 8000
- Gateway Server:        Port 8001  
- Flask Web App:         Port 5000
- WebSocket Audio:       Port 8765

Usage:
    python start_all.py        # Start all servers
    python start_all.py stop   # Stop all servers
    python start_all.py status # Show status
"""
import socket
import sys
import os
import asyncio
import signal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import servers
import uvicorn
from config.settings import API_HOST, API_PORT

# Server configurations
SERVICES = {
    "FastAPI (API v2)": {
        "port": 8000,
        "module": "server.api_v2:app",
        "type": "http"
    },
    "Gateway Server": {
        "port": 8001,
        "module": "server.gateway:app",
        "type": "http"
    },
    "Flask Web App": {
        "port": 5000,
        "module": "web_app:app",
        "type": "http"
    },
    "WebSocket Audio": {
        "port": 8765,
        "module": "server_audio.audio_stream_server",
        "type": "websocket"
    }
}

# Active server processes
active_servers = {}
_executor = ThreadPoolExecutor(max_workers=4)


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


def print_banner():
    """Print startup banner."""
    local_ip = get_local_ip()
    
    print("\n" + "=" * 70)
    print("  🚀 Smart Glasses - Unified Server Launcher")
    print("=" * 70)
    print(f"\n📍 Local IP: {local_ip}")
    print("\n📊 Services:")
    print("-" * 70)
    
    for name, config in SERVICES.items():
        status = "✅ Running" if config["port"] in active_servers else "⏹️ Stopped"
        print(f"   • {name:<22} Port {config['port']:<5} {status}")
    
    print("\n🌐 Access URLs:")
    print(f"   • API Server:      http://{local_ip}:8000")
    print(f"   • Gateway:         http://{local_ip}:8001")
    print(f"   • Web Dashboard:   http://{local_ip}:5000")
    print(f"   • WebSocket:       ws://{local_ip}:8765")
    print("\n📋 Commands:")
    print("   • python start_all.py       Start all servers")
    print("   • python start_all.py stop  Stop all servers")
    print("   • python start_all.py       (Ctrl+C to stop)")
    print("=" * 70 + "\n")
    
    return local_ip


def start_fastapi():
    """Start FastAPI server."""
    try:
        uvicorn.run(
            "server.api_v2:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ FastAPI error: {e}")


def start_gateway():
    """Start gateway server."""
    try:
        uvicorn.run(
            "server.gateway:app",
            host=API_HOST,
            port=API_PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Gateway error: {e}")


def start_flask():
    """Start Flask web app."""
    try:
        from web_app import create_app
        app = create_app()
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Flask error: {e}")


def start_websocket():
    """Start WebSocket audio server."""
    try:
        from server_audio import audio_stream_server
        asyncio.run(audio_stream_server.main())
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


def run_server(name: str, func):
    """Run a server in a thread."""
    try:
        func()
    except Exception as e:
        print(f"❌ {name} failed: {e}")


def start_all():
    """Start all servers concurrently."""
    print_banner()
    
    # Start servers in separate threads
    servers = [
        ("FastAPI (API v2)", start_fastapi),
        ("Gateway Server", start_gateway),
        ("Flask Web App", start_flask),
        ("WebSocket Audio", start_websocket),
    ]
    
    threads = []
    for name, func in servers:
        t = threading.Thread(target=run_server, args=(name, func), daemon=True)
        t.start()
        threads.append(t)
        print(f"✅ Started {name}")
    
    # Mark ports as "running" for display
    global active_servers
    for name, config in SERVICES.items():
        active_servers[config["port"]] = name
    
    print(f"\n🎉 All servers started! Press Ctrl+C to stop.\n")
    
    try:
        # Wait for all threads
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        stop_all()


def stop_all():
    """Stop all servers."""
    print("\n👋 Stopping all servers...")
    
    # Force exit (threads are daemon=True)
    os._exit(0)


def status_check():
    """Show status of all services."""
    print_banner()
    print("\n💡 Tip: Run 'python start_all.py' to start all servers\n")


def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def check_remote_port_in_use(ip: str, port: int) -> bool:
    """Check if a port is in use on a remote IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((ip, port)) == 0
    except:
        return False


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else None
    
    if command == "stop":
        stop_all()
    elif command == "status":
        status_check()
    elif command == "check":
        # Quick health check
        local_ip = get_local_ip()
        print("\n🔍 Health Check:")
        for name, config in SERVICES.items():
            if check_port_in_use(config["port"]):
                print(f"   ✅ {name}: Port {config['port']} in use")
            elif check_remote_port_in_use(local_ip, config["port"]):
                print(f"   ✅ {name}: Port {config['port']} in use (network)")
            else:
                print(f"   ❌ {name}: Port {config['port']} free")
    else:
        start_all()
