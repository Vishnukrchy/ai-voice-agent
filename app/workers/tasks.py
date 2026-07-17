import asyncio

from app.workers.celery_app import celery_app
from app.utils.logger import logger


@celery_app.task(name="process_call_post_processing", bind=True, max_retries=3, default_retry_delay=30)
def process_call_task(self, call_id: str, twilio_call_sid: str | None = None):
    """Celery entrypoint: runs summary generation, structured extraction,
    and recording-URL storage for a completed call, outside the request cycle."""
    try:
        asyncio.run(_run(call_id, twilio_call_sid))
    except Exception as exc:
        logger.exception(f"post-call processing failed for call {call_id}, retrying")
        raise self.retry(exc=exc)


async def _run(call_id: str, twilio_call_sid: str | None) -> None:
    # Local imports to avoid pulling the full app/DB setup into the Celery
    # worker's import path at module load time.
    from app.database.session import AsyncSessionLocal
    from app.extraction.post_call_processor import PostCallProcessor

    async with AsyncSessionLocal() as db:
        await PostCallProcessor(db, call_id).process(twilio_call_sid)
