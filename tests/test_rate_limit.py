"""Login and registration rate limiting."""

import time

import pytest
from fastapi import HTTPException

from app.api.rate_limit import LOGIN_ATTEMPTS_PER_EMAIL, LOGIN_ATTEMPTS_PER_IP, REGISTRATIONS_PER_IP
from app.core.rate_limit import RateLimiter
from tests.conftest import TEST_PASSWORD

GOOD = {"email": "limit@example.com", "password": "correct-horse-7", "full_name": "Lim It"}


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


# ---------------------------------------------------------------- the RateLimiter class


def test_allows_up_to_the_limit_then_rejects():
    limiter = RateLimiter(limit=3, window=60)

    for _ in range(3):
        limiter.hit("a")
    with pytest.raises(HTTPException) as exc_info:
        limiter.hit("a")

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) >= 1


def test_keys_are_independent():
    limiter = RateLimiter(limit=1, window=60)

    limiter.hit("a")
    limiter.hit("b")  # different key, not affected by "a"

    with pytest.raises(HTTPException):
        limiter.hit("a")


def test_old_hits_fall_out_of_the_window():
    limiter = RateLimiter(limit=1, window=0.05)

    limiter.hit("a")
    time.sleep(0.1)
    limiter.hit("a")  # the first hit has aged out, so this is allowed


def test_reset_clears_state():
    limiter = RateLimiter(limit=1, window=60)
    limiter.hit("a")

    limiter.reset()

    limiter.hit("a")  # would raise if not reset


# ---------------------------------------------------------------------- login endpoint


def test_login_is_blocked_after_too_many_attempts_for_one_email(anon_client, make_user):
    make_user(email="target@example.com")
    for _ in range(LOGIN_ATTEMPTS_PER_EMAIL.limit):
        login(anon_client, "target@example.com", "wrong-password")

    response = login(anon_client, "target@example.com", "wrong-password")

    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Please try again later."}
    assert "Retry-After" in response.headers


def test_login_rate_limit_is_per_email_not_global(anon_client, make_user):
    make_user(email="a@example.com")
    make_user(email="b@example.com")
    for _ in range(LOGIN_ATTEMPTS_PER_EMAIL.limit):
        login(anon_client, "a@example.com", "wrong-password")
    assert login(anon_client, "a@example.com", "wrong-password").status_code == 429

    # A different email from the same client is not affected.
    assert login(anon_client, "b@example.com", "wrong-password").status_code == 401


def test_login_email_limit_is_case_insensitive(anon_client, make_user):
    make_user(email="case@example.com")
    for _ in range(LOGIN_ATTEMPTS_PER_EMAIL.limit):
        login(anon_client, "CASE@example.com", "wrong-password")

    assert login(anon_client, "Case@Example.com", "wrong-password").status_code == 429


def test_login_rate_limit_is_also_per_ip_across_emails(make_client):
    one_ip = make_client(ip="203.0.113.5")
    for i in range(LOGIN_ATTEMPTS_PER_IP.limit):
        login(one_ip, f"nobody{i}@example.com", "wrong-password")

    response = login(one_ip, "yet-another@example.com", "wrong-password")

    assert response.status_code == 429


def test_login_rate_limit_counts_successful_attempts_too(anon_client, user):
    for _ in range(LOGIN_ATTEMPTS_PER_EMAIL.limit):
        assert login(anon_client, user.email, TEST_PASSWORD).status_code == 200

    assert login(anon_client, user.email, TEST_PASSWORD).status_code == 429


def test_different_ips_have_independent_login_limits(make_client, make_user):
    make_user(email="shared@example.com")
    first = make_client(ip="198.51.100.1")
    second = make_client(ip="198.51.100.2")
    for _ in range(LOGIN_ATTEMPTS_PER_IP.limit):
        login(first, f"user-{_}@example.com", "wrong-password")
    assert login(first, "one-more@example.com", "wrong-password").status_code == 429

    # A different IP starts with a clean per-IP count (the per-email limit for this
    # fresh email is also unused).
    assert login(second, "shared@example.com", "wrong-password").status_code == 401


# ------------------------------------------------------------------- register endpoint


def test_registration_is_blocked_after_too_many_attempts_from_one_ip(make_client):
    one_ip = make_client(ip="203.0.113.9")
    for i in range(REGISTRATIONS_PER_IP.limit):
        one_ip.post("/auth/register", json={**GOOD, "email": f"user{i}@example.com"})

    response = one_ip.post("/auth/register", json={**GOOD, "email": "one-more@example.com"})

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_registration_rate_limit_is_per_ip(make_client):
    first = make_client(ip="203.0.113.10")
    second = make_client(ip="203.0.113.11")
    for i in range(REGISTRATIONS_PER_IP.limit):
        first.post("/auth/register", json={**GOOD, "email": f"ip-a-{i}@example.com"})
    assert first.post("/auth/register", json={**GOOD, "email": "blocked@example.com"}).status_code == 429

    assert second.post("/auth/register", json={**GOOD, "email": "ip-b@example.com"}).status_code == 201
