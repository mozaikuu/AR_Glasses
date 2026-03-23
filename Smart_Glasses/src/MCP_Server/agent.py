import asyncio
from fastmcp import Client
from fastmcp.client import StdioTransport
from llm import agent_loop

class AgentService:
    def __init__(self):
        self.transport = StdioTransport(
            command="fastmcp",
            args=["run", "src/mcp_server/server.py:mcp", "--transport", "stdio"]
        )
        self.client = None

    async def start(self):
        self.client = await Client(self.transport).__aenter__()
        print("[MCP] Agent service started")

    async def process_text(self, text: str):
        mode = "thinking" if len(text.split()) > 10 else "quick"
        return await agent_loop(self.client, text, mode=mode)

    async def shutdown(self):
        if self.client:
            await self.client.__aexit__(None, None, None)
