import enum
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class CallStatus(str, enum.Enum):
    queued = "queued"
    ringing = "ringing"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    no_answer = "no_answer"
    busy = "busy"


class CallDirection(str, enum.Enum):
    outbound = "outbound"
    inbound = "inbound"


class Call(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "calls"

    agent_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("agents.id"), nullable=False)
    campaign_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("campaigns.id"), nullable=True)
    customer_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("customers.id"), nullable=False)

    twilio_call_sid: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    status: Mapped[CallStatus] = mapped_column(Enum(CallStatus), default=CallStatus.queued, nullable=False)
    direction: Mapped[CallDirection] = mapped_column(Enum(CallDirection), default=CallDirection.outbound, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="calls")
    campaign: Mapped["Campaign"] = relationship(back_populates="calls")
    customer: Mapped["Customer"] = relationship(back_populates="calls")

    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    summary: Mapped["CallSummary"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
    recording: Mapped["CallRecording"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
    extracted_info: Mapped["ExtractedInformation"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
