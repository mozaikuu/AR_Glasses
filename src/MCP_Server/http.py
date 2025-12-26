import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from fastmcp import Client
from fastmcp.client import StdioTransport

from llm import agent_loop  # <-- your file

app = FastAPI()

class TextRequest(BaseModel):
    text: str

# ---------- MCP CLIENT ----------
transport = StdioTransport(
    command="fastmcp",
    args=["run", "src/mcp_server/server.py:mcp", "--transport", "stdio"]
)

client: Client | None = None

@app.on_event("startup")
async def startup():
    global client
    client = await Client(transport).__aenter__()
    print("[HTTP] MCP client ready")

@app.on_event("shutdown")
async def shutdown():
    global client
    if client:
        await client.__aexit__(None, None, None)

# ---------- API ----------
@app.post("/run")
async def run_agent(req: TextRequest):
    result = await agent_loop(client, req.text, mode="thinking")
    return {"response": result}
