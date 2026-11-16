"""Security response headers (X-Frame-Options, nosniff, HSTS, ...)."""

from fastapi.testclient import TestClient

from app.core.security_headers import _HEADERS
from app.main import app


def test_security_headers_are_present(anon_client):
    response = anon_client.get("/health")

    for name, value in _HEADERS.items():
        assert response.headers[name] == value


def test_security_headers_apply_to_error_responses_too(anon_client):
    response = anon_client.get("/applications/999999")  # 401, no token

    for name in _HEADERS:
        assert name in response.headers


def test_hsts_is_not_sent_over_plain_http(anon_client):
    # TestClient requests are plain HTTP by default, matching local development.
    response = anon_client.get("/health")

    assert "Strict-Transport-Security" not in response.headers


def test_hsts_is_sent_once_the_request_reached_us_over_https():
    # request.url.scheme reflects X-Forwarded-Proto once uvicorn runs with
    # --proxy-headers behind Render's proxy (see scripts/start.sh); base_url here
    # stands in for that rewritten scheme.
    with TestClient(app, base_url="https://careerops-api.onrender.com") as https_client:
        response = https_client.get("/health")

    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"
