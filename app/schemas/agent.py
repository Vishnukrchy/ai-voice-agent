from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    voice: str = "Rachel"
    language: str = "en"
    temperature: float = Field(default=0.4, ge=0.0, le=1.0)
    prompt: str = Field(min_length=1)
    greeting_message: str = Field(min_length=1)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    voice: str | None = None
    language: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    prompt: str | None = None
    greeting_message: str | None = None
    is_active: bool | None = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
