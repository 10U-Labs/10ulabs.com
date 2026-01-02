"""E2E happy path tests for sessions endpoint.

Tests critical user journeys from end to end.
These tests make real HTTP requests to the deployed API.

User Journeys:
- Save events journey: User saves session events
- CORS journey: Browser preflight requests work correctly
"""
import requests


class TestEventsSaveJourney:
    """User Journey: User saves session events.

    Critical path: User's browser sends analytics events to track usage.
    Failure impact: Analytics data is lost.
    """

    def test_post_returns_200(self, api_url, test_device_id, test_session_id):
        """Verify POST returns 200 status code."""
        events = [{'event_type': 'page_view', 'timestamp': '2024-01-15T10:30:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_success(self, api_url, test_device_id, test_session_id):
        """Verify POST returns success in response body."""
        events = [{'event_type': 'click', 'timestamp': '2024-01-15T10:31:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        data = response.json()
        assert data.get('success') is True

    def test_post_returns_events_saved_count(self, api_url, test_device_id, test_session_id):
        """Verify POST returns correct events_saved count."""
        events = [
            {'event_type': 'page_view', 'timestamp': '2024-01-15T10:32:00Z'},
            {'event_type': 'click', 'timestamp': '2024-01-15T10:32:01Z'}
        ]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        data = response.json()
        assert data.get('events_saved') == 2


class TestCORSJourney:
    """User Journey: Browser preflight request.

    Critical path: Browser sends OPTIONS request before POST.
    Failure impact: Frontend cannot communicate with API.
    """

    def test_options_returns_cors_headers(self, api_url, test_session_id):
        """Verify OPTIONS request returns CORS headers."""
        response = requests.options(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_cors_headers(self, api_url, test_device_id, test_session_id):
        """Verify POST request returns CORS headers."""
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:33:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert "Access-Control-Allow-Origin" in response.headers
