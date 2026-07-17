import enum
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import UUIDPKMixin


class Speaker(str, enum.Enum):
    agent = "agent"
    customer = "customer"
    system = "system"


class ConversationMessage(Base, UUIDPKMixin):
    __tablename__ = "conversation_messages"

    call_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("calls.id"), nullable=False)
    speaker: Mapped[Speaker] = mapped_column(Enum(Speaker), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    call: Mapped["Call"] = relationship(back_populates="messages")
