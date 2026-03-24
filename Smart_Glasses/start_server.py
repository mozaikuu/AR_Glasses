#!/usr/bin/env python3
"""
Smart Glasses Server Startup Script
Automatically detects local IP and shows connection info for mobile app.
"""
import socket
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback method
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip

def print_startup_info():
    """Print startup information including IP addresses."""
    print("=" * 60)
    print("  Smart Glasses Server - Starting Up")
    print("=" * 60)
    
    local_ip = get_local_ip()
    print(f"\n📍 Local IP Address: {local_ip}")
    
    print("\n📱 Mobile App Configuration:")
    print(f"   Update mobile/lib/config.dart with:")
    print(f"   static const String serverUrl = 'http://{local_ip}:8001';")
    
    print("\n🌐 Access URLs:")
    print(f"   • API Server:     http://{local_ip}:8000")
    print(f"   • Web Dashboard:  http://{local_ip}:5000")
    print(f"   • Health Check:    http://{local_ip}:8000/health")
    print(f"   • API v2 Root:     http://{local_ip}:8000/v2/")
    
    print("\n📋 Quick Commands:")
    print(f"   • ngrok http 8000  # Expose to internet (if needed)")
    print(f"   • curl http://{local_ip}:8000/health  # Test server")
    
    print("\n" + "=" * 60)
    
    return local_ip

if __name__ == "__main__":
    local_ip = print_startup_info()
    
    # Update environment variable for other scripts to use
    os.environ["SERVER_IP"] = local_ip
    
    # Start the servers
    import uvicorn
    from server.api_v2 import app
    
    port = 8000
    print(f"🚀 Starting FastAPI server on port {port}...")
    print(f"   Binding to: 0.0.0.0 (all interfaces)")
    print(f"   Local access: http://localhost:{port}")
    print(f"   Network access: http://{local_ip}:{port}")
    print("-" * 60)
    print("NOTE: Watchdog reloader DISABLED to prevent recursion loops")
    print("      To auto-reload on code changes, use: uvicorn.run(..., reload=True)")
    print("-" * 60)
    
    # Use reload=False to avoid watchdog recursion issues
    # The recursion loop happens when watchdog triggers reload too frequently
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
