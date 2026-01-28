"""Test running the MCP server directly to see what error occurs."""
import sys
import os
import subprocess
from pathlib import Path

project_root = Path(__file__).parent
python_exe = sys.executable

print(f"Testing MCP server startup...")
print(f"Python: {python_exe}")
print(f"Project root: {project_root}")
print()

# Test the exact command the gateway uses
cmd = [
    python_exe,
    "-m", "fastmcp",
    "run", "server.server:mcp",
    "--transport", "stdio"
]

print(f"Command: {' '.join(cmd)}")
print()

# Set environment
env = dict(os.environ)
env["PYTHONPATH"] = str(project_root)

# Run with a short timeout to see if it starts
try:
    print("Starting subprocess (will timeout after 5 seconds)...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(project_root)
    )
    
    # Wait a bit to see initial output
    import time
    time.sleep(2)
    
    # Check if process is still running
    if proc.poll() is None:
        print("OK Process is still running (good!)")
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        print(f"\nSTDOUT:\n{stdout}")
        print(f"\nSTDERR:\n{stderr}")
    else:
        # Process exited
        return_code = proc.returncode
        stdout, stderr = proc.communicate()
        print(f"X Process exited with code {return_code}")
        print(f"\nSTDOUT:\n{stdout}")
        print(f"\nSTDERR:\n{stderr}")
        
except Exception as e:
    print(f"Error running subprocess: {e}")
    import traceback
    traceback.print_exc()

