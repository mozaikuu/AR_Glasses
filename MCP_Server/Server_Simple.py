import asyncio
import json
import sys

from tools.tts import tts_tool
from tools.gps import gps_tool
from tools.camera import cv_tool

from discovery.wifi import start_wifi_broadcast
from discovery.bluetooth import start_bt_broadcast

wifi = start_wifi_broadcast(port=8765)
bt_server, bt_port = start_bt_broadcast()

TOOLS = {
    "tts": tts_tool,
    "gps": gps_tool,
    "cv": cv_tool
}

if message["method"] == "call_tool":
    tool_name = message["params"]["tool"]
    params = message["params"].get("args", {})

    tool = TOOLS.get(tool_name)
    if tool:
        result = await tool(params) if asyncio.iscoroutinefunction(tool) else tool(params)

# {"method": "call_tool", "params": {"tool": "tts", "args": {"text": "Hello world"}}}
# {"method": "call_tool", "params": {"tool": "gps"}}
# {"method": "call_tool", "params": {"tool": "cv", "args": {"frame_path": "/img.jpg"}}}

async def handle_stdin():
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break

        try:
            message = json.loads(line.decode().strip())
            print("Received:", message, file=sys.stderr)

            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"msg": "Hello from your Smart Glasses MCP server!"}
            }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            print("Error:", e, file=sys.stderr)

asyncio.run(handle_stdin())
