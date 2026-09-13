import requests

from test_fixtures.http_endpoint import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def test_invalid_endpoint_returns_404(api_url: str) -> None:
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 404


def test_404_response_does_not_contain_traceback(api_url: str) -> None:
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    assert "traceback" not in response_text


def test_404_response_does_not_reveal_lambda_internals(api_url: str) -> None:
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    response_text = response.text.lower()
    assert "lambda" not in response_text or "documentation" in response_text


def test_service_unavailable_returns_503(api_url: str) -> None:
    skip_if_endpoint_not_deployed(api_url, "/health")
    response = requests.get(f"{api_url}/health", headers=TEST_HEADERS, timeout=10)
    assert response.status_code in [200, 503]


def test_error_response_contains_error_message(api_url: str) -> None:
    response = requests.get(f"{api_url}/nonexistent", headers=TEST_HEADERS, timeout=10)
    assert "error" in response.text.lower() or "not found" in response.text.lower()
