"""Checks that the Alembic migrations are complete, reversible and match the models."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from app import models  # noqa: F401  (registers tables with Base)
from app.db.base import Base
from tests import migrations
from tests.conftest import throwaway_schema


def test_there_is_a_single_migration_head():
    script = ScriptDirectory.from_config(migrations.alembic_config(connection=None))

    assert len(script.get_heads()) == 1


def test_migrations_match_models_and_are_reversible():
    with throwaway_schema("test_careerops_migrations") as engine, engine.connect() as conn:
        migrations.upgrade(conn)
        conn.commit()

        # The schema built by migrations must match the SQLAlchemy models exactly.
        diff = compare_metadata(MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata)
        assert diff == [], f"Models and migrations differ - create a new migration: {diff}"

        migrations.downgrade(conn)
        conn.commit()
        assert set(inspect(conn).get_table_names()) <= {"alembic_version"}

        migrations.upgrade(conn)
        conn.commit()
        assert "applications" in inspect(conn).get_table_names()


# ---------------------------------------------- status/timestamps migration (41cc45136ccd)

BASELINE = "574c59098917"
WORKFLOW = "41cc45136ccd"


def _insert(conn, *statuses):
    for status in statuses:
        conn.execute(
            text("INSERT INTO applications (company, position, location, status, notes) VALUES ('A','B','C',:s,'')"),
            {"s": status},
        )
    conn.commit()


def _revision(conn):
    return MigrationContext.configure(conn).get_current_revision()


def test_workflow_migration_normalises_existing_statuses_and_fills_timestamps():
    with throwaway_schema("test_careerops_mig_data") as engine, engine.connect() as conn:
        migrations.upgrade(conn, BASELINE)
        conn.commit()
        _insert(conn, "Applied", " interview ", "OFFER", "rejected")

        migrations.upgrade(conn, WORKFLOW)
        conn.commit()

        rows = conn.execute(text("SELECT status, created_at, updated_at FROM applications ORDER BY id")).all()
        assert [r.status for r in rows] == ["Applied", "Interview", "Offer", "Rejected"]
        assert all(r.created_at is not None and r.updated_at is not None for r in rows)
        assert any(c["name"] == "ck_applications_status" for c in inspect(conn).get_check_constraints("applications"))


def test_workflow_migration_stops_on_unknown_status_and_changes_nothing():
    with throwaway_schema("test_careerops_mig_unknown") as engine, engine.connect() as conn:
        migrations.upgrade(conn, BASELINE)
        conn.commit()
        _insert(conn, " applied ", "Pending")

        with pytest.raises(DBAPIError, match=r"unknown status values found: 'Pending' \(1 rows\)"):
            migrations.upgrade(conn, WORKFLOW)
        conn.rollback()

        # Still at the baseline, with the original data untouched (even the normalisable row).
        assert _revision(conn) == BASELINE
        assert conn.execute(text("SELECT status FROM applications ORDER BY id")).scalars().all() == [
            " applied ",
            "Pending",
        ]
        assert "created_at" not in {c["name"] for c in inspect(conn).get_columns("applications")}


def test_workflow_migration_downgrade_keeps_rows_and_statuses():
    with throwaway_schema("test_careerops_mig_down") as engine, engine.connect() as conn:
        migrations.upgrade(conn, WORKFLOW)
        conn.commit()
        _insert(conn, "Interview", "Offer")

        migrations.downgrade(conn, BASELINE)
        conn.commit()

        assert _revision(conn) == BASELINE
        assert conn.execute(text("SELECT status FROM applications ORDER BY id")).scalars().all() == [
            "Interview",
            "Offer",
        ]
        assert {"created_at", "updated_at"}.isdisjoint(c["name"] for c in inspect(conn).get_columns("applications"))
