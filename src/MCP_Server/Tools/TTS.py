# wrapper for your Text_to_speech module
import asyncio
import os

# adjust this import to match your existing TTP/text_to_speech function
# Example assumes an async function text_to_speech(file_path)
try:
    from Text_to_speech.TTP import text_to_speech
except Exception:
    # fallback stub if your module path differs; replace with correct import
    async def text_to_speech(fp):
        # simple stub: pretend we spoke
        await asyncio.sleep(0.5)
        return True

async def tts_tool(params):
    text = params.get("text", "")
    if not text:
        return {"error": "no text provided"}

    tmp = "tmp_tts_input.txt"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)

    # If your real function isn't async, call it in executor or adapt.
    if asyncio.iscoroutinefunction(text_to_speech):
        await text_to_speech(tmp)
    else:
        # run sync function in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, text_to_speech, tmp)

    # optionally delete temp
    try:
        os.remove(tmp)
    except Exception:
        pass

    return {"status": "ok", "spoken_text": text}
