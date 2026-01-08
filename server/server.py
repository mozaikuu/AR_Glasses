"""MCP server with FastMCP."""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure PYTHONPATH is set
if "PYTHONPATH" not in os.environ or str(project_root) not in os.environ.get("PYTHONPATH", ""):
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = str(project_root) + (os.pathsep + current_pythonpath if current_pythonpath else "")

# Change to project root directory to ensure relative imports work
os.chdir(project_root)

try:
    from fastmcp import FastMCP
except ImportError as e:
    # Print error to stderr so it's visible in subprocess
    print(f"ERROR: Failed to import fastmcp: {e}", file=sys.stderr, flush=True)
    print(f"ERROR: Python: {sys.executable}", file=sys.stderr, flush=True)
    print(f"ERROR: sys.path = {sys.path[:3]}", file=sys.stderr, flush=True)
    raise

try:
    from tools.search.search_web import retrieve_web_context
except ImportError as e:
    print(f"ERROR: Failed to import search_web: {e}", file=sys.stderr, flush=True)
    raise

try:
    from tools.vision.yolo import infer
except ImportError as e:
    print(f"ERROR: Failed to import yolo: {e}", file=sys.stderr, flush=True)
    # Don't raise - make it optional for now
    def infer():
        return "Vision tool not available: Import failed"

mcp = FastMCP(name="smart-glasses")

# LLM -> MCP -> Tools -> LLM


@mcp.tool()
def VisionDetect() -> str:
    """Detect and identify objects in the camera view using YOLO object detection.

    Requirements:
    - Camera must be connected and accessible
    - Camera permissions must be granted
    - YOLO model must be available

    Returns detected objects as a comma-separated list, or error message if camera/model unavailable.
    """
    try:
        result = infer()

        # If vision fails, provide helpful guidance
        if "not available" in result.lower() or "failed" in result.lower() or "not found" in result.lower():
            result += "\n\nTroubleshooting:\n" \
                     "• Ensure your camera is connected and enabled\n" \
                     "• Grant camera permissions to this application\n" \
                     "• For smart glasses, use an external webcam\n" \
                     "• Check that YOLO model file exists at: src/mcp_server/tools/computer_vision/yolo11n_coco8_trained.pt\n" \
                     "• Alternative: Use search_web tool for object information"

        return result
    except Exception as e:
        return f"Vision detection error: {str(e)}"


@mcp.tool()
def search_web(query: str) -> dict:
    """Perform a web search and return results to summarize."""
    return retrieve_web_context(query)


if __name__ == "__main__":
    mcp.run()

