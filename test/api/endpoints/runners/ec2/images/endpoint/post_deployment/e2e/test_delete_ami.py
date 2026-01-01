"""E2E tests for the DELETE /v1/runners/ec2/images/{ami_id} endpoint."""
import requests
import pytest

from ..conftest import make_authenticated_get


@pytest.fixture(name="test_ami_id", scope="module")
def test_ami_id_fixture(amis_endpoint, api_key):
    """Get an AMI ID to use for delete tests.

    Returns the oldest deletable AMI. An AMI is deletable if it's not the
    latest stable AMI. We don't actually delete it - we just test the
    endpoint behavior with x-test-mode.
    """
    response = make_authenticated_get(amis_endpoint, api_key)
    if response.status_code != 200:
        pytest.skip("Cannot list AMIs to find test candidate")

    amis = response.json().get("amis", [])
    if not amis:
        pytest.skip("No AMIs available for delete testing")

    # Find the latest stable AMI (the one we must protect)
    stable_amis = [
        ami for ami in amis
        if ami.get("tags", {}).get("Stable") == "true"
    ]
    latest_stable_id = None
    if stable_amis:
        sorted_stable = sorted(
            stable_amis,
            key=lambda x: x.get("creation_date", ""),
            reverse=True
        )
        latest_stable_id = sorted_stable[0]["ami_id"]

    # Any AMI except the latest stable is a valid delete candidate
    deletable_amis = [
        ami for ami in amis
        if ami["ami_id"] != latest_stable_id
    ]

    if not deletable_amis:
        pytest.skip("Only one AMI exists (latest stable) - nothing safe to delete")

    # Return the oldest deletable AMI (least likely to be in use)
    sorted_amis = sorted(deletable_amis, key=lambda x: x.get("creation_date", ""))
    return sorted_amis[0]["ami_id"]


@pytest.fixture(name="delete_endpoint", scope="module")
def delete_endpoint_fixture(api_url, test_ami_id) -> str:
    """Return the endpoint URL for deleting a specific AMI."""
    return f"{api_url}/v1/runners/ec2/images/{test_ami_id}"


@pytest.fixture(name="nonexistent_delete_endpoint", scope="module")
def nonexistent_delete_endpoint_fixture(api_url) -> str:
    """Return the endpoint URL for a nonexistent AMI."""
    return f"{api_url}/v1/runners/ec2/images/ami-nonexistent12345"


class TestDeleteAmiAuthentication:
    """Test DELETE endpoint authentication requirements."""

    def test_delete_requires_auth(self, delete_endpoint):
        """Verify DELETE endpoint returns 403 without auth."""
        response = requests.delete(delete_endpoint, timeout=10)
        assert response.status_code == 403

    def test_delete_rejects_invalid_api_key(self, delete_endpoint):
        """Verify DELETE endpoint rejects invalid API key."""
        headers = {"x-api-key": "invalid-key-12345"}
        response = requests.delete(delete_endpoint, headers=headers, timeout=10)
        assert response.status_code == 403


class TestDeleteAmiEndpoint:
    """Test DELETE endpoint behavior with valid authentication.

    Note: These tests use x-test-mode to avoid actually deleting AMIs.
    """

    def test_delete_nonexistent_ami_returns_json(
        self, nonexistent_delete_endpoint, api_key
    ):
        """Verify DELETE for nonexistent AMI returns JSON response."""
        headers = {"x-api-key": api_key, "x-test-mode": "true"}
        response = requests.delete(
            nonexistent_delete_endpoint, headers=headers, timeout=10
        )
        assert response.headers.get("Content-Type") == "application/json"

    def test_delete_endpoint_returns_200_or_error(self, delete_endpoint, api_key):
        """Verify DELETE endpoint returns valid HTTP status."""
        headers = {"x-api-key": api_key, "x-test-mode": "true"}
        response = requests.delete(delete_endpoint, headers=headers, timeout=10)
        # Should return 200 (success) or 4xx (client error) - not 5xx
        assert response.status_code < 500, (
            f"DELETE endpoint returned server error: {response.status_code}"
        )

    def test_delete_response_has_json_body(self, delete_endpoint, api_key):
        """Verify DELETE response has valid JSON body."""
        headers = {"x-api-key": api_key, "x-test-mode": "true"}
        response = requests.delete(delete_endpoint, headers=headers, timeout=10)
        # Should be able to parse as JSON
        try:
            response.json()
        except ValueError:
            pytest.fail("DELETE response is not valid JSON")
