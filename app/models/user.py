from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class User(Base):
    """A registered user. Every application belongs to exactly one user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored lower-cased, so "Ann@Example.com" and "ann@example.com" are the same account.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
