import asyncio
import numpy as np
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

# Load models once at startup
# Note: large-v3-turbo is very fast. 
# For even less lag, 'distil-large-v3' or 'medium' could be used.
stt = WhisperSTT(model_name="large-v3-turbo", device="cpu", compute_type="int8")
translator = GemmaTranslator()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    audio_buffer = bytearray()
    # 2.0 seconds gives enough room for VAD to detect pauses effectively
    BUFFER_SECONDS = 2.0 
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
                    # Convert buffer to numpy array
                    audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0

                    # Transcribe
                    transcription, lang = stt.transcribe_from_audio_np(audio_np, SAMPLE_RATE)
                    
                    if transcription and len(transcription.strip()) > 1:
                        logger.info(f"Detected [{lang}]: {transcription}")
                        
                        # Send transcription to frontend immediately
                        await websocket.send_json({
                            "type": "transcription", 
                            "text": transcription, 
                            "language": lang
                        })

                        # Translate if needed
                        # We translate if source language is different from target
                        # OR if the user explicitly wants a translation.
                        if lang.lower() != target_lang.lower():
                            translation = translator.translate(transcription, lang, target_lang)
                            if translation:
                                await websocket.send_json({
                                    "type": "translation", 
                                    "text": translation
                                })
                        else:
                            # Just echo for visual consistency if languages match
                            await websocket.send_json({
                                "type": "translation", 
                                "text": transcription
                            })

                    # Clear buffer for next chunk
                    audio_buffer.clear()
            
            elif "text" in message:
                config = json.loads(message["text"])
                if config.get("type") == "config":
                    target_lang = config.get("target_lang", "Hindi")
                    logger.info(f"Target language changed to: {target_lang}")

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        audio_buffer.clear()

@app.on_event("startup")
async def startup_event():
    logger.info("Backend is live and models are loaded.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
