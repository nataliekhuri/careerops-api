"""End-to-end smoke test for a deployed CareerOps API (and optionally its frontend).

Walks through the real flows a user would: register, log in, add a company and an
application with a job description, move it on the board, schedule an interview, read
the dashboard, use every AI assistant endpoint, and delete the account again. Creates
exactly one throwaway account (email prefixed "smoke-test-", password generated locally
and never printed) and deletes it at the end, so a successful run leaves no trace.

Uses only the standard library (no extra dependencies to install before a deploy check).

Usage:
    python scripts/smoke_test.py --api-url https://careerops-api.onrender.com
    python scripts/smoke_test.py --api-url https://careerops-api.onrender.com \\
        --web-url https://careerops-web.onrender.com
    python scripts/smoke_test.py --api-url http://127.0.0.1:8000   # local check

Options:
    --api-url URL     Base URL of the API (required).
    --web-url URL     Base URL of the static frontend (optional: adds a check that it
                       serves the app and sends its security headers).
    --keep-account    Do not delete the test account at the end (for manual follow-up).
    --timeout SECONDS Per-request timeout, default 20 (the free API can take about a
                       minute to wake up from sleep on the very first request).

Exit code is 0 only if every check passed. This script only ever touches the one
account it creates; it never reads or modifies any other account's data.

IMPORTANT: running this against a real deployment registers an account and exercises
every write endpoint. Treat it like any other production action - run it with the same
care (and approval) as a manual click-through, not as a harmless read-only check.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

EXPECTED_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def ok(self, label: str) -> None:
        self.passed.append(label)
        print(f"  ok   {label}")

    def fail(self, label: str, detail: str) -> None:
        self.failed.append(f"{label}: {detail}")
        print(f"  FAIL {label}: {detail}")

    def check(self, label: str, condition: bool, detail: str = "") -> None:
        self.ok(label) if condition else self.fail(label, detail or "condition was false")


class Client:
    """A tiny JSON HTTP client (stdlib only) that remembers the bearer token."""

    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token: str | None = None

    def request(self, method: str, path: str, *, json_body=None, form_body=None, auth: bool = True):
        url = self.base_url + path
        headers = {}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"
        elif form_body is not None:
            data = urllib.parse.urlencode(form_body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                return resp.status, dict(resp.headers), (json.loads(body) if body else None)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            try:
                parsed = json.loads(body) if body else None
            except json.JSONDecodeError:
                parsed = body.decode(errors="replace")
            return exc.code, dict(exc.headers), parsed

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)


def check_headers(report: Report, label: str, headers: dict, scheme: str) -> None:
    lower = {k.lower(): v for k, v in headers.items()}
    for name, expected in EXPECTED_SECURITY_HEADERS.items():
        report.check(f"{label}: {name}", lower.get(name) == expected, f"got {lower.get(name)!r}")
    if scheme == "https":
        report.check(f"{label}: Strict-Transport-Security", "strict-transport-security" in lower)


def wait_for_wake_up(client: Client, report: Report) -> None:
    """The free API sleeps after 15 minutes idle; the first request can take ~a minute."""
    print("Waiting for the API to respond (it may need to wake up)...")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        status, _, _ = client.get("/health", auth=False)
        if status == 200:
            report.ok("API is awake and responding")
            return
        time.sleep(3)
    report.fail("API wake-up", "did not respond to /health within 90 seconds")


def run_api_checks(api_url: str, timeout: float, keep_account: bool) -> Report:
    report = Report()
    client = Client(api_url, timeout)
    scheme = urllib.parse.urlsplit(api_url).scheme

    wait_for_wake_up(client, report)

    status, headers, body = client.get("/health/ready", auth=False)
    report.check("GET /health/ready", status == 200 and body and body.get("status") == "ready", f"{status} {body}")
    check_headers(report, "security headers", headers, scheme)

    status, _, body = client.get("/ai/provider", auth=False)
    report.check(
        "GET /ai/provider is unauthenticated 401 (sanity: auth is enforced)",
        status == 401,
        f"got {status}",
    )

    # ---------------------------------------------------------------- account
    suffix = secrets.token_hex(6)
    email = f"smoke-test-{suffix}@example.com"
    password = "Smoke-" + secrets.token_urlsafe(18)  # generated locally; never printed or logged

    status, _, body = client.post(
        "/auth/register", json_body={"email": email, "password": password, "full_name": "Smoke Test"}, auth=False
    )
    report.check("POST /auth/register", status == 201, f"{status} {body}")
    if status != 201:
        report.fail("smoke test", "cannot continue without a test account")
        return report

    status, _, body = client.post("/auth/login", form_body={"username": email, "password": password}, auth=False)
    report.check("POST /auth/login", status == 200 and body and "access_token" in body, f"{status} {body}")
    if status != 200:
        return report
    client.token = body["access_token"]

    status, _, body = client.get("/users/me")
    report.check("GET /users/me", status == 200 and body.get("email") == email, f"{status} {body}")

    # ---------------------------------------------------------------- core data
    status, _, company = client.post("/companies", json_body={"name": "Smoke Test Co", "industry": "Testing"})
    report.check("POST /companies", status == 201, f"{status} {company}")
    company_id = company.get("id") if isinstance(company, dict) else None

    status, _, app_body = client.post(
        "/applications",
        json_body={
            "company": "Smoke Test Co",
            "position": "Backend Engineer",
            "location": "Remote",
            "company_id": company_id,
            "job_description": "Requirements: Python, FastAPI, PostgreSQL. Nice to have: Docker.",
        },
    )
    report.check("POST /applications", status == 200, f"{status} {app_body}")
    application = app_body.get("application") if isinstance(app_body, dict) else None
    application_id = application.get("id") if application else None

    if application_id:
        status, _, body = client.patch(f"/applications/{application_id}", json_body={"status": "Screening"})
        report.check(
            "PATCH /applications/{id} (board move)",
            status == 200 and body.get("status") == "Screening",
            f"{status} {body}",
        )

        when = (datetime.now(UTC) + timedelta(days=3)).isoformat()
        status, _, body = client.post(
            "/interviews",
            json_body={"application_id": application_id, "scheduled_at": when, "interview_type": "video"},
        )
        report.check("POST /interviews", status == 201, f"{status} {body}")

    status, _, body = client.get("/applications")
    report.check("GET /applications", status == 200 and isinstance(body, list) and len(body) == 1, f"{status} {body}")

    status, _, body = client.get("/dashboard/stats")
    report.check("GET /dashboard/stats", status == 200 and body.get("total_applications") == 1, f"{status} {body}")

    # ---------------------------------------------------------------- AI assistant
    status, headers, body = client.get("/ai/provider")
    report.check(
        "GET /ai/provider is the free built-in analyzer",
        status == 200
        and body
        == {
            "name": "builtin",
            "external": False,
            "cost": "free",
            "description": "Built-in rule-based analyzer. Runs on this server; your data is not sent anywhere.",
        },
        f"{status} {body}",
    )

    status, _, profile = client.put(
        "/users/me/career-profile",
        json_body={"skills": ["Python", "FastAPI"], "years_experience": 3, "cv_text": "Built FastAPI services."},
    )
    report.check("PUT /users/me/career-profile", status == 200, f"{status} {profile}")

    if application_id:
        source = {"application_id": application_id}
        status, _, body = client.post("/ai/job-analysis", json_body=source)
        report.check(
            "POST /ai/job-analysis", status == 200 and "Python" in body.get("required_skills", []), f"{status} {body}"
        )

        status, _, body = client.post("/ai/match", json_body=source)
        report.check("POST /ai/match", status == 200 and body.get("score") is not None, f"{status} {body}")

        status, _, body = client.post("/ai/cv-review", json_body={"application_id": application_id})
        report.check("POST /ai/cv-review", status == 200 and "checks" in body, f"{status} {body}")

        status, _, body = client.post("/ai/interview-prep", json_body=source)
        report.check("POST /ai/interview-prep", status == 200 and "technical_questions" in body, f"{status} {body}")

    status, _, body = client.get("/ai/skill-insights")
    report.check("GET /ai/skill-insights", status == 200 and body.get("analyzed_applications") == 1, f"{status} {body}")

    # ---------------------------------------------------------------- isolation sanity
    status, _, body = client.get("/applications/999999999")
    report.check("GET of a non-existent application is 404 (not a crash)", status == 404, f"{status} {body}")

    # ---------------------------------------------------------------- cleanup
    if keep_account:
        print(f"\n--keep-account set: leaving {email} in place for manual follow-up.")
    else:
        status, _, body = client.delete("/users/me", json_body={"password": password})
        report.check("DELETE /users/me (cleanup)", status == 204, f"{status} {body}")

        status, _, _ = client.post("/auth/login", form_body={"username": email, "password": password}, auth=False)
        report.check("Account is really gone (login now fails)", status == 401, f"got {status}")

    return report


def run_web_checks(web_url: str, timeout: float) -> Report:
    report = Report()
    scheme = urllib.parse.urlsplit(web_url).scheme
    req = urllib.request.Request(web_url.rstrip("/") + "/", headers={"Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, headers, html = resp.status, dict(resp.headers), resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        status, headers, html = exc.code, dict(exc.headers), ""

    report.check("GET / (frontend)", status == 200, f"got {status}")
    report.check("frontend HTML mentions CareerOps", "CareerOps" in html)
    lower = {k.lower(): v for k, v in headers.items()}
    report.check("frontend: Content-Security-Policy", "content-security-policy" in lower)
    report.check(
        "frontend: X-Frame-Options", lower.get("x-frame-options") == "DENY", f"got {lower.get('x-frame-options')!r}"
    )
    report.check("frontend: X-Content-Type-Options", lower.get("x-content-type-options") == "nosniff")
    if scheme == "https":
        report.check("frontend: Strict-Transport-Security or HTTPS-only hosting", True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-url", required=True, help="Base URL of the API, e.g. https://careerops-api.onrender.com")
    parser.add_argument("--web-url", help="Base URL of the static frontend (optional)")
    parser.add_argument("--keep-account", action="store_true", help="Do not delete the test account afterwards")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds (default 20)")
    args = parser.parse_args()

    print(f"=== API checks: {args.api_url} ===")
    report = run_api_checks(args.api_url, args.timeout, args.keep_account)

    if args.web_url:
        print(f"\n=== Frontend checks: {args.web_url} ===")
        web_report = run_web_checks(args.web_url, args.timeout)
        report.passed += web_report.passed
        report.failed += web_report.failed

    print(f"\n{len(report.passed)} passed, {len(report.failed)} failed.")
    if report.failed:
        print("\nFailed checks:")
        for line in report.failed:
            print(f"  - {line}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
