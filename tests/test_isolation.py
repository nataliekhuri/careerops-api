"""Users must never see or change each other's applications."""

import pytest


@pytest.fixture
def alice(make_user, make_client):
    return make_client(make_user(email="alice@example.com"))


@pytest.fixture
def bob(make_user, make_client):
    return make_client(make_user(email="bob@example.com"))


def create(client, **fields):
    body = {"company": "Acme", "position": "Dev", "location": "Remote", **fields}
    response = client.post("/applications", json=body)
    assert response.status_code == 200, response.text
    return response.json()["application"]


def test_each_user_lists_only_their_own_applications(alice, bob):
    a1 = create(alice, company="Alice Co")
    a2 = create(alice, company="Alice Two")
    b1 = create(bob, company="Bob Co")

    alice_list = alice.get("/applications")
    bob_list = bob.get("/applications")

    assert [a["id"] for a in alice_list.json()] == [a1["id"], a2["id"]]
    assert alice_list.headers["X-Total-Count"] == "2"
    assert [a["id"] for a in bob_list.json()] == [b1["id"]]
    assert bob_list.headers["X-Total-Count"] == "1"


def test_filters_never_leak_other_users_applications(alice, bob):
    create(alice, company="Shared Name", status="Offer")

    response = bob.get("/applications", params={"company": "shared", "status": "Offer"})

    assert response.json() == []
    assert response.headers["X-Total-Count"] == "0"


@pytest.mark.parametrize(
    ("method", "body"),
    [
        ("GET", None),
        ("PUT", {"company": "Hacked", "position": "X", "location": "Y"}),
        ("PATCH", {"status": "Rejected"}),
        ("DELETE", None),
    ],
)
def test_other_users_application_looks_not_found(alice, bob, method, body):
    target = create(alice, company="Private", notes="secret note")

    response = bob.request(method, f"/applications/{target['id']}", json=body)

    # 404 (not 403), with the same message as a missing id: existence is not revealed.
    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}
    assert "secret note" not in response.text


def test_failed_cross_user_writes_change_nothing(alice, bob):
    target = create(alice, company="Private", status="Interview")

    bob.put(f"/applications/{target['id']}", json={"company": "Hacked", "position": "X", "location": "Y"})
    bob.patch(f"/applications/{target['id']}", json={"status": "Rejected"})
    bob.delete(f"/applications/{target['id']}")

    assert alice.get(f"/applications/{target['id']}").json() == target


def test_applications_are_owned_by_whoever_creates_them(alice, bob, db_session):
    from app.models.application import Application

    created = create(bob)

    owner_id = db_session.get(Application, created["id"]).user_id
    assert owner_id == bob.user.id != alice.user.id


def test_owner_cannot_be_set_through_the_api(alice, bob):
    response = alice.post(
        "/applications", json={"company": "A", "position": "B", "location": "C", "user_id": bob.user.id}
    )

    assert response.status_code == 422
    assert "user_id" not in alice.get("/applications").text


def test_deleting_one_account_keeps_other_users_data(alice, bob):
    create(alice)
    kept = create(bob)

    alice.request("DELETE", "/users/me", json={"password": "test-password-123"})

    assert [a["id"] for a in bob.get("/applications").json()] == [kept["id"]]
