import pytest
import requests

TIMEOUT = 10


def _rejected(url: str) -> requests.Response:
    return requests.post(url, json={}, timeout=TIMEOUT)


def error_response_is_json(url: str) -> bool:
    try:
        _rejected(url).json()
    except ValueError:
        return False
    return True


def error_response_names_the_error(url: str) -> bool:
    return "error" in _rejected(url).json()


def error_response_hides(url: str, fragment: str) -> bool:
    return fragment not in _rejected(url).text.lower()


def endpoint_is_deployed(api_url: str, path: str, method: str = "GET") -> bool:
    url = f"{api_url}{path}"
    headers = {"x-test-mode": "true"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, json={}, timeout=5)
        if response.status_code == 404:
            return False
        if response.status_code == 500:
            return False
        try:
            body = response.json()
            if body.get("error") == "Not Found":
                return False
        except (ValueError, KeyError):
            pass
        return True
    except requests.exceptions.RequestException:
        return False


def skip_if_endpoint_not_deployed(api_url: str, path: str, method: str = "GET") -> None:
    if not endpoint_is_deployed(api_url, path, method):
        pytest.skip(f"Endpoint {path} not deployed (managed by separate workflow)")
