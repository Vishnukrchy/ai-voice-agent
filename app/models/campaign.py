import enum

from sqlalchemy import CHAR, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    paused = "paused"
    completed = "completed"


class Campaign(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("agents.id"), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.draft, nullable=False)

    agent: Mapped["Agent"] = relationship(back_populates="campaigns")
    calls: Mapped[list["Call"]] = relationship(back_populates="campaign")
