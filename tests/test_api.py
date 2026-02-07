"""
Tests for the Mergington High School API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_participants = {
        activity: details["participants"].copy()
        for activity, details in activities.items()
    }
    
    yield
    
    # Restore original state after each test
    for activity, details in activities.items():
        details["participants"] = original_participants[activity].copy()


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    
    # Verify structure of an activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was added
    assert email in activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    activity_name = "Chess Club"
    # This email is already in the Chess Club
    email = "michael@mergington.edu"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    activity_name = "Chess Club"
    # This email is already in the Chess Club
    email = "michael@mergington.edu"
    
    # Verify participant is initially in the activity
    assert email in activities[activity_name]["participants"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify participant was removed
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistration from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_unregister_participant_not_signed_up(client):
    """Test unregistering a participant who is not signed up"""
    activity_name = "Chess Club"
    email = "notsignedup@mergington.edu"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"].lower()


def test_full_signup_and_unregister_workflow(client):
    """Test the complete workflow of signing up and then unregistering"""
    activity_name = "Programming Class"
    email = "workflow@mergington.edu"
    
    # Initial state - student not in activity
    initial_participants = activities[activity_name]["participants"].copy()
    assert email not in initial_participants
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    
    # Verify we're back to initial state
    assert activities[activity_name]["participants"] == initial_participants


def test_multiple_signups_different_activities(client):
    """Test that a student can sign up for multiple different activities"""
    email = "multitasker@mergington.edu"
    activities_to_join = ["Chess Club", "Programming Class", "Drama Club"]
    
    for activity_name in activities_to_join:
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
