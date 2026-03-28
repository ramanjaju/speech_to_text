from audio.mic import MicrophoneStream
from stt.whisper_stt import WhisperSTT

print("🎙️ Starting real-time speech-to-text system...")

# Initialize components
mic = MicrophoneStream(chunk_duration=10)
stt = WhisperSTT()

# Start microphone
mic.start()

print("📝 Speak into the microphone (Ctrl+C to stop)\n")

try:
    while True:
        audio_chunk = mic.read()
        text, language = stt.transcribe(audio_chunk)

        if text:
            print(f"[{language}] {text}")
except KeyboardInterrupt:
    mic.stop()
    print("\n🛑 Stopped")