import requests

from test_fixtures.http_endpoint import (
    error_response_hides,
    error_response_is_json,
    error_response_names_the_error,
)


class TestInputValidationJourney:
    def test_missing_device_id_returns_400(self, api_url, test_session_id):
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:30:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"events": events},
            timeout=10
        )
        assert response.status_code == 400

    def test_missing_events_returns_400(self, api_url, test_device_id, test_session_id):
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id},
            timeout=10
        )
        assert response.status_code == 400

    def test_empty_events_returns_400(self, api_url, test_device_id, test_session_id):
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": []},
            timeout=10
        )
        assert response.status_code == 400

    def test_invalid_event_format_returns_400(self, api_url, test_device_id, test_session_id):
        events = [{'event_type': 'test'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert response.status_code == 400


class TestErrorResponseSecurityJourney:
    def test_error_response_is_json(self, api_url, test_session_id):
        assert error_response_is_json(
            f"{api_url}/v1/sessions/{test_session_id}/events")

    def test_error_response_has_error_field(self, api_url, test_session_id):
        assert error_response_names_the_error(
            f"{api_url}/v1/sessions/{test_session_id}/events")

    def test_error_response_does_not_reveal_var_paths(self, api_url, test_session_id):
        assert error_response_hides(
            f"{api_url}/v1/sessions/{test_session_id}/events", "/var/")

    def test_error_response_does_not_reveal_tmp_paths(self, api_url, test_session_id):
        assert error_response_hides(
            f"{api_url}/v1/sessions/{test_session_id}/events", "/tmp/")
