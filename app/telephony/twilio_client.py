"""Twilio Voice API wrapper: places outbound calls and connects them to our
TwiML/Media Streams WebSocket endpoint for real-time audio."""
from twilio.rest import Client

from app.config import settings
from app.utils.logger import logger

_client: Client | None = None


def get_twilio_client() -> Client:
    global _client
    if _client is None:
        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


def place_outbound_call(to_number: str, call_id: str) -> str:
    """Initiates an outbound call. Twilio will fetch TwiML from our
    /telephony/voice/{call_id} endpoint, which connects the call to our
    Media Streams WebSocket for real-time audio exchange.

    Returns the Twilio call SID.
    """
    client = get_twilio_client()
    call = client.calls.create(
        to=to_number,
        from_=settings.twilio_phone_number,
        url=f"{settings.base_url}/api/telephony/voice/{call_id}",
        record=True,
        status_callback=f"{settings.base_url}/api/telephony/status/{call_id}",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )
    logger.info(f"Twilio call initiated: sid={call.sid} to={to_number} call_id={call_id}")
    return call.sid


def end_call(twilio_call_sid: str) -> None:
    client = get_twilio_client()
    client.calls(twilio_call_sid).update(status="completed")
    logger.info(f"Twilio call ended: sid={twilio_call_sid}")


def get_recording_url(twilio_call_sid: str) -> str | None:
    """Fetches the recording URL for a completed call, if available."""
    client = get_twilio_client()
    recordings = client.recordings.list(call_sid=twilio_call_sid, limit=1)
    if not recordings:
        return None
    recording = recordings[0]
    return f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
