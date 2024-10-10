from fastapi import FastAPI, File, UploadFile, WebSocket
from pydantic import BaseModel
import io
from melo.api import TTS
from fastapi.responses import StreamingResponse,HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
# Initialize the TTS models as before
device = 'cpu'
models = {
    'EN': TTS(language='EN', device=device),
    'ES': TTS(language='ES', device=device),
    'FR': TTS(language='FR', device=device),
    'ZH': TTS(language='ZH', device=device),
    'JP': TTS(language='JP', device=device),
    'KR': TTS(language='KR', device=device),
}

class SynthesizePayload(BaseModel):
    text: str = 'Ahoy there matey! There she blows!'
    language: str = 'EN'
    speaker: str = 'EN-US'
    speed: float = 1.0

@app.post("/stream")
async def synthesize_stream(payload: SynthesizePayload):
    language = payload.language
    text = payload.text
    speaker = payload.speaker or list(models[language].hps.data.spk2id.keys())[0]
    speed = payload.speed

    def audio_stream():
        bio = io.BytesIO()
        models[language].tts_to_file(text, models[language].hps.data.spk2id[speaker], bio, speed=speed, format='wav')
        audio_data = bio.getvalue()
        return audio_data

    return StreamingResponse(audio_stream(), media_type="audio/wav")

@app.post("/streamresponse")
async def synthesize_stream(payload: SynthesizePayload):
    language = payload.language
    text = payload.text
    speaker = payload.speaker or list(models[language].hps.data.spk2id.keys())[0]
    speed = payload.speed

    async def audio_stream():
        async for audio_chunk in models[language].tts_to_file_async(
            text,
            speaker_id=models[language].hps.data.spk2id[speaker],
            speed=speed,
            format='wav'
        ):
            bio = io.BytesIO(audio_chunk)
            audio_data = bio.getvalue()
            print("One chunk received with length:", len(audio_data))
            yield audio_data 
        # Return a StreamingResponse with the audio stream
    return StreamingResponse(audio_stream(), media_type="audio/wav")

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")