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
