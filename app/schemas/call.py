from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    full_name: str
    phone: str = Field(min_length=8, max_length=20)
    email: str | None = None
    city: str | None = None
    state: str | None = None


class CustomerResponse(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class CampaignCreate(BaseModel):
    name: str
    agent_id: str


class CampaignResponse(CampaignCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    created_at: datetime


class StartCallRequest(BaseModel):
    agent_id: str
    customer_id: str
    campaign_id: str | None = None


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    customer_id: str
    campaign_id: str | None
    status: str
    direction: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    created_at: datetime


class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    speaker: str
    message: str
    timestamp: datetime


class CallSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    call_id: str
    summary: str
    lead_score: float | None
    sentiment: str | None
    important_notes: str | None
    next_action: str | None


class ExtractedInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    call_id: str
    name: str | None
    age: int | None
    gender: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    interested_product: str | None
    budget: str | None
    lead_score: float | None
    interest_level: str | None
    follow_up_required: bool | None
    next_follow_up_date: date | None
    reason: str | None
