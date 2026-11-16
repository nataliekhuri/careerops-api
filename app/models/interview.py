from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class InterviewType(StrEnum):
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    OTHER = "other"


class InterviewOutcome(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _in_list(column: str, values: type[StrEnum]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v.value}'" for v in values) + ")"


class Interview(Base):
    """An interview for one of the user's applications."""

    __tablename__ = "interviews"
    __table_args__ = (
        # The (application_id, user_id) pair must match an application with the SAME
        # owner, so the database itself prevents attaching an interview to someone
        # else's application. Deleting the application deletes its interviews.
        ForeignKeyConstraint(
            ["application_id", "user_id"],
            ["applications.id", "applications.user_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(_in_list("interview_type", InterviewType), name="interview_type"),
        CheckConstraint(_in_list("outcome", InterviewOutcome), name="outcome"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 600", name="duration_minutes"),
        Index("ix_interviews_user_id_scheduled_at", "user_id", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, server_default="60")
    interview_type: Mapped[str] = mapped_column(
        String(20), default=InterviewType.VIDEO.value, server_default=InterviewType.VIDEO.value
    )
    location: Mapped[str] = mapped_column(String(500), default="", server_default="")
    interviewer: Mapped[str] = mapped_column(String(255), default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    outcome: Mapped[str] = mapped_column(
        String(20), default=InterviewOutcome.PENDING.value, server_default=InterviewOutcome.PENDING.value
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )

    application: Mapped["Application"] = relationship(back_populates="interviews")
