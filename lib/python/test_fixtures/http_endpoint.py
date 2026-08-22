"""Checks on what a live endpoint's error responses give away.

Every endpoint here answers a request it must reject the same way, so the
checks are written once and each suite hands them the URL of its own endpoint.
"""
import requests

TIMEOUT = 10


def _rejected(url: str) -> requests.Response:
    """Post a body the endpoint has to reject and hand back the response."""
    return requests.post(url, json={}, timeout=TIMEOUT)


def error_response_is_json(url: str) -> bool:
    """Say whether the endpoint's error response parses as JSON."""
    try:
        _rejected(url).json()
    except ValueError:
        return False
    return True


def error_response_names_the_error(url: str) -> bool:
    """Say whether the endpoint's error response carries an error field."""
    return "error" in _rejected(url).json()


def error_response_hides(url: str, fragment: str) -> bool:
    """Say whether the endpoint's error response keeps a path out of its body."""
    return fragment not in _rejected(url).text.lower()
