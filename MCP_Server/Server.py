"""
MCP JSON-RPC TCP server + tool dispatcher + wifi & bluetooth discovery integration.

Run: python server.py
"""

import asyncio
import json
import sys
import signal

from tools.tts import tts_tool
from tools.gps import gps_tool
from tools.camera import cv_tool

from discovery.wifi import start_wifi_broadcast
from discovery.bluetooth import start_bt_broadcast

PORT = 8765
TOOLS = {
    "tts": tts_tool,
    "gps": gps_tool,
    "cv": cv_tool
}

async def handle_tcp(reader, writer):
    addr = writer.get_extra_info('peername')
    print("TCP client connected:", addr)
    while True:
        data = await reader.readline()
        if not data:
            break
        try:
            msg = json.loads(data.decode().strip())
        except Exception as e:
            print("Invalid JSON:", e)
            continue

        # Expect JSON-RPC like: {"jsonrpc":"2.0","id":1,"method":"call_tool","params":{"tool":"tts","args":{"text":"hi"}}}
        response = {"jsonrpc": "2.0", "id": msg.get("id")}

        try:
            if msg.get("method") == "call_tool":
                params = msg.get("params", {})
                tool_name = params.get("tool")
                args = params.get("args", {})
                if tool_name in TOOLS:
                    tool = TOOLS[tool_name]
                    if asyncio.iscoroutinefunction(tool):
                        result = await tool(args)
                    else:
                        # run sync tool in threadpool so we don't block event loop
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, tool, args)
                    response["result"] = result
                else:
                    response["error"] = {"code": -32601, "message": "Tool not found"}
            else:
                response["error"] = {"code": -32601, "message": "Unknown method"}
        except Exception as e:
            response["error"] = {"code": -32000, "message": str(e)}

        writer.write((json.dumps(response) + "\n").encode())
        await writer.drain()

    writer.close()
    await writer.wait_closed()
    print("TCP client disconnected:", addr)


async def start_server():
    server = await asyncio.start_server(handle_tcp, host="0.0.0.0", port=PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"[TCP] Serving on {addrs}")

    # Start discovery services
    zeroconf, local_ip = start_wifi_broadcast(port=PORT)
    bt_sock = start_bt_broadcast(local_ip, PORT)

    # Graceful shutdown on SIGINT/SIGTERM
    loop = asyncio.get_event_loop()
    stop = asyncio.Future()

    def _signal_handler():
        if not stop.done():
            stop.set_result(True)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except Exception:
            # Not all systems support add_signal_handler (Windows)
            pass

    async with server:
        await asyncio.wait([server.serve_forever(), stop], return_when=asyncio.FIRST_COMPLETED)

    # cleanup
    try:
        zeroconf.unregister_all_services()
        zeroconf.close()
    except Exception:
        pass
    try:
        bt_sock.close()
    except Exception:
        pass
    print("Server shut down.")

if __name__ == "__main__":
    asyncio.run(start_server())
