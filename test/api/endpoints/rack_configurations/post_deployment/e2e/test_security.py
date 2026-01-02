"""E2E security tests for rack designer endpoint.

Tests critical security user journeys from end to end.
These tests make real HTTP requests to the deployed API.

User Journeys:
- Input validation journey: User sends invalid data
- Not found handling journey: User accesses non-existent resource
- Error response security journey: Error responses don't leak information
"""
import requests


class TestInputValidationJourney:
    """User Journey: Validation of user input.

    Critical path: User sends malformed or invalid data.
    Failure impact: Server errors or security vulnerabilities.
    """

    def test_missing_device_id_returns_400(self, api_url):
        """Verify POST without device_id returns 400."""
        config = {"rackHeight": 12, "rackCount": 3, "placedParts": []}
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config},
            timeout=10
        )
        assert response.status_code == 400

    def test_missing_configuration_returns_400(self, api_url, test_device_id):
        """Verify POST without configuration field returns 400."""
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_invalid_configuration_returns_400(self, api_url, test_device_id):
        """Verify POST with invalid configuration returns 400."""
        config = {"rackCount": 3, "placedParts": []}  # Missing rackHeight
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={"configuration": config, "device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_get_invalid_format_returns_400(self, api_url):
        """Verify GET with invalid hash format returns 400."""
        response = requests.get(
            f"{api_url}/v1/rack-configurations/invalid",
            timeout=10
        )
        assert response.status_code == 400


class TestNotFoundHandlingJourney:
    """User Journey: Non-existent resource access.

    Critical path: User accesses a configuration that doesn't exist.
    Failure impact: Confusing error messages or server errors.
    """

    def test_get_not_found_returns_404(self, api_url):
        """Verify GET with non-existent hash returns 404."""
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        assert response.status_code == 404

    def test_404_response_is_json(self, api_url):
        """Verify 404 response returns valid JSON."""
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        try:
            response.json()
        except ValueError:
            assert False, "404 response should be valid JSON"

    def test_404_response_does_not_contain_traceback(self, api_url):
        """Verify 404 response doesn't expose stack traces."""
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        text = response.text.lower()
        assert "traceback" not in text, "Error response should not contain traceback"

    def test_404_response_does_not_contain_line_numbers(self, api_url):
        """Verify 404 response doesn't expose line numbers."""
        response = requests.get(
            f"{api_url}/v1/rack-configurations/NOTFOUND0",
            timeout=10
        )
        text = response.text.lower()
        assert "at line" not in text, "Error response should not contain line numbers"


class TestErrorResponseSecurityJourney:
    """User Journey: Error response security.

    Critical path: Server returns error responses.
    Failure impact: Information disclosure vulnerabilities.
    """

    def test_error_response_is_json(self, api_url):
        """Verify error responses return valid JSON."""
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={},  # Invalid request
            timeout=10
        )
        try:
            response.json()
        except ValueError:
            assert False, "Error response should be valid JSON"

    def test_error_response_has_error_field(self, api_url):
        """Verify error responses have an error field."""
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={},  # Invalid request
            timeout=10
        )
        data = response.json()
        assert "error" in data, "Error response should have 'error' field"

    def test_error_response_does_not_reveal_var_paths(self, api_url):
        """Verify error responses don't expose /var/ paths."""
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={},  # Invalid request
            timeout=10
        )
        text = response.text.lower()
        assert "/var/" not in text, "Error should not contain /var/ paths"

    def test_error_response_does_not_reveal_tmp_paths(self, api_url):
        """Verify error responses don't expose /tmp/ paths."""
        response = requests.post(
            f"{api_url}/v1/rack-configurations",
            json={},  # Invalid request
            timeout=10
        )
        text = response.text.lower()
        assert "/tmp/" not in text, "Error should not contain /tmp/ paths"
