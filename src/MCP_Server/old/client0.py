import asyncio
from fastmcp import Client
from fastmcp.client import StdioTransport
# from tools.llm.llm import decide_tool
# from llm import decide_tool
from mcp_server.old.llm_inferrence import decide_tool
from tools.text_to_speech.tts import text_to_speech
from tools.speech_recognition.Audio_transcription import transcribe_audio

async def agent():
    transport = StdioTransport(
        command="fastmcp",
        args=[
            "run",
            "src/mcp_server/server.py:mcp",
            "--transport",
            "stdio",
        ],
    )
    
    client = Client(transport=transport)

    async with client:
        
        # ask the user to speak
        await text_to_speech("what do you need help with sir?")
        print("Q: done")
        
        # text = transcribe_audio()
        text = "A silent story unfolds before my eyes, yet its name escapes me"
        
        decision = await decide_tool(text)
        
        result = await client.call_tool(
            name=decision["tool"],
            arguments=decision["args"]
        )
        
        print("User Input:", text)
        # print(result.content[0].text)
        await text_to_speech(result.content[0].text)        
        # return "Agent run complete."

if __name__ == "__main__":
    asyncio.run(agent())