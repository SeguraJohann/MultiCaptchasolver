from abc import ABC, abstractmethod
from enum import StrEnum


class TranscriberName(StrEnum):
    WHISPER = "whisper"


class Transcriber(ABC):
    """Turns challenge audio (mp3 bytes) into raw text."""

    async def start(self) -> None:
        """Load models or open clients. Called once at startup."""

    async def stop(self) -> None:
        """Release resources."""

    @abstractmethod
    async def transcribe(self, audio: bytes) -> str: ...
