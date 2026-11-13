"""add career profiles and job descriptions

Changes (all additive; existing rows are kept unchanged):

1. Adds applications.job_description (TEXT NOT NULL DEFAULT ''). PostgreSQL 11+
   stores a constant default without rewriting the table, so this is fast and
   existing applications simply get an empty description.
2. Creates "career_profiles": at most one per user (user_id is the primary key),
   deleted together with the user. Holds the skills, years of experience and CV text
   used by the AI career assistant.

The migration runs in one transaction. Downgrade drops career_profiles and
applications.job_description (data in those is lost; applications are kept).

Revision ID: 66ff5fb506ac
Revises: e1ea5f0b4a8d
Create Date: 2026-11-13 15:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "66ff5fb506ac"
down_revision: str | Sequence[str] | None = "e1ea5f0b4a8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. job descriptions on applications
    op.add_column("applications", sa.Column("job_description", sa.Text(), server_default="", nullable=False))

    # 2. career profiles
    op.create_table(
        "career_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("headline", sa.String(length=255), server_default="", nullable=False),
        sa.Column("target_role", sa.String(length=255), server_default="", nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("cv_text", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("years_experience BETWEEN 0 AND 60", name=op.f("ck_career_profiles_years_experience")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_career_profiles_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("career_profiles_pkey")),
    )


def downgrade() -> None:
    op.drop_table("career_profiles")
    op.drop_column("applications", "job_description")
