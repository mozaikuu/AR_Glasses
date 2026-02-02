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

try:
    from tools.navigation.navigation import navigate, load_graph, get_all_locations, visualize_graph, astar, navigate_steps
except ImportError as e:
    print(f"ERROR: Failed to import navigation: {e}", file=sys.stderr, flush=True)

try:
    from tools.navigation.nav_runner import start_navigation, next_navigation_step, get_navigation_status, cancel_navigation
except ImportError as e:
    print(f"ERROR: Failed to import nav_runner: {e}", file=sys.stderr, flush=True)

mcp = FastMCP(name="Cerebro")

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
                     "• Check that YOLO model file exists at: models/yolo11n.pt\n" \
                     "• Alternative: Use search_web tool for object information"

        return result
    except Exception as e:
        return f"Vision detection error: {str(e)}"


@mcp.tool()
def search_web(query: str) -> dict:
    """Perform a web search and return results to summarize."""
    return retrieve_web_context(query)


@mcp.tool()
def navigate_indoor(start: str, destination: str) -> dict:
    """Navigate from a starting location to a destination within the building using A* pathfinding.

    Requirements:
    - Start and destination must be valid locations in the building
    - A path must exist between the two locations

    Returns detailed navigation instructions including:
    - The path taken (list of locations)
    - Total distance
    - Step-by-step instructions with directions
    - Turn-by-turn guidance

    Common starting points: Entrance, Stairs G, Elevator G, Floor 1
    Common destinations: Dean Office, TA Office, Hall 2-1-84, Section 2-1-40
    """
    result = navigate(start, destination)
    return result


@mcp.tool()
def list_navigation_locations() -> dict:
    """List all available locations for indoor navigation.

    Returns a dictionary containing all locations that can be used as
    start or destination points for indoor navigation.
    """
    graph = load_graph()
    locations = get_all_locations(graph)
    return {
        "locations": sorted(locations),
        "count": len(locations)
    }


@mcp.tool()
def navigate_and_visualize(start: str, destination: str, save_image: bool = False) -> dict:
    """Navigate from start to destination and generate a visual map.

    Requirements:
    - Start and destination must be valid locations in the building
    - A path must exist between the two locations

    Returns detailed navigation information including:
    - The path taken (list of locations)
    - Total distance
    - Step-by-step instructions
    - Path visualization image as base64 string (if matplotlib available)
    - Turn-by-turn guidance

    Common locations: Entrance, Hall 2-0-25, Stairs G, Elevator G, Floor 1,
    TA Office, Dean Office, Hall 2-1-84, Section 2-1-40
    """
    import base64
    from io import BytesIO

    graph = load_graph()

    # Validate locations
    all_locations = get_all_locations(graph)
    if start not in all_locations:
        return {
            "success": False,
            "error": f"Start location '{start}' not found",
            "available_locations": sorted(all_locations)
        }

    if destination not in all_locations:
        return {
            "success": False,
            "error": f"Destination '{destination}' not found",
            "available_locations": sorted(all_locations)
        }

    # Run A* algorithm
    path, distance, steps = astar(graph, start, destination)

    if not path:
        return {
            "success": False,
            "error": f"No path found from '{start}' to '{destination}'",
            "start": start,
            "destination": destination
        }

    # Generate visualization
    image_base64 = None
    if save_image:
        try:
            # Create a temporary buffer for the image
            buffer = BytesIO()
            visualize_graph(graph, path=path, save_path=buffer, show=False)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            buffer.close()
        except Exception as e:
            print(f"WARNING: Could not generate visualization: {e}", file=sys.stderr)

    # Format step-by-step instructions
    directions_text = f"Route from {start} to {destination}:\n\n"
    directions_text += f"Total steps: {len(steps)}\n"
    directions_text += f"Total distance: {distance} steps\n\n"

    for step in steps:
        directions_text += f"Step {step['step']}: {step['from']}\n"
        directions_text += f"   -> {step['instruction']}\n"
        directions_text += f"   (Distance: {step['distance']} steps)\n\n"

    return {
        "success": True,
        "start": start,
        "destination": destination,
        "path": path,
        "total_distance": distance,
        "steps": steps,
        "directions": directions_text,
        "image_base64": image_base64,
        "image_format": "png" if image_base64 else None
    }


@mcp.tool()
def start_indoor_navigation(start: str, destination: str) -> dict:
    """Start a step-by-step indoor navigation session with voice and visual guidance.

    Requirements:
    - Start and destination must be valid locations in the building
    - A path must exist between the two locations

    Use this for turn-by-turn navigation while wearing smart glasses.
    After starting, use 'next_navigation_step' to advance through each instruction.

    Returns:
    - Navigation session details with first instruction
    - Audio-ready text for TTS playback
    - Progress information for glasses display

    Example locations: Entrance, Hall 2-0-25, Stairs G, Elevator G, Floor 1,
    TA Office, Dean Office, Hall 2-1-84, Section 2-1-40
    """
    result = start_navigation(start, destination)
    return result


@mcp.tool()
def next_navigation_instruction(session_id: str = None) -> dict:
    """Get the next navigation instruction for glasses guidance.

    Use this tool when the user says 'next', 'continue', or 'turn by turn'
    during an active navigation session. Returns the next instruction with:
    - Text for TTS audio playback
    - Location details for visual display on glasses
    - Progress information

    Args:
        session_id: Optional session ID. Uses most recent if not provided.

    Returns:
    - Next step instruction with audio text
    - Current progress (step X of Y)
    - Arrival notification when navigation is complete
    """
    result = next_navigation_step(session_id)
    return result


@mcp.tool()
def get_navigation_progress(session_id: str = None) -> dict:
    """Get current navigation status and progress for glasses display.

    Use this tool to show the user's current position in the navigation route,
    including:
    - Current step number and total steps
    - Progress percentage
    - Current instruction for display
    - Remaining distance

    Args:
        session_id: Optional session ID. Uses most recent if not provided.

    Returns:
    - Current progress information
    - Current instruction text
    """
    result = get_navigation_status(session_id)
    return result


@mcp.tool()
def cancel_navigation_session(session_id: str = None) -> dict:
    """Cancel the current navigation session.

    Use when the user wants to stop navigation or go to a different destination.
    Frees up the navigation session.

    Args:
        session_id: Optional session ID. Cancels most recent if not provided.

    Returns:
    - Confirmation of cancellation
    """
    result = cancel_navigation(session_id)
    return result


if __name__ == "__main__":
    mcp.run()

