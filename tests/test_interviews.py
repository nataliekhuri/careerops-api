"""Interviews CRUD, validation, calendar filters, cascade and isolation."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

BASE = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def create_application(client, **fields):
    response = client.post("/applications", json={"company": "Acme", "position": "Dev", "location": "Remote", **fields})
    assert response.status_code == 200, response.text
    return response.json()["application"]


def create_interview(client, application_id, **fields):
    body = {"application_id": application_id, "scheduled_at": iso(BASE), **fields}
    response = client.post("/interviews", json=body)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def application(client):
    return create_application(client)


# ---------------------------------------------------------------------- CRUD


def test_create_interview_with_defaults_and_application_summary(client, application):
    interview = create_interview(client, application["id"])

    assert interview["duration_minutes"] == 60
    assert interview["interview_type"] == "video"
    assert interview["outcome"] == "pending"
    assert interview["application"] == {
        "id": application["id"],
        "company": "Acme",
        "position": "Dev",
        "status": "Applied",
    }
    assert datetime.fromisoformat(interview["scheduled_at"]) == BASE


def test_times_with_offsets_are_stored_as_the_same_instant(client, application):
    berlin = "2026-12-01T10:00:00+01:00"  # == 09:00 UTC

    interview = create_interview(client, application["id"], scheduled_at=berlin)

    assert datetime.fromisoformat(interview["scheduled_at"]) == BASE


def test_get_update_delete_interview(client, application):
    interview = create_interview(client, application["id"])

    assert client.get(f"/interviews/{interview['id']}").status_code == 200
    updated = client.patch(
        f"/interviews/{interview['id']}",
        json={"outcome": "PASSED", "scheduled_at": iso(BASE + timedelta(days=1)), "interview_type": "technical"},
    ).json()
    assert updated["outcome"] == "passed"
    assert updated["interview_type"] == "technical"
    assert datetime.fromisoformat(updated["scheduled_at"]) == BASE + timedelta(days=1)
    assert client.delete(f"/interviews/{interview['id']}").status_code == 204
    assert client.get(f"/interviews/{interview['id']}").status_code == 404


@pytest.mark.parametrize(
    "changes",
    [
        {"scheduled_at": "2026-12-01T09:00:00"},  # no time zone
        {"scheduled_at": "not a date"},
        {"duration_minutes": 0},
        {"duration_minutes": 601},
        {"interview_type": "lunch"},
        {"outcome": "maybe"},
        {"location": "x" * 501},
        {"application_id": 0},
        {"user_id": 1},
    ],
)
def test_invalid_interview_returns_422(client, application, changes):
    body = {"application_id": application["id"], "scheduled_at": iso(BASE), **changes}

    assert client.post("/interviews", json=body).status_code == 422


def test_patch_cannot_move_interview_to_another_application_or_set_nulls(client, application):
    interview = create_interview(client, application["id"])

    assert client.patch(f"/interviews/{interview['id']}", json={"application_id": 5}).status_code == 422
    assert client.patch(f"/interviews/{interview['id']}", json={"scheduled_at": None}).status_code == 422


def test_unknown_application_is_rejected(client):
    response = client.post("/interviews", json={"application_id": 999999, "scheduled_at": iso(BASE)})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Application not found"


def test_deleting_an_application_deletes_its_interviews(client, application):
    interview = create_interview(client, application["id"])

    client.delete(f"/applications/{application['id']}")

    assert client.get(f"/interviews/{interview['id']}").status_code == 404


# ----------------------------------------------------- calendar & filtering


def test_list_is_sorted_soonest_first_and_filters_by_range(client, application):
    later = create_interview(client, application["id"], scheduled_at=iso(BASE + timedelta(days=10)))
    soon = create_interview(client, application["id"], scheduled_at=iso(BASE))
    middle = create_interview(client, application["id"], scheduled_at=iso(BASE + timedelta(days=5)))

    ids = lambda r: [i["id"] for i in r.json()]  # noqa: E731
    assert ids(client.get("/interviews")) == [soon["id"], middle["id"], later["id"]]
    assert ids(client.get("/interviews", params={"descending": True})) == [later["id"], middle["id"], soon["id"]]
    december_week = client.get(
        "/interviews", params={"start": iso(BASE + timedelta(days=1)), "end": iso(BASE + timedelta(days=8))}
    )
    assert ids(december_week) == [middle["id"]]
    assert december_week.headers["X-Total-Count"] == "1"


def test_filter_by_application_outcome_and_type(client, application):
    other_app = create_application(client, company="Globex")
    a = create_interview(client, application["id"], interview_type="phone")
    b = create_interview(client, other_app["id"], outcome="failed")

    assert [i["id"] for i in client.get("/interviews", params={"application_id": other_app["id"]}).json()] == [b["id"]]
    assert [i["id"] for i in client.get("/interviews", params={"outcome": "failed"}).json()] == [b["id"]]
    assert [i["id"] for i in client.get("/interviews", params={"interview_type": "PHONE"}).json()] == [a["id"]]


@pytest.mark.parametrize(
    "params",
    [
        {"start": "2026-12-01T00:00:00"},  # no time zone
        {"start": "2026-12-05T00:00:00Z", "end": "2026-12-01T00:00:00Z"},  # start after end
        {"limit": 0},
        {"limit": 501},
        {"outcome": "maybe"},
    ],
)
def test_invalid_interview_filters_return_422(client, params):
    assert client.get("/interviews", params=params).status_code == 422


# ------------------------------------------------------------------ isolation


@pytest.fixture
def other(make_user, make_client):
    return make_client(make_user(email="other@example.com"))


def test_interviews_are_private(client, other, application):
    mine = create_interview(client, application["id"], notes="secret prep notes")

    assert other.get("/interviews").json() == []
    assert other.get("/interviews", params={"application_id": application["id"]}).json() == []
    for method, body in [("GET", None), ("PATCH", {"outcome": "failed"}), ("DELETE", None)]:
        response = other.request(method, f"/interviews/{mine['id']}", json=body)
        assert response.status_code == 404
        assert "secret" not in response.text
    assert client.get(f"/interviews/{mine['id']}").json()["outcome"] == "pending"


def test_cannot_create_interview_for_another_users_application(client, other, application):
    response = other.post("/interviews", json={"application_id": application["id"], "scheduled_at": iso(BASE)})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Application not found"  # same as missing
    assert client.get("/interviews").json() == []


def test_database_rejects_interview_whose_owner_differs_from_the_application_owner(
    client, other, application, db_session
):
    """Defence in depth: even a bug in the API could not attach an interview to someone else's application."""
    with pytest.raises(IntegrityError):
        db_session.execute(
            text("INSERT INTO interviews (user_id, application_id, scheduled_at) VALUES (:u, :a, now())"),
            {"u": other.user.id, "a": application["id"]},
        )
        db_session.flush()
    db_session.rollback()
