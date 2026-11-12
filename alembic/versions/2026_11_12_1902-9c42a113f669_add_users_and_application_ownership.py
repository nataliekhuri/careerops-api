"""add users and application ownership

Changes:

1. Creates the "users" table (id, unique lower-case email, Argon2 password hash,
   full name, active flag, timestamps).
2. Adds applications.user_id: every application belongs to one user. Deleting a
   user deletes their applications (ON DELETE CASCADE).

Existing applications have no owner and the migration cannot guess one, so it
STOPS (and changes nothing) if the applications table contains any rows. Assign or
export those rows first. The whole migration runs in one transaction.

Downgrade drops user_id and the users table (all accounts are lost; application
rows are kept).

Revision ID: 9c42a113f669
Revises: 41cc45136ccd
Create Date: 2026-11-12 19:02:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c42a113f669"
down_revision: str | Sequence[str] | None = "41cc45136ccd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Stop before changing anything if there are applications without an owner.
    op.execute(
        """
        DO $$
        DECLARE existing bigint;
        BEGIN
            SELECT count(*) INTO existing FROM applications;
            IF existing > 0 THEN
                RAISE EXCEPTION 'Migration stopped: % existing application(s) have no owner. Assign them to a user (or export and remove them) before running this migration. Nothing was changed.', existing;
            END IF;
        END $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("users_pkey")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.add_column("applications", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        op.f("fk_applications_user_id_users"), "applications", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_constraint(op.f("fk_applications_user_id_users"), "applications", type_="foreignkey")
    op.drop_column("applications", "user_id")
    op.drop_table("users")
