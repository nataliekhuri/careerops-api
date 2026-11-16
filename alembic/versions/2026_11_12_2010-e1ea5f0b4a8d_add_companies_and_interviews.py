"""add companies and interviews

Changes (all additive; existing rows are kept unchanged):

1. Creates "companies" (per user; name unique per user).
2. Adds a UNIQUE (id, user_id) constraint on "applications" so interviews can
   reference an application together with its owner.
3. Adds applications.company_id (nullable). Deleting a company sets it to NULL,
   so applications are never deleted with their company.
4. Creates "interviews". The composite foreign key (application_id, user_id) ->
   applications (id, user_id) guarantees, in the database itself, that an
   interview always has the same owner as its application. Deleting the
   application deletes its interviews.

Existing applications get company_id = NULL. The whole migration runs in one
transaction. Downgrade removes interviews, companies and company_id (data in
those is lost; applications are kept).

Revision ID: e1ea5f0b4a8d
Revises: 9c42a113f669
Create Date: 2026-11-12 20:10:39

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1ea5f0b4a8d"
down_revision: str | Sequence[str] | None = "9c42a113f669"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. companies
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=500), server_default="", nullable=False),
        sa.Column("industry", sa.String(length=100), server_default="", nullable=False),
        sa.Column("location", sa.String(length=255), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_companies_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("companies_pkey")),
        sa.UniqueConstraint("user_id", "name", name=op.f("uq_companies_user_id")),
    )
    op.create_index(op.f("ix_companies_user_id"), "companies", ["user_id"])

    # 2. (id, user_id) must exist before interviews can reference it
    op.create_unique_constraint(op.f("uq_applications_id"), "applications", ["id", "user_id"])

    # 3. optional company link on applications
    op.add_column("applications", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_applications_company_id"), "applications", ["company_id"])
    op.create_foreign_key(
        op.f("fk_applications_company_id_companies"),
        "applications",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 4. interviews
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("interview_type", sa.String(length=20), server_default="video", nullable=False),
        sa.Column("location", sa.String(length=500), server_default="", nullable=False),
        sa.Column("interviewer", sa.String(length=255), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("outcome", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "interview_type IN ('phone', 'video', 'onsite', 'technical', 'behavioral', 'other')",
            name=op.f("ck_interviews_interview_type"),
        ),
        sa.CheckConstraint(
            "outcome IN ('pending', 'passed', 'failed', 'cancelled')", name=op.f("ck_interviews_outcome")
        ),
        sa.CheckConstraint("duration_minutes BETWEEN 1 AND 600", name=op.f("ck_interviews_duration_minutes")),
        sa.ForeignKeyConstraint(
            ["application_id", "user_id"],
            ["applications.id", "applications.user_id"],
            name=op.f("fk_interviews_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_interviews_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("interviews_pkey")),
    )
    op.create_index(op.f("ix_interviews_application_id"), "interviews", ["application_id"])
    op.create_index(op.f("ix_interviews_user_id_scheduled_at"), "interviews", ["user_id", "scheduled_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_interviews_user_id_scheduled_at"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_application_id"), table_name="interviews")
    op.drop_table("interviews")
    op.drop_constraint(op.f("fk_applications_company_id_companies"), "applications", type_="foreignkey")
    op.drop_index(op.f("ix_applications_company_id"), table_name="applications")
    op.drop_column("applications", "company_id")
    op.drop_constraint(op.f("uq_applications_id"), "applications", type_="unique")
    op.drop_index(op.f("ix_companies_user_id"), table_name="companies")
    op.drop_table("companies")
