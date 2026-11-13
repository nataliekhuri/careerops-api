import pytest
from sqlalchemy import select

from app.models.application import Application


def create(client, **fields):
    response = client.post("/applications", json=fields)
    assert response.status_code == 200, response.text
    return response.json()["application"]


def without_timestamps(application: dict) -> dict:
    return {k: v for k, v in application.items() if k not in ("created_at", "updated_at")}


# ----------------------------------------------------------------- create


def test_create_returns_message_and_application(client, payload):
    response = client.post("/applications", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Application created successfully"
    assert isinstance(body["application"]["id"], int)
    assert without_timestamps(body["application"]) == {
        "id": body["application"]["id"],
        "company_id": None,
        "job_description": "",
        **payload,
    }


def test_create_applies_defaults(client):
    application = create(client, company="Acme", position="Dev", location="Remote")

    assert application["status"] == "Applied"
    assert application["notes"] == ""


def test_create_persists_to_database(client, db_session, payload):
    application = create(client, **payload)

    stored = db_session.scalars(select(Application).where(Application.id == application["id"])).one()
    assert stored.company == payload["company"]
    assert stored.position == payload["position"]


# ------------------------------------------------------------------- read


def test_list_is_empty_initially(client):
    response = client.get("/applications")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_applications_in_creation_order(client, payload):
    first = create(client, **payload)
    second = create(client, **{**payload, "company": "Globex"})

    response = client.get("/applications")

    assert response.status_code == 200
    assert [a["id"] for a in response.json()] == [first["id"], second["id"]]


def test_get_one_application(client, payload):
    application = create(client, **payload)

    response = client.get(f"/applications/{application['id']}")

    assert response.status_code == 200
    assert response.json() == application


def test_get_unknown_application_returns_404(client):
    response = client.get("/applications/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


def test_get_with_non_integer_id_returns_422(client):
    assert client.get("/applications/abc").status_code == 422


# ----------------------------------------------------------------- update


def test_update_replaces_all_fields(client, payload):
    application = create(client, **payload)
    changes = {**payload, "status": "Interview", "notes": "Phone screen booked"}

    response = client.put(f"/applications/{application['id']}", json=changes)

    assert response.status_code == 200
    assert without_timestamps(response.json()) == {
        "id": application["id"],
        "company_id": None,
        "job_description": "",
        **changes,
    }
    assert client.get(f"/applications/{application['id']}").json()["status"] == "Interview"


def test_update_unknown_application_returns_404(client, payload):
    response = client.put("/applications/999999", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


def test_update_with_invalid_body_returns_422(client, payload):
    application = create(client, **payload)

    response = client.put(f"/applications/{application['id']}", json={"company": "Only company"})

    assert response.status_code == 422


# ----------------------------------------------------------------- delete


def test_delete_returns_deleted_application(client, payload):
    application = create(client, **payload)

    response = client.delete(f"/applications/{application['id']}")

    assert response.status_code == 200
    assert response.json() == {"message": "Application deleted successfully", "application": application}
    assert client.get(f"/applications/{application['id']}").status_code == 404


def test_delete_unknown_application_returns_404(client):
    response = client.delete("/applications/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


# ------------------------------------------------------------- validation


@pytest.mark.parametrize("missing", ["company", "position", "location"])
def test_missing_required_field_returns_422(client, payload, missing):
    body = {k: v for k, v in payload.items() if k != missing}

    response = client.post("/applications", json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("field", ["company", "position", "location", "status"])
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_text_fields_are_rejected(client, payload, field, value):
    response = client.post("/applications", json={**payload, field: value})

    assert response.status_code == 422


@pytest.mark.parametrize(("field", "limit"), [("company", 255), ("position", 255), ("location", 255), ("status", 50)])
def test_text_longer_than_column_limit_returns_422_not_500(client, payload, field, limit):
    response = client.post("/applications", json={**payload, field: "x" * (limit + 1)})

    assert response.status_code == 422


# status is limited to a fixed set of values (see test_application_workflow.py), not just a length.
@pytest.mark.parametrize(("field", "limit"), [("company", 255), ("position", 255), ("location", 255)])
def test_text_at_column_limit_is_accepted(client, payload, field, limit):
    application = create(client, **{**payload, field: "x" * limit})

    assert application[field] == "x" * limit


def test_notes_longer_than_limit_returns_422(client, payload):
    response = client.post("/applications", json={**payload, "notes": "x" * 5001})

    assert response.status_code == 422


def test_surrounding_whitespace_is_trimmed(client, payload):
    application = create(client, **{**payload, "company": "  Acme Corp  ", "location": " Remote "})

    assert application["company"] == "Acme Corp"
    assert application["location"] == "Remote"


def test_unknown_fields_are_rejected(client, payload):
    response = client.post("/applications", json={**payload, "salary": 100000})

    assert response.status_code == 422
