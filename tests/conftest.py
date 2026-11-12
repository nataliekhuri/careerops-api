"""
Shared test fixtures.

Tests run against the real PostgreSQL server configured in .env (or environment
variables), but inside a separate, throwaway schema. The app's own tables in the
"public" schema are never read or written. The test schema is built by running the
Alembic migrations, and every test runs in a transaction that is rolled back
afterwards, so tests are isolated from each other.
"""

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from tests import migrations

TEST_SCHEMA = os.getenv("TEST_DB_SCHEMA", "test_careerops")


def check_test_schema_name(name: str) -> str:
    """Only ever create/drop a schema whose name clearly marks it as a test schema."""
    if not re.fullmatch(r"test_[a-z0-9_]+", name):
        raise RuntimeError(f"Refusing to use schema {name!r}: it must look like 'test_<name>'.")
    return name


@contextmanager
def throwaway_schema(name: str) -> Iterator[Engine]:
    """Create an empty schema, yield an engine that only sees it, then drop it."""
    name = check_test_schema_name(name)
    url = get_settings().database_url
    admin_engine = create_engine(url)
    with admin_engine.begin() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{name}" CASCADE'))
        conn.execute(text(f'CREATE SCHEMA "{name}"'))

    schema_engine = create_engine(url, connect_args={"options": f"-csearch_path={name}"})
    try:
        yield schema_engine
    finally:
        schema_engine.dispose()
        with admin_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{name}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    with throwaway_schema(TEST_SCHEMA) as test_engine:
        with test_engine.connect() as conn:
            migrations.upgrade(conn)
            conn.commit()
        yield test_engine


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def payload() -> dict:
    return {
        "company": "Acme Corp",
        "position": "Backend Developer",
        "location": "Remote",
        "status": "Applied",
        "notes": "Referred by a former colleague",
    }
