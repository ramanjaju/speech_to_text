import sounddevice as sd
import queue
import numpy as np


class MicrophoneStream:
    """
    Real-time microphone audio stream.
    Captures audio in fixed-size chunks and exposes them via a queue.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 2.0
    ):
        """
        Args:
            sample_rate (int): Audio sample rate (Whisper expects 16kHz)
            chunk_duration (float): Length of each audio chunk in seconds
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.blocksize = int(sample_rate * chunk_duration)

        self._queue = queue.Queue()
        self._stream = None

    def _audio_callback(self, indata, frames, time, status):
        """
        This function is called automatically by sounddevice
        whenever a new chunk of audio is available.
        """
        if status:
            print("⚠️ Audio status:", status)

        # Copy audio to avoid overwriting
        self._queue.put(indata.copy())

    def start(self):
        """
        Start the microphone stream.
        """
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.blocksize,
            callback=self._audio_callback
        )
        self._stream.start()
        print("🎙️ Microphone stream started")

    def read(self) -> np.ndarray:
        """
        Blocking read of the next audio chunk.

        Returns:
            np.ndarray: 1D float32 audio array
        """
        audio_chunk = self._queue.get()
        return np.squeeze(audio_chunk)

    def stop(self):
        """
        Stop the microphone stream.
        """
        if self._stream:
            self._stream.stop()
            self._stream.close()
            print("🛑 Microphone stream stopped")
