"""Dashboard statistics: exact numbers, empty state, weekly buckets and isolation."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.crud.dashboard import get_stats

STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]


def create_application(client, **fields):
    response = client.post("/applications", json={"company": "Acme", "position": "Dev", "location": "Remote", **fields})
    assert response.status_code == 200, response.text
    return response.json()["application"]


def test_empty_dashboard(client):
    stats = client.get("/dashboard/stats")

    assert stats.status_code == 200
    body = stats.json()
    assert body["total_applications"] == 0
    assert body["by_status"] == dict.fromkeys(STATUSES, 0)
    assert body["rates"] == {"response_rate": 0.0, "interview_rate": 0.0, "offer_rate": 0.0}
    assert len(body["applications_per_week"]) == 12
    assert all(week["count"] == 0 for week in body["applications_per_week"])
    assert body["top_companies"] == []
    assert body["upcoming_interviews"] == []


def test_counts_and_rates(client):
    # 10 applications: 4 Applied, 1 Screening, 2 Interview, 1 Offer, 1 Rejected, 1 Withdrawn
    for status, n in [
        ("Applied", 4),
        ("Screening", 1),
        ("Interview", 2),
        ("Offer", 1),
        ("Rejected", 1),
        ("Withdrawn", 1),
    ]:
        for _ in range(n):
            create_application(client, status=status)

    body = client.get("/dashboard/stats").json()

    assert body["total_applications"] == 10
    assert body["active_applications"] == 8  # Applied + Screening + Interview + Offer
    assert body["by_status"] == {
        "Applied": 4,
        "Screening": 1,
        "Interview": 2,
        "Offer": 1,
        "Rejected": 1,
        "Withdrawn": 1,
    }
    # Rates exclude Withdrawn: 9 considered.
    assert body["rates"] == {"response_rate": 55.6, "interview_rate": 33.3, "offer_rate": 11.1}


def test_top_companies(client):
    for company, n in [("Acme", 3), ("Globex", 2), ("Initech", 1)]:
        for _ in range(n):
            create_application(client, company=company)

    assert client.get("/dashboard/stats").json()["top_companies"] == [
        {"company": "Acme", "count": 3},
        {"company": "Globex", "count": 2},
        {"company": "Initech", "count": 1},
    ]


def test_weekly_counts_are_bucketed_by_monday_and_zero_filled(db_session, user):
    now = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)  # a Thursday
    for created in [
        datetime(2026, 11, 9, 8, 0, tzinfo=UTC),  # Monday this week
        datetime(2026, 11, 12, 9, 0, tzinfo=UTC),  # Thursday this week
        datetime(2026, 11, 8, 23, 59, tzinfo=UTC),  # last minute of Sunday in the previous week
        datetime(2026, 8, 1, 12, 0, tzinfo=UTC),  # older than 12 weeks: not counted
    ]:
        db_session.execute(
            text(
                "INSERT INTO applications (user_id, company, position, location, notes, created_at) "
                "VALUES (:u, 'A', 'B', 'C', '', :c)"
            ),
            {"u": user.id, "c": created},
        )

    weeks = get_stats(db_session, user.id, now=now)["applications_per_week"]

    assert len(weeks) == 12
    assert weeks[-1]["week_start"].isoformat() == "2026-11-09"
    assert weeks[0]["week_start"].isoformat() == "2026-08-24"
    assert weeks[-1]["count"] == 2
    assert weeks[-2]["week_start"].isoformat() == "2026-11-02"
    assert weeks[-2]["count"] == 1
    assert sum(w["count"] for w in weeks) == 3


def test_upcoming_interviews(client):
    application = create_application(client, company="Acme")
    now = datetime.now(UTC)
    create_interview = lambda when, **f: client.post(  # noqa: E731
        "/interviews", json={"application_id": application["id"], "scheduled_at": when.isoformat(), **f}
    ).json()
    create_interview(now - timedelta(days=1))  # past
    create_interview(now + timedelta(days=2), outcome="cancelled")  # not pending
    soon = create_interview(now + timedelta(days=1))
    later = create_interview(now + timedelta(days=3))

    body = client.get("/dashboard/stats").json()

    assert body["total_interviews"] == 4
    assert body["upcoming_interviews_count"] == 2
    assert [i["id"] for i in body["upcoming_interviews"]] == [soon["id"], later["id"]]
    assert body["upcoming_interviews"][0]["application"]["company"] == "Acme"


def test_company_total(client):
    client.post("/companies", json={"name": "A"})
    client.post("/companies", json={"name": "B"})

    assert client.get("/dashboard/stats").json()["total_companies"] == 2


@pytest.fixture
def other(make_user, make_client):
    return make_client(make_user(email="other@example.com"))


def test_dashboard_only_counts_the_current_users_data(client, other):
    application = create_application(client, company="Mine", status="Offer")
    client.post("/companies", json={"name": "Mine"})
    client.post(
        "/interviews",
        json={"application_id": application["id"], "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
    )

    theirs = other.get("/dashboard/stats").json()

    assert theirs["total_applications"] == 0
    assert theirs["total_companies"] == 0
    assert theirs["total_interviews"] == 0
    assert theirs["top_companies"] == []
    assert theirs["upcoming_interviews"] == []
    assert client.get("/dashboard/stats").json()["total_applications"] == 1


def test_dashboard_requires_login(anon_client):
    assert anon_client.get("/dashboard/stats").status_code == 401
