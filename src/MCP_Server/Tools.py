from mcp.server.fastmcp import FastMCP
# import Computer_Vision.yolo as cv_tool
from Computer_Vision.yolo import infer

mcp = FastMCP(name="Tools Server")

# LLM -> MCP -> Tools -> LLM 

@mcp.tool()
def CV() -> None:
    """Computer Vision tool."""
    return infer()


@mcp.tool()
def GPS() -> str:
    """GPS tool."""
    return "GPS tool executed."

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