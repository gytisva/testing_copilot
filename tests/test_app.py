import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Programming%20Class/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Programming Class"
    }
    assert email in client.get("/activities").json()["Programming Class"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email():
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant():
    email = "temporary.student@mergington.edu"
    client.post("/activities/Tennis%20Club/signup", params={"email": email})

    response = client.delete("/activities/Tennis%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Tennis Club"
    }
    assert email not in client.get("/activities").json()["Tennis Club"]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_nonparticipant():
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_requires_email():
    response = client.delete("/activities/Chess%20Club/signup")

    assert response.status_code == 422
