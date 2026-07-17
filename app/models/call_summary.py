from sqlalchemy import CHAR, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class CallSummary(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "call_summary"

    call_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("calls.id"), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    lead_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)  # positive/neutral/negative
    important_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)

    call: Mapped["Call"] = relationship(back_populates="summary")
