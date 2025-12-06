"""Integration tests for AMI workflow trigger endpoint."""
from ..conftest import make_authenticated_post


def test_trigger_workflow_with_test_mode_returns_200(amis_endpoint, api_key):
    """Test that trigger workflow returns 200 in test mode."""
    response = make_authenticated_post(amis_endpoint, api_key)
    assert response.status_code == 200


def test_trigger_workflow_with_test_mode_returns_json(amis_endpoint, api_key):
    """Test that trigger workflow returns JSON content type."""
    response = make_authenticated_post(amis_endpoint, api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_trigger_workflow_with_test_mode_has_success_field(amis_endpoint, api_key):
    """Test that trigger workflow response has success field."""
    response = make_authenticated_post(amis_endpoint, api_key)
    assert "success" in response.json()


def test_trigger_workflow_with_test_mode_returns_success_true(amis_endpoint, api_key):
    """Test that trigger workflow returns success true in test mode."""
    response = make_authenticated_post(amis_endpoint, api_key)
    assert response.json()["success"] is True


def test_trigger_workflow_with_test_mode_has_test_mode_field(amis_endpoint, api_key):
    """Test that trigger workflow response includes test_mode flag."""
    response = make_authenticated_post(amis_endpoint, api_key)
    assert response.json().get("test_mode") is True
