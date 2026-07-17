"""Text-to-speech using the ElevenLabs API."""
from pathlib import Path

from elevenlabs.client import ElevenLabs
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import logger

_client: ElevenLabs | None = None


def get_elevenlabs_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def synthesize_speech(text: str, voice: str, output_path: str) -> str:
    """Converts text to speech and writes audio (mp3) to output_path.
    Returns the path written. Twilio Media Streams require mu-law 8kHz —
    downstream code should transcode this before sending on the WS if
    streaming directly, or Twilio's <Play> can consume mp3 directly for
    the non-streaming call flow."""
    client = get_elevenlabs_client()
    audio_stream = client.text_to_speech.convert(
        voice_id=voice,
        text=text,
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    logger.debug(f"TTS synthesized {len(text)} chars -> {output_path}")
    return str(path)
