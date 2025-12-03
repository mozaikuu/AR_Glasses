from mcp.server.fastmcp import FastMCP
# import Computer_Vision.yolo as cv_tool
from Computer_Vision.yolo import infer
from GPS_Navigation.Floor_planning import MultiFloorPlanner

mcp = FastMCP(name="Tools Server")

# LLM -> MCP -> Tools -> LLM 

@mcp.tool()
def CV() -> str:
    """Computer Vision tool."""
    results = infer()
    return f"Computer Vision Inference Results: {results}"

# @mcp.tool()
# def GPS_Path() -> str:
#     return MultiFloorPlanner.calculate_path()

# @mcp.tool()
# def GPS_Layout() -> str:    
#     return MultiFloorPlanner.save_project()

@mcp.tool()
def SpeechToText() -> str:
    """Speech to Text tool."""
    return "SpeechToText tool executed."

@mcp.tool()
def TextToSpeech() -> str:
    """Text to Speech tool."""
    return "TextToSpeech tool executed."

@mcp.tool()
def NLU() -> str:
    """Natural Language Understanding tool."""
    return "NLU tool executed."