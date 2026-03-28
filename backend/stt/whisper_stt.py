from faster_whisper import WhisperModel
import numpy as np


class WhisperSTT:
    """
    Speech-to-Text module using Whisper Turbo (quantized).
    """

    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        compute_type: str = "int8",
        device: str = "cpu"
    ):
        print("🧠 Loading Whisper Turbo (quantized)...")
        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        print("✅ Whisper model loaded")

    def transcribe(self, audio: np.ndarray):
        """
        Transcribe a 16kHz mono float32 audio chunk.
        """

        if audio is None or len(audio) == 0:
            return "", None

        audio = audio.astype("float32")

        segments, info = self.model.transcribe(audio)

        text = " ".join(segment.text.strip() for segment in segments)

        return text.strip(), info.language