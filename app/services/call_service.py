from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.call import Call, CallStatus
from app.models.customer import Customer
from app.repositories.base import BaseRepository
from app.schemas.call import StartCallRequest
from app.telephony.twilio_client import end_call as twilio_end_call
from app.telephony.twilio_client import place_outbound_call
from app.utils.logger import logger


class CallService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.call_repo = BaseRepository(Call, db)

    async def start_call(self, payload: StartCallRequest) -> Call:
        agent = await self.db.get(Agent, payload.agent_id)
        if agent is None or not agent.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active agent not found")

        customer = await self.db.get(Customer, payload.customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        call = await self.call_repo.create(
            agent_id=agent.id,
            customer_id=customer.id,
            campaign_id=payload.campaign_id,
            status=CallStatus.queued,
        )

        try:
            call_sid = place_outbound_call(to_number=customer.phone, call_id=call.id)
            call = await self.call_repo.update(call, twilio_call_sid=call_sid, status=CallStatus.ringing)
        except Exception:
            logger.exception(f"Failed to place outbound call for call_id={call.id}")
            call = await self.call_repo.update(call, status=CallStatus.failed)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to initiate call via Twilio")

        return call

    async def end_call(self, call_id: str) -> Call:
        call = await self.call_repo.get(call_id)
        if call is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

        if call.twilio_call_sid:
            try:
                twilio_end_call(call.twilio_call_sid)
            except Exception:
                logger.exception(f"Failed to end Twilio call for call_id={call_id}")

        return await self.call_repo.update(
            call, status=CallStatus.completed, ended_at=datetime.utcnow()
        )
