from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.call import Call
from app.models.call_summary import CallSummary
from app.models.conversation_message import ConversationMessage
from app.models.extracted_information import ExtractedInformation
from app.models.user import User
from app.schemas.call import (
    CallResponse,
    CallSummaryResponse,
    ConversationMessageResponse,
    ExtractedInfoResponse,
    StartCallRequest,
)
from app.services.call_service import CallService
from app.workers.tasks import process_call_task

router = APIRouter(prefix="/api", tags=["Calls"])


@router.post("/call/start", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def start_call(
    payload: StartCallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await CallService(db).start_call(payload)


@router.post("/call/end", response_model=CallResponse)
async def end_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    call = await CallService(db).end_call(call_id)
    # Kick off AI summary + extraction as a background job so this request
    # returns immediately.
    process_call_task.delay(call_id=call.id, twilio_call_sid=call.twilio_call_sid)
    return call


@router.get("/calls", response_model=list[CallResponse])
async def list_calls(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Call).limit(limit).offset(offset).order_by(Call.created_at.desc()))
    return list(result.scalars().all())


@router.get("/call/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    call = await db.get(Call, call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return call


@router.get("/transcript/{call_id}", response_model=list[ConversationMessageResponse])
async def get_transcript(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.call_id == call_id)
        .order_by(ConversationMessage.timestamp)
    )
    return list(result.scalars().all())


@router.get("/summary/{call_id}", response_model=CallSummaryResponse)
async def get_summary(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(CallSummary).where(CallSummary.call_id == call_id))
    summary = result.scalar_one_or_none()
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not yet available")
    return summary


@router.get("/extracted-info/{call_id}", response_model=ExtractedInfoResponse)
async def get_extracted_info(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(ExtractedInformation).where(ExtractedInformation.call_id == call_id))
    info = result.scalar_one_or_none()
    if info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracted info not yet available")
    return info
