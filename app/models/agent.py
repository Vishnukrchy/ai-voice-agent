from sqlalchemy import Boolean, CHAR, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Agent(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice: Mapped[str] = mapped_column(String(100), nullable=False, default="Rachel")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.4)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    greeting_message: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)

    knowledge_files: Mapped[list["KnowledgeFile"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    calls: Mapped[list["Call"]] = relationship(back_populates="agent")
