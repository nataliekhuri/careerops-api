"""Registration, login, tokens and account management."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import ALGORITHM, create_access_token
from app.models.user import User
from tests.conftest import TEST_PASSWORD

GOOD = {"email": "Ann@Example.com", "password": "correct-horse-7", "full_name": "Ann Example"}


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


# ---------------------------------------------------------------- registration


def test_register_creates_user_without_exposing_the_password(anon_client, db_session):
    response = anon_client.post("/auth/register", json=GOOD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ann@example.com"  # stored lower-case
    assert body["full_name"] == "Ann Example"
    assert set(body) == {"id", "email", "full_name", "created_at"}
    stored = db_session.scalar(select(User).where(User.email == "ann@example.com"))
    assert stored.hashed_password.startswith("$argon2id$")
    assert GOOD["password"] not in stored.hashed_password


def test_duplicate_email_is_rejected_case_insensitively(anon_client):
    assert anon_client.post("/auth/register", json=GOOD).status_code == 201

    response = anon_client.post("/auth/register", json={**GOOD, "email": "ANN@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "An account with this email already exists"}


@pytest.mark.parametrize(
    "changes",
    [
        {"email": "not-an-email"},
        {"password": "short1"},
        {"password": "x" * 129},
        {"password": "onlyletters"},
        {"password": "1234567890"},
        {"password": "        "},
        {"full_name": "x" * 256},
        {"is_admin": True},
    ],
)
def test_invalid_registration_returns_422(anon_client, changes):
    assert anon_client.post("/auth/register", json={**GOOD, **changes}).status_code == 422


# ----------------------------------------------------------------------- login


def test_login_returns_a_bearer_token_that_works(anon_client, make_client):
    anon_client.post("/auth/register", json=GOOD)

    response = login(anon_client, "ANN@example.com", GOOD["password"])

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == get_settings().access_token_expire_minutes * 60
    me = make_client(None).get("/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ann@example.com"


@pytest.mark.parametrize(
    ("email", "password"), [("owner@example.com", "wrong-password-1"), ("nobody@example.com", "x1")]
)
def test_wrong_credentials_get_the_same_generic_error(anon_client, user, email, password):
    response = login(anon_client, email, password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_inactive_user_cannot_log_in_or_use_a_token(anon_client, client, user, db_session):
    user.is_active = False
    db_session.commit()

    assert login(anon_client, user.email, TEST_PASSWORD).status_code == 401
    assert client.get("/users/me").status_code == 401


# ---------------------------------------------------------------------- tokens


def test_protected_endpoints_require_a_token(anon_client):
    for method, path in [
        ("GET", "/applications"),
        ("POST", "/applications"),
        ("GET", "/applications/1"),
        ("PUT", "/applications/1"),
        ("PATCH", "/applications/1"),
        ("DELETE", "/applications/1"),
        ("GET", "/users/me"),
        ("PATCH", "/users/me"),
        ("POST", "/users/me/password"),
        ("DELETE", "/users/me"),
    ]:
        response = anon_client.request(method, path, json={})
        assert response.status_code == 401, (method, path)
        assert response.headers["WWW-Authenticate"] == "Bearer"


def _token(user_id, secret=None, **overrides):
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=5), "type": "access", **overrides}
    secret = secret or get_settings().jwt_secret_key.get_secret_value()
    return jwt.encode({k: v for k, v in payload.items() if v is not None}, secret, algorithm=ALGORITHM)


@pytest.mark.parametrize(
    "make_token",
    [
        lambda uid: "not-a-jwt",
        lambda uid: _token(uid, secret="a-different-secret-that-is-long-enough-xx"),
        lambda uid: _token(uid, exp=datetime.now(UTC) - timedelta(seconds=1)),
        lambda uid: _token(uid, type="refresh"),
        lambda uid: _token(uid, exp=None),
        lambda uid: _token("abc"),
        lambda uid: _token(999_999),
        lambda uid: jwt.encode({"sub": str(uid), "type": "access"}, "", algorithm="none"),
    ],
    ids=["garbage", "wrong-secret", "expired", "wrong-type", "no-expiry", "bad-subject", "unknown-user", "alg-none"],
)
def test_invalid_tokens_are_rejected(anon_client, user, make_token):
    response = anon_client.get("/users/me", headers={"Authorization": f"Bearer {make_token(user.id)}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_tokens_expire_after_the_configured_time(user):
    token, lifetime = create_access_token(user.id, expires_minutes=15)
    claims = jwt.decode(token, get_settings().jwt_secret_key.get_secret_value(), algorithms=[ALGORITHM])

    assert lifetime == 900
    assert claims["exp"] - claims["iat"] == 900


# --------------------------------------------------------------------- profile


def test_read_and_update_profile(client):
    assert client.get("/users/me").json()["email"] == "owner@example.com"

    response = client.patch("/users/me", json={"full_name": "  New Name  "})

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_profile_update_cannot_change_email_or_password(client):
    assert client.patch("/users/me", json={"full_name": "A", "email": "x@example.com"}).status_code == 422


def test_change_password(client, anon_client):
    wrong = client.post("/users/me/password", json={"current_password": "nope", "new_password": "new-password-9"})
    assert wrong.status_code == 400

    ok = client.post("/users/me/password", json={"current_password": TEST_PASSWORD, "new_password": "new-password-9"})
    assert ok.status_code == 204

    assert login(anon_client, "owner@example.com", TEST_PASSWORD).status_code == 401
    assert login(anon_client, "owner@example.com", "new-password-9").status_code == 200


def test_delete_account_requires_password_and_removes_its_applications(client, anon_client, payload, db_session):
    client.post("/applications", json=payload)

    assert client.request("DELETE", "/users/me", json={"password": "wrong"}).status_code == 400
    assert client.request("DELETE", "/users/me", json={"password": TEST_PASSWORD}).status_code == 204

    assert client.get("/users/me").status_code == 401
    assert login(anon_client, "owner@example.com", TEST_PASSWORD).status_code == 401
    assert db_session.execute(select(User)).first() is None


def test_api_refuses_to_start_without_a_jwt_secret(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.config import Settings
    from app.main import app

    monkeypatch.setattr("app.main.get_settings", lambda: Settings(_env_file=None, db_password="x", jwt_secret_key=None))

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"), TestClient(app):
        pass


def test_short_jwt_secret_is_rejected():
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None, db_password="x", jwt_secret_key="too-short")
