from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Setting(Base, UUIDPKMixin, TimestampMixin):
    """Admin-editable runtime settings (e.g. default voice, retry limits) stored as key/value."""
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
