"""Unit tests for test_fixtures.http_endpoint module."""
from unittest.mock import MagicMock, call, patch

from test_fixtures.http_endpoint import (
    TIMEOUT,
    error_response_hides,
    error_response_is_json,
    error_response_names_the_error,
)

URL = "https://example.invalid/v1/thing"


def _response(payload=None, text="", raises=False):
    """Build a response whose json() answers, or refuses to."""
    response = MagicMock()
    response.json.side_effect = ValueError if raises else None
    response.json.return_value = payload if payload is not None else {}
    response.text = text
    return response


def test_a_rejected_request_carries_an_empty_body():
    """The request the checks send is one the endpoint has to reject."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response()
        error_response_is_json(URL)
        assert post.call_args == call(URL, json={}, timeout=TIMEOUT)


def test_error_response_is_json_when_the_body_parses():
    """An error response that parses as JSON is reported as JSON."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"error": "bad request"})
        assert error_response_is_json(URL)


def test_error_response_is_not_json_when_the_body_does_not_parse():
    """An error response that does not parse is reported as not JSON."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(raises=True)
        assert not error_response_is_json(URL)


def test_error_response_names_the_error_when_the_field_is_there():
    """An error response carrying an error field is reported as naming it."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"error": "bad request"})
        assert error_response_names_the_error(URL)


def test_error_response_names_no_error_when_the_field_is_missing():
    """An error response with no error field is reported as missing it."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"message": "bad request"})
        assert not error_response_names_the_error(URL)


def test_error_response_hides_a_path_it_does_not_carry():
    """A body without the fragment is reported as hiding it."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(text="Bad Request")
        assert error_response_hides(URL, "/var/")


def test_error_response_hides_nothing_when_the_path_is_in_the_body():
    """A body carrying the fragment is reported as not hiding it."""
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(text="failed at /VAR/task/handler.py")
        assert not error_response_hides(URL, "/var/")
