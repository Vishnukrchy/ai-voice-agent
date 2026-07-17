from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Customer(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "customers"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)

    calls: Mapped[list["Call"]] = relationship(back_populates="customer")
