"""
Twilio calls these endpoints directly (not our frontend), so there is no
JWT here — instead we validate the Twilio request signature to make sure
requests genuinely originate from Twilio.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.request_validator import RequestValidator

from app.config import settings
from app.database.session import get_db
from app.models.call import Call, CallStatus
from app.telephony.twiml_builder import build_stream_twiml
from app.utils.logger import logger

router = APIRouter(prefix="/api/telephony", tags=["Telephony Webhooks"])

_validator = RequestValidator(settings.twilio_auth_token)


async def _verify_twilio_signature(request: Request) -> bool:
    signature = request.headers.get("X-Twilio-Signature", "")
    form = await request.form()
    url = str(request.url)
    return _validator.validate(url, dict(form), signature)


@router.post("/voice/{call_id}")
async def voice_webhook(call_id: str, request: Request):
    """Twilio fetches this URL once the call is answered; we respond with
    TwiML that connects the call to our real-time Media Streams WebSocket."""
    if not settings.debug and not await _verify_twilio_signature(request):
        logger.warning(f"Rejected Twilio webhook with invalid signature for call {call_id}")
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    twiml = build_stream_twiml(call_id)
    return Response(content=twiml, media_type="application/xml")


@router.post("/status/{call_id}")
async def status_callback(call_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Twilio posts call lifecycle events (ringing, answered, completed) here."""
    if not settings.debug and not await _verify_twilio_signature(request):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    form = await request.form()
    call_status = form.get("CallStatus", "")
    logger.info(f"Twilio status callback | call={call_id} status={call_status}")

    call = await db.get(Call, call_id)
    if call is not None:
        status_map = {
            "ringing": CallStatus.ringing,
            "in-progress": CallStatus.in_progress,
            "completed": CallStatus.completed,
            "no-answer": CallStatus.no_answer,
            "busy": CallStatus.busy,
            "failed": CallStatus.failed,
        }
        if call_status in status_map:
            call.status = status_map[call_status]

            now = datetime.utcnow()
            if call_status == "in-progress" and call.started_at is None:
                call.started_at = now
            elif call_status in ("completed", "no-answer", "busy", "failed") and call.ended_at is None:
                call.ended_at = now
                if call.started_at is not None:
                    call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())

            await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
