import numpy as np
import noisereduce as nr
from faster_whisper import WhisperModel

class WhisperSTT:
    """
    Speech-to-Text with VAD and Noise Reduction.
    """

    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        compute_type: str = "int8",
        device: str = "cpu"
    ):
        print(f"🧠 Loading {model_name} (quantized)...")
        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        print("✅ Whisper model loaded with Silero VAD filtering enabled")

    def transcribe_from_audio_np(self, audio: np.ndarray, sample_rate: int = 16000):
        """
        Transcribe a 16kHz mono float32 audio chunk with Noise Suppression and VAD.
        """

        if audio is None or len(audio) == 0:
            return "", None

        audio = audio.astype("float32")

        # 1. Background Noise Suppression (Removes stationary noise like fans)
        try:
            # We use a non-stationary method if possible, or just simple suppression
            audio = nr.reduce_noise(y=audio, sr=sample_rate, stationary=True, prop_decrease=0.7)
        except Exception as e:
            print(f"Noise reduction warning: {e}")

        # 2. Transcribe with Silero VAD (Ignores non-human sounds)
        # vad_filter=True makes Whisper ignore silent parts or non-human noise
        segments, info = self.model.transcribe(
            audio, 
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text = " ".join(segment.text.strip() for segment in segments)

        return text.strip(), info.language