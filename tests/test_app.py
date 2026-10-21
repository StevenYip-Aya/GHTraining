from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    expected_activity = {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }

    response = client.get("/activities")

    assert response.status_code == 200
    assert len(response.json()) == 9
    assert response.json()["Chess Club"] == expected_activity


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant(client):
    email = "student@example.com"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "michael@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/activities/Chess Club/signup"),
        ("delete", "/activities/Chess Club/participants"),
    ],
)
def test_mutation_routes_require_email(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "email"


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess Club/participants", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unregistered_participant(client):
    email = "student@example.com"

    response = client.delete("/activities/Chess Club/participants", params={"email": email})

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}