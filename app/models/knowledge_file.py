import enum

from sqlalchemy import CHAR, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class FileStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class KnowledgeFile(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "knowledge_files"

    agent_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("agents.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, txt
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.pending, nullable=False)

    agent: Mapped["Agent"] = relationship(back_populates="knowledge_files")
