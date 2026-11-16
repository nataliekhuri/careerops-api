"""Companies CRUD, validation, application links and isolation."""

import pytest

ACME = {"name": "Acme Corp", "website": "https://acme.example", "industry": "Software", "location": "Berlin"}


def create_company(client, **fields):
    response = client.post("/companies", json={**ACME, **fields})
    assert response.status_code == 201, response.text
    return response.json()


def create_application(client, **fields):
    response = client.post("/applications", json={"company": "Acme", "position": "Dev", "location": "Remote", **fields})
    assert response.status_code == 200, response.text
    return response.json()["application"]


# ---------------------------------------------------------------------- CRUD


def test_create_company_returns_it_with_defaults(client):
    company = create_company(client, name="  Globex  ", website="", industry="", location="")

    assert company["name"] == "Globex"
    assert company["notes"] == ""
    assert company["application_count"] == 0
    assert {"id", "created_at", "updated_at"} <= set(company)


def test_get_list_update_delete_company(client):
    company = create_company(client)

    assert client.get(f"/companies/{company['id']}").json()["name"] == "Acme Corp"
    assert [c["id"] for c in client.get("/companies").json()] == [company["id"]]

    updated = client.patch(f"/companies/{company['id']}", json={"industry": "Fintech"}).json()
    assert updated["industry"] == "Fintech"
    assert updated["name"] == "Acme Corp"

    assert client.delete(f"/companies/{company['id']}").status_code == 204
    assert client.get(f"/companies/{company['id']}").status_code == 404


def test_duplicate_names_are_rejected_case_insensitively(client):
    create_company(client, name="Acme")
    other = create_company(client, name="Globex")

    assert client.post("/companies", json={"name": "ACME"}).status_code == 409
    assert client.patch(f"/companies/{other['id']}", json={"name": "acme"}).status_code == 409
    assert client.patch(f"/companies/{other['id']}", json={"name": "Globex"}).status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "A", "website": "acme.example"},
        {"name": "A", "website": "javascript:alert(1)"},
        {"name": "A", "industry": "x" * 101},
        {"name": "A", "notes": "x" * 5001},
        {"name": "A", "user_id": 1},
    ],
)
def test_invalid_company_returns_422(client, body):
    assert client.post("/companies", json=body).status_code == 422


def test_patch_rejects_null_name(client):
    company = create_company(client)

    assert client.patch(f"/companies/{company['id']}", json={"name": None}).status_code == 422


def test_search_sort_and_pagination(client):
    for name, industry, location in [
        ("Beta", "Retail", "Paris"),
        ("alpha", "Software", "Berlin"),
        ("Gamma", "AI", "Remote"),
    ]:
        create_company(client, name=name, industry=industry, location=location)

    names = lambda r: [c["name"] for c in r.json()]  # noqa: E731
    assert names(client.get("/companies")) == ["alpha", "Beta", "Gamma"]  # case-insensitive A-Z
    assert names(client.get("/companies", params={"sort": "-name"})) == ["Gamma", "Beta", "alpha"]
    assert names(client.get("/companies", params={"q": "soft"})) == ["alpha"]
    assert names(client.get("/companies", params={"q": "paris"})) == ["Beta"]
    page = client.get("/companies", params={"limit": 1, "offset": 1})
    assert names(page) == ["Beta"]
    assert page.headers["X-Total-Count"] == "3"


# ------------------------------------------------------- links to applications


def test_application_can_link_to_a_company_and_count_is_shown(client):
    company = create_company(client)

    application = create_application(client, company_id=company["id"])

    assert application["company_id"] == company["id"]
    assert client.get(f"/companies/{company['id']}").json()["application_count"] == 1
    linked = client.get("/applications", params={"company_id": company["id"]}).json()
    assert [a["id"] for a in linked] == [application["id"]]


def test_application_company_link_can_be_changed_and_removed(client):
    first, second = create_company(client, name="First"), create_company(client, name="Second")
    application = create_application(client, company_id=first["id"])

    assert (
        client.patch(f"/applications/{application['id']}", json={"company_id": second["id"]}).json()["company_id"]
        == second["id"]
    )
    assert client.patch(f"/applications/{application['id']}", json={"company_id": None}).json()["company_id"] is None


def test_unknown_company_id_is_rejected(client):
    response = client.post(
        "/applications", json={"company": "A", "position": "B", "location": "C", "company_id": 999999}
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Company not found"


def test_deleting_a_company_keeps_its_applications(client):
    company = create_company(client)
    application = create_application(client, company_id=company["id"])

    client.delete(f"/companies/{company['id']}")

    kept = client.get(f"/applications/{application['id']}")
    assert kept.status_code == 200
    assert kept.json()["company_id"] is None
    assert kept.json()["company"] == "Acme"


def test_applications_without_company_id_still_work(client):
    """Backward compatibility: clients that never send company_id are unaffected."""
    application = create_application(client)

    assert application["company_id"] is None
    assert (
        client.put(
            f"/applications/{application['id']}", json={"company": "X", "position": "Y", "location": "Z"}
        ).status_code
        == 200
    )


# ------------------------------------------------------------------ isolation


@pytest.fixture
def other(make_user, make_client):
    return make_client(make_user(email="other@example.com"))


def test_companies_are_private(client, other):
    mine = create_company(client, name="Mine", notes="secret")

    assert other.get("/companies").json() == []
    assert other.get("/companies", params={"q": "mine"}).headers["X-Total-Count"] == "0"
    for method, body in [("GET", None), ("PATCH", {"name": "Hacked"}), ("DELETE", None)]:
        response = other.request(method, f"/companies/{mine['id']}", json=body)
        assert response.status_code == 404
        assert "secret" not in response.text
    assert client.get(f"/companies/{mine['id']}").json()["name"] == "Mine"


def test_same_company_name_is_allowed_for_different_users(client, other):
    create_company(client, name="Acme")

    assert other.post("/companies", json={"name": "Acme"}).status_code == 201


def test_cannot_link_an_application_to_another_users_company(client, other):
    theirs = create_company(other, name="Theirs")
    mine = create_application(client)

    created = client.post(
        "/applications", json={"company": "A", "position": "B", "location": "C", "company_id": theirs["id"]}
    )
    patched = client.patch(f"/applications/{mine['id']}", json={"company_id": theirs["id"]})
    replaced = client.put(
        f"/applications/{mine['id']}",
        json={"company": "A", "position": "B", "location": "C", "company_id": theirs["id"]},
    )

    for response in (created, patched, replaced):
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Company not found"  # same as a missing id
    assert client.get(f"/applications/{mine['id']}").json()["company_id"] is None


def test_application_count_only_counts_the_owners_applications(client, other):
    company = create_company(client)
    create_application(client, company_id=company["id"])

    assert client.get(f"/companies/{company['id']}").json()["application_count"] == 1
