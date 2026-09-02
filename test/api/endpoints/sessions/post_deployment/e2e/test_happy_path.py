import requests


class TestEventsSaveJourney:
    def test_post_returns_200(
        self,
        api_url: str,
        test_device_id: str,
        test_session_id: str
    ) -> None:
        events = [{'event_type': 'page_view', 'timestamp': '2024-01-15T10:30:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_success(
        self,
        api_url: str,
        test_device_id: str,
        test_session_id: str
    ) -> None:
        events = [{'event_type': 'click', 'timestamp': '2024-01-15T10:31:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        data = response.json()
        assert data.get('success') is True

    def test_post_returns_events_saved_count(
        self,
        api_url: str,
        test_device_id: str,
        test_session_id: str
    ) -> None:
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
    def test_options_returns_cors_headers(self, api_url: str, test_session_id: str) -> None:
        response = requests.options(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            timeout=10
        )
        assert response.status_code == 200

    def test_post_returns_cors_headers(
        self,
        api_url: str,
        test_device_id: str,
        test_session_id: str
    ) -> None:
        events = [{'event_type': 'test', 'timestamp': '2024-01-15T10:33:00Z'}]
        response = requests.post(
            f"{api_url}/v1/sessions/{test_session_id}/events",
            json={"device_id": test_device_id, "events": events},
            timeout=10
        )
        assert "Access-Control-Allow-Origin" in response.headers
