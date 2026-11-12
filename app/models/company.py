from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class Company(Base):
    """A company the user is interested in or has applied to. Private to its owner."""

    __tablename__ = "companies"
    __table_args__ = (
        # Names are unique per user (the API also compares them case-insensitively).
        UniqueConstraint("user_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(500), default="", server_default="")
    industry: Mapped[str] = mapped_column(String(100), default="", server_default="")
    location: Mapped[str] = mapped_column(String(255), default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )

    applications: Mapped[list["Application"]] = relationship(back_populates="company_ref")
