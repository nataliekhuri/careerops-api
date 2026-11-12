"""add status workflow and timestamps

Changes to the "applications" table:

1. Normalises existing status values to the allowed set, ignoring case and
   surrounding spaces (e.g. " interview " -> "Interview"). If any row has a
   status that is NOT one of the allowed values, the migration stops with an
   error and changes nothing (the whole migration runs in one transaction).
2. Adds a CHECK constraint so only allowed statuses can be stored.
3. Gives the status column a database default of 'Applied'.
4. Adds created_at and updated_at (timestamp with time zone, NOT NULL).
   Existing rows get the time the migration runs, because no earlier
   history exists.
5. Adds an index on status for filtering.

Downgrade removes all of the above. Note: it drops created_at/updated_at,
so those values are lost on downgrade. Statuses and all other data are kept.

Revision ID: 41cc45136ccd
Revises: 574c59098917
Create Date: 2026-11-12 15:28:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "41cc45136ccd"
down_revision: Union[str, Sequence[str], None] = "574c59098917"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen copy of the allowed statuses at the time of this migration.
# (Do not import from app code: migrations must not change if the app changes later.)
STATUSES = ("Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn")
STATUS_LIST_SQL = ", ".join(f"'{s}'" for s in STATUSES)


def upgrade() -> None:
    # Plain SQL (values are the fixed constants above), so `alembic upgrade --sql`
    # shows exactly what will run.

    # 1. Normalise existing values case-insensitively.
    for status in STATUSES:
        op.execute(
            f"UPDATE applications SET status = '{status}' "
            f"WHERE lower(btrim(status)) = lower('{status}') AND status <> '{status}'"
        )

    # Stop (and roll back everything) if any status is still not allowed.
    op.execute(
        f"""
        DO $$
        DECLARE unknown_values text;
        BEGIN
            SELECT string_agg(format('%L (%s rows)', status, n), ', ' ORDER BY status)
              INTO unknown_values
              FROM (SELECT status, count(*) AS n FROM applications
                    WHERE status NOT IN ({STATUS_LIST_SQL}) GROUP BY status) AS bad;
            IF unknown_values IS NOT NULL THEN
                RAISE EXCEPTION 'Migration stopped: unknown status values found: %. Update them to one of {", ".join(STATUSES)} and run the migration again. Nothing was changed.', unknown_values;
            END IF;
        END $$;
        """
    )

    # 2-3. Constraint and default.
    op.create_check_constraint(op.f("ck_applications_status"), "applications", f"status IN ({STATUS_LIST_SQL})")
    op.alter_column("applications", "status", server_default="Applied", existing_type=sa.String(50), existing_nullable=False)

    # 4. Timestamps (existing rows get the migration time).
    op.add_column(
        "applications",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. Index for filtering by status.
    op.create_index(op.f("ix_applications_status"), "applications", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_column("applications", "updated_at")
    op.drop_column("applications", "created_at")
    op.alter_column("applications", "status", server_default=None, existing_type=sa.String(50), existing_nullable=False)
    op.drop_constraint(op.f("ck_applications_status"), "applications", type_="check")
