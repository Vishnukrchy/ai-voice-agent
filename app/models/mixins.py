"""Reusable mixins for ORM models."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPKMixin:
    """UUID primary key stored as CHAR(36) for MySQL portability."""
    id: Mapped[str] = mapped_column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )


class TimestampMixin:
    """created_at / updated_at columns, DB-side defaults."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
