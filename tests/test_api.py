from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.history[0].status_code == 307
    assert response.history[0].headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Soccer Club" in activities
    assert activities["Soccer Club"]["participants"] == []
    assert activities["Soccer Club"]["max_participants"] == 24


def test_signup_adds_participant(client):
    email = "student@example.com"
    response = client.post("/activities/Soccer Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Club"}
    assert email in client.get("/activities").json()["Soccer Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "student@example.com"
    url = "/activities/Soccer Club/signup"
    client.post(url, params={"email": email})

    response = client.post(url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Soccer Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown Club/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_without_changing_other_activities(client):
    email = "michael@mergington.edu"
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}

    activities = client.get("/activities").json()
    assert email not in activities["Chess Club"]["participants"]
    assert activities["Chess Club"]["participants"] == ["daniel@mergington.edu"]
    assert activities["Soccer Club"]["participants"] == []


def test_unregister_rejects_participant_who_is_not_signed_up(client):
    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"