"""Speech-to-text using faster-whisper. Model is loaded once and reused
across requests/calls (loading is the expensive part)."""
from faster_whisper import WhisperModel

from app.utils.logger import logger

_model: WhisperModel | None = None


def get_whisper_model() -> WhisperModel:
    global _model
    if _model is None:
        # "small" balances latency vs accuracy for phone-quality (8kHz) audio.
        # Switch to "base" for lower latency or "medium" for higher accuracy.
        _model = WhisperModel("small", device="cpu", compute_type="int8")
        logger.info("faster-whisper model loaded (small, cpu, int8)")
    return _model


def transcribe_audio(audio_path: str, language: str = "en") -> str:
    """Transcribes an audio file (wav/mp3) to text."""
    model = get_whisper_model()
    segments, _info = model.transcribe(audio_path, language=language, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments)
    logger.debug(f"STT transcribed: {text[:200]}")
    return text.strip()
