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


# ------------------------------------------------- users/ownership migration (9c42a113f669)

USERS = "9c42a113f669"


def test_users_migration_on_empty_table_adds_users_and_ownership():
    with throwaway_schema("test_careerops_mig_users") as engine, engine.connect() as conn:
        migrations.upgrade(conn, WORKFLOW)
        conn.commit()

        migrations.upgrade(conn, USERS)
        conn.commit()

        inspector = inspect(conn)
        assert "users" in inspector.get_table_names()
        user_id = next(c for c in inspector.get_columns("applications") if c["name"] == "user_id")
        assert user_id["nullable"] is False
        fk = inspector.get_foreign_keys("applications")[0]
        assert (fk["referred_table"], fk["options"].get("ondelete")) == ("users", "CASCADE")


def test_users_migration_stops_when_applications_have_no_owner():
    with throwaway_schema("test_careerops_mig_orphans") as engine, engine.connect() as conn:
        migrations.upgrade(conn, WORKFLOW)
        conn.commit()
        _insert(conn, "Applied", "Offer")

        with pytest.raises(DBAPIError, match=r"2 existing application\(s\) have no owner"):
            migrations.upgrade(conn, USERS)
        conn.rollback()

        assert _revision(conn) == WORKFLOW
        assert "users" not in inspect(conn).get_table_names()
        assert conn.execute(text("SELECT count(*) FROM applications")).scalar() == 2


def test_users_migration_downgrade_keeps_application_rows():
    with throwaway_schema("test_careerops_mig_users_down") as engine, engine.connect() as conn:
        migrations.upgrade(conn, USERS)
        conn.commit()
        user_id = conn.execute(
            text("INSERT INTO users (email, hashed_password) VALUES ('a@example.com', 'x') RETURNING id")
        ).scalar()
        conn.execute(
            text("INSERT INTO applications (user_id, company, position, location, notes) VALUES (:u,'A','B','C','')"),
            {"u": user_id},
        )
        conn.commit()

        migrations.downgrade(conn, WORKFLOW)
        conn.commit()

        assert _revision(conn) == WORKFLOW
        assert "users" not in inspect(conn).get_table_names()
        assert conn.execute(text("SELECT count(*) FROM applications")).scalar() == 1
