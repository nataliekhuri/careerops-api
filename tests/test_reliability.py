"""Readiness check and handling of unexpected errors."""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app


class BrokenSession:
    """Stands in for a database session when the database is unreachable or failing."""

    def __init__(self, error: Exception):
        self.error = error

    def execute(self, *args, **kwargs):
        raise self.error

    scalar = scalars = get = execute


@pytest.fixture
def broken_client():
    def use(error: Exception) -> TestClient:
        app.dependency_overrides[get_db] = lambda: BrokenSession(error)
        test_client = TestClient(app, raise_server_exceptions=False)
        # A validly signed token, so requests reach the database (which then fails).
        token, _ = create_access_token(1)
        test_client.headers["Authorization"] = f"Bearer {token}"
        return test_client

    yield use
    app.dependency_overrides.clear()


def test_ready_when_database_is_reachable(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_not_ready_when_database_is_unreachable(broken_client, caplog):
    error = OperationalError("SELECT 1", {}, Exception("connection refused: secret-host:5433"))

    with caplog.at_level(logging.WARNING):
        response = broken_client(error).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable"}
    assert "secret-host" not in response.text
    assert any("readiness" in r.message.lower() for r in caplog.records)


def test_liveness_does_not_need_the_database(broken_client):
    response = broken_client(OperationalError("x", {}, Exception("down"))).get("/health")

    assert response.status_code == 200


def test_unexpected_error_returns_generic_500_and_is_logged(broken_client, caplog):
    with caplog.at_level(logging.ERROR):
        response = broken_client(RuntimeError("internal detail: table xyz")).get("/applications")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "xyz" not in response.text
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert errors and "GET /applications" in errors[0].getMessage()
    assert errors[0].exc_info is not None


def test_database_outage_during_request_returns_503(broken_client):
    error = OperationalError("SELECT", {}, Exception("server closed the connection"))

    response = broken_client(error).get("/applications")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}


def test_database_url_has_a_connection_timeout():
    from app.core.config import Settings

    settings = Settings(_env_file=None, db_password="x", db_connect_timeout=7)

    assert settings.database_url.query["connect_timeout"] == "7"
    assert Settings(_env_file=None, db_password="x").database_url.query["connect_timeout"] == "5"
