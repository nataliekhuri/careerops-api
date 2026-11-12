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
import secrets
from collections.abc import Callable, Iterator
from contextlib import contextmanager

# Tests sign their own tokens with a throwaway key generated for this run only.
os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.crud import user as user_crud  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from tests import migrations  # noqa: E402

TEST_PASSWORD = "test-password-123"

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
def make_user(db_session: Session) -> Callable[..., User]:
    """Create users directly in the test database."""
    counter = iter(range(1, 10_000))

    def _make(email: str | None = None, password: str = TEST_PASSWORD, full_name: str = "Test User") -> User:
        email = email or f"user{next(counter)}@example.com"
        return user_crud.create_user(db_session, UserCreate(email=email, password=password, full_name=full_name))

    return _make


@pytest.fixture
def make_client(db_session: Session) -> Iterator[Callable[[User | None], TestClient]]:
    """Create test clients; pass a user to send that user's bearer token on every request."""
    app.dependency_overrides[get_db] = lambda: db_session
    clients: list[TestClient] = []

    def _make(user: User | None = None) -> TestClient:
        test_client = TestClient(app)
        test_client.__enter__()
        clients.append(test_client)
        if user is not None:
            token, _ = create_access_token(user.id)
            test_client.headers["Authorization"] = f"Bearer {token}"
            test_client.user = user  # type: ignore[attr-defined]
        return test_client

    try:
        yield _make
    finally:
        for test_client in clients:
            test_client.__exit__(None, None, None)
        app.dependency_overrides.clear()


@pytest.fixture
def user(make_user) -> User:
    """The default signed-in user."""
    return make_user(email="owner@example.com")


@pytest.fixture
def client(make_client, user: User) -> TestClient:
    """A client signed in as the default user."""
    return make_client(user)


@pytest.fixture
def anon_client(make_client) -> TestClient:
    """A client that is not signed in."""
    return make_client(None)


@pytest.fixture
def payload() -> dict:
    return {
        "company": "Acme Corp",
        "position": "Backend Developer",
        "location": "Remote",
        "status": "Applied",
        "notes": "Referred by a former colleague",
    }
