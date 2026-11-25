"""To add a transcriber: subclass Transcriber, add its TranscriberName, register it here."""

from multicaptcha.config import Settings
from multicaptcha.transcribers.base import Transcriber, TranscriberName
from multicaptcha.transcribers.whisper import WhisperTranscriber


def build_transcribers(settings: Settings) -> dict[TranscriberName, Transcriber]:
    return {
        TranscriberName.WHISPER: WhisperTranscriber(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
        ),
    }
