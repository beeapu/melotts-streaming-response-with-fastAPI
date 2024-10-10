import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
import torch
import time
from melo.api import TTS
import asyncio
from typing import Optional

    
class TTSResponse(BaseModel):
    voice_id:str
    text:str
    sr:int
    sdp_ratio:Optional[float] = 0.2
    noise_scale:Optional[float] = 0.6
    noise_scale_w:Optional[float] =  0.8
    speed:Optional[float] = 1.0
    
app = FastAPI()

device = 'cpu'
models = {
    'EN': TTS(language='EN', device=device),
    # 'ES': TTS(language='ES', device=device),
    # 'FR': TTS(language='FR', device=device),
    'ZH': TTS(language='ZH', device=device),
    # 'JP': TTS(language='JP', device=device),
    # 'KR': TTS(language='KR', device=device),
}
speaker_ids = models['EN'].hps.data.spk2id
default_text_dict = {
    'EN': 'The field of text-to-speech has seen rapid development recently.',
    'ES': 'El campo de la conversión de texto a voz ha experimentado un rápido desarrollo recientemente.',
    'FR': 'Le domaine de la synthèse vocale a connu un développement rapide récemment',
    'ZH': 'text-to-speech 领域近年来发展迅速',
    'JP': 'テキスト読み上げの分野は最近急速な発展を遂げています',
    'KR': '최근 텍스트 음성 변환 분야가 급속도로 발전하고 있습니다.',    
}

# Define the request body model
class TTSRequest(BaseModel):
    text: str
    language: str
    speaker: str
    speed: float

async def synthesize_async(speaker: str, text: str, speed: float, language: str):
    if language not in models:
        raise HTTPException(status_code=400, detail="Language not supported")
    
    bio = io.BytesIO()
    model = models[language]
    start_time = time.time()
    model.tts_to_file(text, model.hps.data.spk2id[speaker], bio, speed=speed, format='wav')
    end_time = time.time()
    return bio.getvalue()

@app.post("/synthesize/")
async def synthesize(request: TTSRequest):
    __t = time.time()
    print("Started the saynth")
    try:
        audio = synthesize_async(request.speaker, request.text, request.speed, request.language)
        print("Ending the sync")
        totalTime=time.time() - __t
        return {"audio": audio.hex(),"Time":totalTime} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# # INFO:
# #     Command to run: uvicorn fastApi:app --reload
