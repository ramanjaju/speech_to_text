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

import torch
import torchaudio

# Load Silero VAD model (already in requirements.txt)
# This model is very accurate and focuses on human speech boundaries
model_vad, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established with VAD.")
    
    audio_buffer = bytearray()
    SAMPLE_RATE = 16000
    target_lang = "Hindi"
    mode = "translation"
    
    # VAD State
    is_speaking = False
    silence_count = 0
    # Approx 30 chunks of silence (at 512 samples per chunk) is ~1 second pause
    MAX_SILENCE_CHUNKS = 25 

    try:
        while True:
            try:
                message = await websocket.receive()
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WS error: {e}")
                break
            
            if "bytes" in message:
                data = message["bytes"]
                audio_buffer.extend(data)
                
                # Check current chunk for speech (VAD expects specific sizes: 512, 1024, or 1536)
                chunk_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Silero VAD handles 16kHz audio perfectly
                with torch.no_grad():
                    # We only check the VAD if the chunk is large enough
                    if len(chunk_np) >= 512:
                        # Take the first 512 samples for a quick check
                        speech_prob = model_vad(torch.from_numpy(chunk_np[:512]), SAMPLE_RATE).item()
                        
                        if speech_prob > 0.4:  # Adjust sensitivity
                            is_speaking = True
                            silence_count = 0
                        elif is_speaking:
                            silence_count += 1
                
                # TRIGGER: We were speaking, and now we've paused (end of sentence)
                if is_speaking and silence_count >= MAX_SILENCE_CHUNKS:
                    audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # 1. Transcription (STT)
                    transcription, lang = stt.transcribe_from_audio_np(audio_np, SAMPLE_RATE)
                    
                    if transcription and len(transcription.strip()) > 2:
                        logger.info(f"User sentence: {transcription}")
                        await websocket.send_json({"type": "transcription", "text": transcription, "language": lang})

                        # 2. Process based on Mode
                        if mode == "chat":
                            ai_response = translator.chat(transcription)
                            if ai_response:
                                await websocket.send_json({"type": "chat_response", "text": ai_response})
                        else:
                            translation = translator.translate(transcription, lang, target_lang)
                            if translation:
                                await websocket.send_json({"type": "translation", "text": translation})

                    # RESET for the next sentence
                    audio_buffer.clear()
                    is_speaking = False
                    silence_count = 0
                
                # Safety: If buffer grows too long (20s) without a pause, process it anyway
                if len(audio_buffer) > (SAMPLE_RATE * 2 * 20):
                    is_speaking = True
                    silence_count = MAX_SILENCE_CHUNKS
            
            elif "text" in message:
                config = json.loads(message["text"])
                if config.get("type") == "config":
                    target_lang = config.get("target_lang", "Hindi")
                    mode = config.get("mode", "translation")
                    logger.info(f"Mode switched to: {mode}")

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
