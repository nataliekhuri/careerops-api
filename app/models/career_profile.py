from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CareerProfile(Base):
    """What the AI assistant knows about a user's career. One per user, private to them."""

    __tablename__ = "career_profiles"
    __table_args__ = (CheckConstraint("years_experience BETWEEN 0 AND 60", name="years_experience"),)

    # The user id is the primary key: a user has at most one profile. Deleting the
    # user deletes the profile.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    headline: Mapped[str] = mapped_column(String(255), default="", server_default="")
    target_role: Mapped[str] = mapped_column(String(255), default="", server_default="")
    years_experience: Mapped[int | None] = mapped_column(Integer)
    # A JSON array of skill names, e.g. ["Python", "PostgreSQL"].
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    cv_text: Mapped[str] = mapped_column(Text, default="", server_default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.clock_timestamp()
    )
