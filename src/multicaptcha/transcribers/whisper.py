import asyncio
import io

from faster_whisper import WhisperModel

from multicaptcha.core.errors import TranscriptionError
from multicaptcha.transcribers.base import Transcriber


class WhisperTranscriber(Transcriber):
    def __init__(self, model: str, device: str, compute_type: str) -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    async def start(self) -> None:
        self._model = await asyncio.to_thread(
            WhisperModel,
            self._model_name,
            device=self._device,
            compute_type=self._compute_type,
        )

    async def stop(self) -> None:
        self._model = None

    async def transcribe(self, audio: bytes) -> str:
        if self._model is None:
            raise TranscriptionError("Whisper model is not loaded")
        try:
            return await asyncio.to_thread(self._run, self._model, audio)
        except Exception as e:
            raise TranscriptionError(f"Whisper failed: {e}") from e

    @staticmethod
    def _run(model: WhisperModel, audio: bytes) -> str:
        segments, _ = model.transcribe(io.BytesIO(audio), language="en")
        return " ".join(segment.text.strip() for segment in segments)
