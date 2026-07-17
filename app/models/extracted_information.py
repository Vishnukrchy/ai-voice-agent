from datetime import date

from sqlalchemy import CHAR, Boolean, Date, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class ExtractedInformation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "extracted_information"

    call_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("calls.id"), unique=True, nullable=False)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interested_product: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lead_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    interest_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # high/medium/low
    follow_up_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full raw JSON returned by the LLM extraction step, kept for auditability
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    call: Mapped["Call"] = relationship(back_populates="extracted_info")
