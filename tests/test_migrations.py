"""Checks that the Alembic migrations are complete, reversible and match the models."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app import models  # noqa: F401  (registers tables with Base)
from app.db.base import Base
from tests import migrations
from tests.conftest import throwaway_schema


def test_there_is_a_single_migration_head():
    script = ScriptDirectory.from_config(migrations.alembic_config(connection=None))

    assert len(script.get_heads()) == 1


def test_migrations_match_models_and_are_reversible():
    with throwaway_schema("test_careerops_migrations") as engine:
        with engine.connect() as conn:
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
