# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP  
# from tools.computer_vision.yolo import infer
# from tools.gps_navigation.Floor_planning import MultiFloorPlanner 
from tools.search_web.search_web import retrieve_web_context
from tools.computer_vision.cv import detect_objects
from tools.computer_vision.yolo import infer

mcp = FastMCP(name="smart-glasses")

# LLM -> MCP -> Tools -> LLM 

# @mcp.tool()
# def NavigateIndoor(start: str, destination: str, algorithm: str = "astar") -> str:
#     graph = {...}
#     heuristic = {...}

#     nav = IndoorNavigator(graph, heuristic)

#     if algorithm == "bfs":
#         path = nav.bfs(start, destination)
#     elif algorithm == "dfs":
#         path = nav.dfs(start, destination)
#     elif algorithm == "dijkstra":
#         path, _ = nav.dijkstra(start, destination)
#     else:
#         path, _ = nav.astar(start, destination)

#     if not path:
#         return "No route found."

#     return " → ".join(path)

@mcp.tool()
def search_web(query: str) -> dict:
    """Perform a web search and returns results to summarize."""
    # Placeholder for web search logic
    return retrieve_web_context(query)

# @mcp.tool()
# def CV() -> str:
#     """Computer Vision tool."""
#     results = infer()
#     return f"Computer Vision Inference Results: {results}"

# @mcp.tool()
# def GPS_Path() -> str:
#     return MultiFloorPlanner.calculate_path()

# @mcp.tool()
# def GPS_Layout() -> str:    
#     return MultiFloorPlanner.save_project()

# @mcp.tool()
# def VisionDetect() -> str:
#     """Detect objects using the camera."""
#     return detect_objects()


def VisionDetect() -> str:
    """Detect objects using the camera."""
    return infer()

# @mcp.tool()
# def TTS() -> str:
#     """Natural Language Understanding tool."""
#     return "NLU tool executed."

# # @mcp.resource("file://documents/{name}")
# # def read_document(name: str) -> str:
# #     """Read a document by name."""
# #     # This would normally read from disk
# #     return f"Content of {name}"

#  /////////////////////////////////////////////////////////////////////////////////////

# NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

# def ensure_file():
#     if not os.path.exists(NOTES_FILE):
#         with open(NOTES_FILE, "w") as f:
#             f.write("")

# @mcp.tool()
# def add_note(message: str) -> str:
#     """
#     Append a new note to the sticky note file.

#     Args:
#         message (str): The note content to be added.

#     Returns:
#         str: Confirmation message indicating the note was saved.
#     """
#     ensure_file()
#     with open(NOTES_FILE, "a") as f:
#         f.write(message + "\n")
#     return "Note saved!"

# @mcp.tool()
# def read_notes() -> str:
#     """
#     Read and return all notes from the sticky note file.

#     Returns:
#         str: All notes as a single string separated by line breaks.
#              If no notes exist, a default message is returned.
#     """
#     ensure_file()
#     with open(NOTES_FILE, "r") as f:
#         content = f.read().strip()
#     return content or "No notes yet."

# @mcp.resource("notes://latest")
# def get_latest_note() -> str:
#     """
#     Get the most recently added note from the sticky note file.

#     Returns:
#         str: The last note entry. If no notes exist, a default message is returned.
#     """
#     ensure_file()
#     with open(NOTES_FILE, "r") as f:
#         lines = f.readlines()
#     return lines[-1].strip() if lines else "No notes yet."

# @mcp.prompt()
# def note_summary_prompt() -> str:
#     """
#     Generate a prompt asking the AI to summarize all current notes.

#     Returns:
#         str: A prompt string that includes all notes and asks for a summary.
#              If no notes exist, a message will be shown indicating that.
#     """
#     ensure_file()
#     with open(NOTES_FILE, "r") as f:
#         content = f.read().strip()
#     if not content:
#         return "There are no notes yet."

#     return f"Summarize the current notes: {content}"

if __name__ == "__main__":
    mcp.run()