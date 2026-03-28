from audio.mic import MicrophoneStream
import numpy as np

mic = MicrophoneStream(chunk_duration=2)
mic.start()

print("🎙️ Speak something... (Ctrl+C to stop)")

try:
    while True:
        chunk = mic.read()
        print("Received audio chunk:", chunk.shape)
except KeyboardInterrupt:
    mic.stop()
