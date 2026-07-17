import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.admin, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
