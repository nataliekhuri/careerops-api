"""Tests for statuses, timestamps, PATCH, filtering, sorting and pagination."""

from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]


def create(client, **fields):
    body = {"company": "Acme", "position": "Dev", "location": "Remote", **fields}
    response = client.post("/applications", json=body)
    assert response.status_code == 200, response.text
    return response.json()["application"]


def parse(ts: str) -> datetime:
    value = datetime.fromisoformat(ts)
    assert value.tzinfo is not None, "timestamps must include a timezone"
    return value


# ------------------------------------------------------------------ statuses


@pytest.mark.parametrize("status", STATUSES)
def test_each_allowed_status_is_accepted(client, status):
    assert create(client, status=status)["status"] == status


@pytest.mark.parametrize(("given", "stored"), [("interview", "Interview"), ("  OFFER ", "Offer"), ("rejected", "Rejected")])
def test_status_is_case_insensitive_and_normalised(client, given, stored):
    assert create(client, status=given)["status"] == stored


@pytest.mark.parametrize("status", ["Pending", "Hired", "Applied!", "x" * 51])
def test_unknown_status_returns_422(client, status):
    response = client.post("/applications", json={"company": "A", "position": "B", "location": "C", "status": status})

    assert response.status_code == 422


def test_database_rejects_invalid_status_even_without_the_api(db_session):
    with pytest.raises(IntegrityError):
        db_session.execute(
            text("INSERT INTO applications (company, position, location, status, notes) VALUES ('A','B','C','Bogus','')")
        )
        db_session.flush()
    db_session.rollback()


def test_database_default_status_is_applied(db_session):
    status = db_session.execute(
        text("INSERT INTO applications (company, position, location, notes) VALUES ('A','B','C','') RETURNING status")
    ).scalar_one()

    assert status == "Applied"


# ---------------------------------------------------------------- timestamps


def test_new_application_has_timestamps(client):
    application = create(client)

    created, updated = parse(application["created_at"]), parse(application["updated_at"])
    assert created == updated


def test_put_updates_updated_at_but_not_created_at(client):
    application = create(client)

    response = client.put(
        f"/applications/{application['id']}",
        json={"company": "Acme", "position": "Dev", "location": "Remote", "status": "Interview"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_at"] == application["created_at"]
    assert parse(body["updated_at"]) > parse(application["updated_at"])


def test_timestamps_cannot_be_set_by_the_client(client):
    response = client.post(
        "/applications",
        json={"company": "A", "position": "B", "location": "C", "created_at": "2000-01-01T00:00:00Z"},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------- PATCH


def test_patch_changes_only_the_given_fields(client):
    application = create(client, notes="first note")

    response = client.patch(f"/applications/{application['id']}", json={"status": "Interview"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Interview"
    for field in ("company", "position", "location", "notes", "created_at"):
        assert body[field] == application[field]
    assert parse(body["updated_at"]) > parse(application["updated_at"])


def test_patch_applies_the_same_validation(client):
    application = create(client)

    assert client.patch(f"/applications/{application['id']}", json={"company": "   "}).status_code == 422
    assert client.patch(f"/applications/{application['id']}", json={"status": "Pending"}).status_code == 422
    assert client.patch(f"/applications/{application['id']}", json={"position": "x" * 256}).status_code == 422


@pytest.mark.parametrize("field", ["company", "position", "location", "status", "notes"])
def test_patch_rejects_null_values(client, field):
    application = create(client)

    response = client.patch(f"/applications/{application['id']}", json={field: None})

    assert response.status_code == 422


def test_patch_rejects_unknown_fields(client):
    application = create(client)

    assert client.patch(f"/applications/{application['id']}", json={"salary": 1}).status_code == 422


def test_patch_with_empty_body_changes_nothing(client):
    application = create(client)

    response = client.patch(f"/applications/{application['id']}", json={})

    assert response.status_code == 200
    assert response.json() == application


def test_patch_unknown_application_returns_404(client):
    response = client.patch("/applications/999999", json={"status": "Offer"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


# ------------------------------------------------------------------ filtering


def ids(response):
    assert response.status_code == 200, response.text
    return [a["id"] for a in response.json()]


def test_filter_by_status(client):
    applied = create(client, status="Applied")
    interview = create(client, status="Interview")

    assert ids(client.get("/applications", params={"status": "Interview"})) == [interview["id"]]
    assert ids(client.get("/applications", params={"status": "applied"})) == [applied["id"]]


def test_filter_by_invalid_status_returns_422(client):
    assert client.get("/applications", params={"status": "Pending"}).status_code == 422


def test_filter_by_company_is_case_insensitive_substring(client):
    acme = create(client, company="Acme Corporation")
    create(client, company="Globex")

    assert ids(client.get("/applications", params={"company": "acme"})) == [acme["id"]]
    assert ids(client.get("/applications", params={"company": "CORP"})) == [acme["id"]]


def test_filter_by_location(client):
    berlin = create(client, location="Berlin, Germany")
    create(client, location="Remote")

    assert ids(client.get("/applications", params={"location": "berlin"})) == [berlin["id"]]


def test_filters_can_be_combined(client):
    match = create(client, company="Acme", status="Offer")
    create(client, company="Acme", status="Rejected")
    create(client, company="Globex", status="Offer")

    assert ids(client.get("/applications", params={"company": "acme", "status": "Offer"})) == [match["id"]]


def test_filter_text_wildcards_are_treated_literally(client):
    create(client, company="Acme")
    percent = create(client, company="100% Remote Ltd")

    assert ids(client.get("/applications", params={"company": "%"})) == [percent["id"]]
    assert ids(client.get("/applications", params={"company": "_"})) == []


# ------------------------------------------------------ sorting & pagination


def test_default_order_is_creation_order(client):
    created = [create(client, company=name)["id"] for name in ("C", "A", "B")]

    assert ids(client.get("/applications")) == created


def test_sort_by_company_and_descending(client):
    c, a, b = (create(client, company=name)["id"] for name in ("C", "A", "B"))

    assert ids(client.get("/applications", params={"sort": "company"})) == [a, b, c]
    assert ids(client.get("/applications", params={"sort": "-company"})) == [c, b, a]
    assert ids(client.get("/applications", params={"sort": "-created_at"})) == [b, a, c]


def test_invalid_sort_returns_422(client):
    assert client.get("/applications", params={"sort": "salary"}).status_code == 422


def test_limit_and_offset(client):
    created = [create(client, company=f"Company {i}")["id"] for i in range(5)]

    assert ids(client.get("/applications", params={"limit": 2})) == created[:2]
    assert ids(client.get("/applications", params={"limit": 2, "offset": 2})) == created[2:4]
    assert ids(client.get("/applications", params={"offset": 4})) == created[4:]


def test_total_count_header_reflects_filters_not_page(client):
    for i in range(3):
        create(client, status="Interview", company=f"I{i}")
    create(client, status="Offer")

    response = client.get("/applications", params={"status": "Interview", "limit": 1})

    assert len(response.json()) == 1
    assert response.headers["X-Total-Count"] == "3"


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "abc"}])
def test_invalid_pagination_returns_422(client, params):
    assert client.get("/applications", params=params).status_code == 422


def test_default_page_size_is_50(client, db_session):
    db_session.execute(
        text(
            "INSERT INTO applications (company, position, location, notes) "
            "SELECT 'C' || g, 'Dev', 'Remote', '' FROM generate_series(1, 55) g"
        )
    )

    response = client.get("/applications")

    assert len(response.json()) == 50
    assert response.headers["X-Total-Count"] == "55"
