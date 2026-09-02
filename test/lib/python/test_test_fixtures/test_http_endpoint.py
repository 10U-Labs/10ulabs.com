from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
import requests

from test_fixtures.http_endpoint import (
    TIMEOUT,
    endpoint_is_deployed,
    error_response_hides,
    error_response_is_json,
    error_response_names_the_error,
    skip_if_endpoint_not_deployed,
)

URL = "https://example.invalid/v1/thing"
BASE = "https://example.invalid"
PATH = "/v1/thing"
HEADERS = {"x-test-mode": "true"}


def _response(payload: Any = None, text: str = "", raises: bool = False) -> MagicMock:
    response = MagicMock()
    response.json.side_effect = ValueError if raises else None
    response.json.return_value = payload if payload is not None else {}
    response.text = text
    return response


def test_a_rejected_request_carries_an_empty_body() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response()
        error_response_is_json(URL)
        assert post.call_args == call(URL, json={}, timeout=TIMEOUT)


def test_error_response_is_json_when_the_body_parses() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"error": "bad request"})
        assert error_response_is_json(URL)


def test_error_response_is_not_json_when_the_body_does_not_parse() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(raises=True)
        assert not error_response_is_json(URL)


def test_error_response_names_the_error_when_the_field_is_there() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"error": "bad request"})
        assert error_response_names_the_error(URL)


def test_error_response_names_no_error_when_the_field_is_missing() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response({"message": "bad request"})
        assert not error_response_names_the_error(URL)


def test_error_response_hides_a_path_it_does_not_carry() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(text="Bad Request")
        assert error_response_hides(URL, "/var/")


def test_error_response_hides_nothing_when_the_path_is_in_the_body() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _response(text="failed at /VAR/task/handler.py")
        assert not error_response_hides(URL, "/var/")


def _reply(status: int = 200, payload: Any = None, raises: bool = False) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.json.side_effect = ValueError if raises else None
    response.json.return_value = payload if payload is not None else {}
    return response


def test_endpoint_is_not_deployed_when_the_status_is_404() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(status=404)
        assert not endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_not_deployed_when_the_status_is_500() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(status=500)
        assert not endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_not_deployed_when_the_body_names_a_not_found_error() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(payload={"error": "Not Found"})
        assert not endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_deployed_when_the_body_names_another_error() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(payload={"error": "Bad Request"})
        assert endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_deployed_when_the_body_does_not_parse() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(raises=True)
        assert endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_not_deployed_when_the_request_raises() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.side_effect = requests.exceptions.RequestException
        assert not endpoint_is_deployed(BASE, PATH)


def test_endpoint_is_asked_with_post_when_the_method_is_post() -> None:
    with patch("test_fixtures.http_endpoint.requests.post") as post:
        post.return_value = _reply()
        endpoint_is_deployed(BASE, PATH, "POST")
        assert post.call_args == call(URL, headers=HEADERS, json={}, timeout=5)


def test_skip_if_endpoint_not_deployed_skips_when_it_is_not() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply(status=404)
        with pytest.raises(pytest.skip.Exception):
            skip_if_endpoint_not_deployed(BASE, PATH)


def test_skip_if_endpoint_not_deployed_returns_when_it_is() -> None:
    with patch("test_fixtures.http_endpoint.requests.get") as get:
        get.return_value = _reply()
        assert skip_if_endpoint_not_deployed(BASE, PATH) is None
