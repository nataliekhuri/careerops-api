from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.interview import Interview
    from app.models.user import User


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
        # Lets interviews reference (id, user_id) so their owner must match.
        UniqueConstraint("id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Owner. Deleting a user deletes their applications.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(255))
    # Optional link to a saved company. Deleting the company keeps the application.
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), index=True)
    position: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50),
        default=ApplicationStatus.APPLIED.value,
        server_default=ApplicationStatus.APPLIED.value,
        index=True,
    )
    location: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="")
    # The job posting, used by the AI assistant. Empty when not provided.
    job_description: Mapped[str] = mapped_column(Text, default="", server_default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # clock_timestamp() (not now()) so the value reflects the moment of the change.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )

    user: Mapped["User"] = relationship(back_populates="applications")
    company_ref: Mapped["Company | None"] = relationship(back_populates="applications")
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", passive_deletes=True
    )
