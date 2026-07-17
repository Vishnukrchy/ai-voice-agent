from twilio.twiml.voice_response import Connect, VoiceResponse

from app.config import settings


def build_stream_twiml(call_id: str) -> str:
    """Builds the TwiML that connects an answered call to our bidirectional
    Media Streams WebSocket, where the real-time STT -> LLM -> TTS loop runs."""
    response = VoiceResponse()
    ws_url = settings.base_url.replace("https://", "wss://").replace("http://", "ws://")
    connect = Connect()
    connect.stream(url=f"{ws_url}/ws/media-stream/{call_id}")
    response.append(connect)
    return str(response)
