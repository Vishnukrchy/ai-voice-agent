from sqlalchemy import CHAR, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class CallRecording(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "call_recordings"

    call_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("calls.id"), unique=True, nullable=False)
    recording_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    call: Mapped["Call"] = relationship(back_populates="recording")
