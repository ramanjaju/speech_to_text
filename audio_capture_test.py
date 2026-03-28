import sounddevice as sd
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

# --------------------
# Audio parameters
# --------------------
SAMPLE_RATE = 16000
DURATION = 10  # seconds

# --------------------
# Record audio
# --------------------
print("🎙️ Recording...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32"
)
sd.wait()
print("✅ Done recording")

print("Audio shape:", audio.shape)

# --------------------
# Save audio to file
# --------------------
sf.write("test.wav", audio, SAMPLE_RATE)
print("💾 Audio saved as test.wav")

# --------------------
# Load Whisper Turbo (quantized)
# --------------------
print("🧠 Loading Whisper Turbo model...")
model = WhisperModel(
    "large-v3-turbo",
    device="cpu",          # Apple Silicon handled internally
    compute_type="int8"    # quantized inference
)
print("✅ Model loaded")

# --------------------
# Transcribe audio
# --------------------
print("📝 Transcribing...")
segments, info = model.transcribe("test.wav")

print(f"Detected language: {info.language}")

for segment in segments:
    print(segment.text)
