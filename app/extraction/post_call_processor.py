from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.gemini_client import extract_structured_info, generate_summary
from app.models.call_recording import CallRecording
from app.models.call_summary import CallSummary
from app.models.conversation_message import ConversationMessage
from app.models.extracted_information import ExtractedInformation
from app.telephony.twilio_client import get_recording_url
from app.utils.logger import logger


def _parse_date(value) -> date | None:
    """Gemini returns dates as 'YYYY-MM-DD' strings (or null); the DB column
    is a real Date type, so this converts safely and never raises."""
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Could not parse next_follow_up_date value: {value!r}")
        return None


def _parse_int(value) -> int | None:
    """LLM JSON output isn't schema-guaranteed — coerce safely instead of
    letting a stray string blow up the DB insert."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class PostCallProcessor:
    """Runs after a call ends: builds the transcript, generates the AI
    summary, extracts structured lead data, and stores the recording URL.
    Intended to be invoked from a Celery background task so the HTTP
    request that ends the call doesn't block on LLM calls."""

    def __init__(self, db: AsyncSession, call_id: str):
        self.db = db
        self.call_id = call_id

    async def _build_transcript(self) -> str:
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.call_id == self.call_id)
            .order_by(ConversationMessage.timestamp)
        )
        messages = result.scalars().all()
        return "\n".join(f"{m.speaker.value}: {m.message}" for m in messages)

    async def process(self, twilio_call_sid: str | None) -> None:
        transcript = await self._build_transcript()
        if not transcript.strip():
            logger.warning(f"Call {self.call_id}: empty transcript, skipping AI post-processing")
            return

        summary_data = await generate_summary(transcript)
        self.db.add(CallSummary(
            call_id=self.call_id,
            summary=summary_data.get("summary", ""),
            lead_score=_parse_float(summary_data.get("lead_score")),
            sentiment=summary_data.get("sentiment"),
            important_notes=summary_data.get("important_notes"),
            next_action=summary_data.get("next_action"),
        ))

        extracted = await extract_structured_info(transcript)
        self.db.add(ExtractedInformation(
            call_id=self.call_id,
            name=extracted.get("name"),
            age=_parse_int(extracted.get("age")),
            gender=extracted.get("gender"),
            phone=extracted.get("phone"),
            address=extracted.get("address"),
            city=extracted.get("city"),
            state=extracted.get("state"),
            interested_product=extracted.get("interested_product"),
            budget=extracted.get("budget"),
            lead_score=_parse_float(extracted.get("lead_score")),
            interest_level=extracted.get("interest_level"),
            follow_up_required=bool(extracted.get("follow_up_required")) if extracted.get("follow_up_required") is not None else None,
            next_follow_up_date=_parse_date(extracted.get("next_follow_up_date")),
            reason=extracted.get("reason"),
            raw_json=extracted,
        ))

        if twilio_call_sid:
            recording_url = get_recording_url(twilio_call_sid)
            if recording_url:
                self.db.add(CallRecording(call_id=self.call_id, recording_url=recording_url))

        await self.db.commit()
        logger.info(f"Call {self.call_id}: post-call processing complete")
