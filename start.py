#!/usr/bin/env python3
"""
Simple startup script for Smart Glasses.

Runs:
1. FastAPI server (port 8000) - Main API
2. Flask web app (port 5000) - Web UI

Usage:
    python start.py        # Start both servers
    python start.py stop    # Stop all servers
"""
import subprocess
import sys
import os
import signal

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Server configurations
SERVERS = [
    {"name": "API Server", "script": "start_server.py", "port": 8000},
    {"name": "Web UI", "script": "run_flask.py", "port": 5000},
]

processes = []


def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    print("\nStopping servers...")
    for p in processes:
        p.terminate()
    sys.exit(0)


def check_port(port):
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_server(name, script, port):
    """Start a server."""
    if check_port(port):
        print(f"⚠️  Port {port} in use - {name} may already be running")
        return

    print(f"Starting {name}...")
    try:
        p = subprocess.Popen([sys.executable, script], cwd=PROJECT_ROOT)
        processes.append(p)
        print(f"✅ {name} started (port {port})")
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")


def stop_all():
    """Stop all servers."""
    print("Stopping all servers...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    print("All servers stopped.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    command = sys.argv[1] if len(sys.argv) > 1 else None

    if command == "stop":
        stop_all()
    else:
        print("=" * 50)
        print("  Smart Glasses Server")
        print("=" * 50)

        for server in SERVERS:
            start_server(server["name"], server["script"], server["port"])

        print("\n🌐 Access URLs:")
        print("   • API:    http://localhost:8000")
        print("   • Web:    http://localhost:5000")
        print("\nPress Ctrl+C to stop.\n")

        # Wait for processes
        try:
            for p in processes:
                p.wait()
        except KeyboardInterrupt:
            stop_all()
