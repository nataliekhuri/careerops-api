from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApplicationStatus(StrEnum):
    """Allowed stages of a job application."""

    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


STATUS_VALUES = tuple(s.value for s in ApplicationStatus)


class Application(Base):
    """A job application stored in the "applications" table."""

    __tablename__ = "applications"
    __table_args__ = (
        # Enforced by the database too, not only by the API.
        CheckConstraint(
            "status IN (" + ", ".join(f"'{v}'" for v in STATUS_VALUES) + ")",
            name="status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50),
        default=ApplicationStatus.APPLIED.value,
        server_default=ApplicationStatus.APPLIED.value,
        index=True,
    )
    location: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # clock_timestamp() (not now()) so the value reflects the moment of the change.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )
