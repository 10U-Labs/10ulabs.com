"""Integration tests for the get latest AMI endpoint."""
import pytest

from ..conftest import make_authenticated_get


@pytest.fixture(name="latest_response", scope="module")
def latest_response_fixture(latest_ami_endpoint, api_key):
    """Fetch the latest AMI response for use in tests."""
    return make_authenticated_get(latest_ami_endpoint, api_key)


def test_get_latest_ami_returns_200(latest_response):
    """Test that the endpoint returns 200 status."""
    assert latest_response.status_code == 200


def test_get_latest_ami_returns_json(latest_response):
    """Test that the response has JSON content type."""
    assert latest_response.headers["Content-Type"] == "application/json"


def test_get_latest_ami_has_success_field(latest_response):
    """Test that the response contains a success field."""
    assert "success" in latest_response.json()


def test_get_latest_ami_returns_success_true(latest_response):
    """Test that the response returns success true."""
    assert latest_response.json().get("success") is True


def test_get_latest_ami_has_ami_id(latest_response):
    """Test that response contains ami_id."""
    assert "ami_id" in latest_response.json()


def test_get_latest_ami_has_name(latest_response):
    """Test that response contains name."""
    assert "name" in latest_response.json()


def test_get_latest_ami_has_state(latest_response):
    """Test that response contains state."""
    assert "state" in latest_response.json()


def test_get_latest_ami_has_creation_date(latest_response):
    """Test that response contains creation_date."""
    assert "creation_date" in latest_response.json()
