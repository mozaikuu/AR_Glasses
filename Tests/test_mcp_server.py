"""Test script to diagnose MCP server startup issues."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Python: {sys.executable}")
print(f"Project root: {project_root}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")
print()

# Test imports
print("Testing imports...")
try:
    print("  - fastmcp...", end=" ")
    from fastmcp import FastMCP
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("  - server.server...", end=" ")
    from server.server import mcp
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - tools.search.search_web...", end=" ")
    from tools.search.search_web import retrieve_web_context
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - tools.vision.yolo...", end=" ")
    from tools.vision.yolo import infer
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    print("  (This is OK - camera might not be available)")
    # Don't exit, just warn

print()
print("All critical imports successful!")
print()
print("Try running the MCP server directly:")
print(f"  {sys.executable} -m fastmcp run server.server:mcp --transport stdio")

