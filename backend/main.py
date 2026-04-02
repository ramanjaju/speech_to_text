import asyncio
import numpy as np
import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from stt.whisper_stt import WhisperSTT
from translation.gemma_translator import GemmaTranslator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models (Back to the stable large-v3-turbo)
stt = WhisperSTT(model_name="large-v3-turbo", device="cpu", compute_type="int8")
translator = GemmaTranslator()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    audio_buffer = bytearray()
    BUFFER_SECONDS = 5  # Back to 5 seconds for stability
    SAMPLE_RATE = 16000
    target_lang = "Hindi"

    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                data = message["bytes"]
                audio_buffer.extend(data)

                buffer_duration = len(audio_buffer) / (SAMPLE_RATE * 2) 
                if buffer_duration >= BUFFER_SECONDS:
                    audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0

                    # Simple transcription
                    transcription, lang = stt.transcribe_from_audio_np(audio_np, SAMPLE_RATE)
                    
                    if transcription:
                        logger.info(f"Transcription: {transcription}")
                        await websocket.send_json({"type": "transcription", "text": transcription, "language": lang})

                        # Simple translation (No streaming)
                        translation = translator.translate(transcription, lang, target_lang)
                        if translation:
                            await websocket.send_json({"type": "translation", "text": translation})

                    audio_buffer.clear()
            
            elif "text" in message:
                config = json.loads(message["text"])
                if config.get("type") == "config":
                    target_lang = config.get("target_lang", "Hindi")

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        audio_buffer.clear()

# Serve Frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
