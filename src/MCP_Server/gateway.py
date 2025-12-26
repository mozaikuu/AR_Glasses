import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from agent import AgentService

app = FastAPI()
agent = AgentService()

class TextRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup():
    await agent.start()

@app.post("/process")
async def process_text(req: TextRequest):
    result = await agent.process_text(req.text)
    return {"result": result}
