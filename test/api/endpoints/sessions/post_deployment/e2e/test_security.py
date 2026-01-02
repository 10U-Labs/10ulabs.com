"""E2E security tests for sessions endpoint.

Tests critical security user journeys from end to end.
These tests make real HTTP requests to the deployed API.

User Journeys:
- Input validation journey: User sends invalid data
- Error response security journey: Error responses don't leak information
"""
import requests


class TestInputValidationJourney:
    """User Journey: Validation of user input.

    Critical path: User sends malformed or invalid data.
    Failure impact: Server errors or security vulnerabilities.
    """

    def test_missing_device_id_returns_400(self, api_url, test_session_id):
        """Verify POST without device_id returns 400."""
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"events": events},
            timeout=10
        )
        assert response.status_code == 400

    def test_missing_events_returns_400(self, api_url, test_device_id, test_session_id):
        """Verify POST without events field returns 400."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_empty_events_returns_400(self, api_url, test_device_id, test_session_id):
        """Verify POST with empty events array returns 400."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": []},
            timeout=10
        )
        assert response.status_code == 400

    def test_invalid_event_format_returns_400(self, api_url, test_device_id, test_session_id):
        """Verify POST with invalid event format returns 400."""
        events = [{'event_type': 'test'}]  # Missing timestamp
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert response.status_code == 400


class TestErrorResponseSecurityJourney:
    """User Journey: Error response security.

    Critical path: Server returns error responses.
    Failure impact: Information disclosure vulnerabilities.
    """

    def test_error_response_is_json(self, api_url, test_session_id):
        """Verify error responses return valid JSON."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={},  # Invalid request
            timeout=10
        )
        try:
            response.json()
        except ValueError:
            assert False, "Error response should be valid JSON"

    def test_error_response_has_error_field(self, api_url, test_session_id):
        """Verify error responses have an error field."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={},  # Invalid request
            timeout=10
        )
        data = response.json()
        assert "error" in data, "Error response should have 'error' field"

    def test_error_response_does_not_reveal_var_paths(self, api_url, test_session_id):
        """Verify error responses don't expose /var/ paths."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={},  # Invalid request
            timeout=10
        )
        text = response.text.lower()
        assert "/var/" not in text, "Error should not contain /var/ paths"

    def test_error_response_does_not_reveal_tmp_paths(self, api_url, test_session_id):
        """Verify error responses don't expose /tmp/ paths."""
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={},  # Invalid request
            timeout=10
        )
        text = response.text.lower()
        assert "/tmp/" not in text, "Error should not contain /tmp/ paths"
