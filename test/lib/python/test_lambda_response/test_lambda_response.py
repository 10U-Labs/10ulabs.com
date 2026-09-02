from typing import Any, Dict

import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)
from test_fixtures.outcomes import accepted


class TestParseResponseBody:
    def test_parses_json_body(self) -> None:
        response = {"body": '{"key": "value"}'}
        result = parse_response_body(response)
        assert result == {"key": "value"}

    def test_parses_nested_json(self) -> None:
        response = {"body": '{"nested": {"key": "value"}}'}
        result = parse_response_body(response)
        assert result == {"nested": {"key": "value"}}

    def test_parses_array_body(self) -> None:
        response = {"body": '[1, 2, 3]'}
        result = parse_response_body(response)
        assert result == [1, 2, 3]

    def test_parses_empty_object(self) -> None:
        response = {"body": "{}"}
        result = parse_response_body(response)
        assert result == {}

    def test_parses_string_value(self) -> None:
        response = {"body": '"hello"'}
        result = parse_response_body(response)
        assert result == "hello"

    def test_parses_number_value(self) -> None:
        response = {"body": "42"}
        result = parse_response_body(response)
        assert result == 42


class TestAssertResponseStatus:
    def test_passes_for_matching_status(self) -> None:
        response = {"statusCode": 200}
        assert accepted(assert_response_status, response, 200)

    def test_passes_for_404_status(self) -> None:
        response = {"statusCode": 404}
        assert accepted(assert_response_status, response, 404)

    def test_fails_for_mismatched_status(self) -> None:
        response = {"statusCode": 500}
        with pytest.raises(AssertionError):
            assert_response_status(response, 200)

    def test_fails_when_expecting_200_got_400(self) -> None:
        response = {"statusCode": 400}
        with pytest.raises(AssertionError):
            assert_response_status(response, 200)


class TestAssertJsonContentType:
    def test_passes_for_application_json(self) -> None:
        response = {"headers": {"Content-Type": "application/json"}}
        assert accepted(assert_json_content_type, response)

    def test_passes_for_json_with_charset(self) -> None:
        response = {"headers": {"Content-Type": "application/json; charset=utf-8"}}
        assert accepted(assert_json_content_type, response)

    def test_fails_for_text_html(self) -> None:
        response = {"headers": {"Content-Type": "text/html"}}
        with pytest.raises(AssertionError):
            assert_json_content_type(response)

    def test_fails_for_text_plain(self) -> None:
        response = {"headers": {"Content-Type": "text/plain"}}
        with pytest.raises(AssertionError):
            assert_json_content_type(response)


class TestAssertCorsHeaders:
    def test_passes_with_allow_origin(self) -> None:
        response = {"headers": {"Access-Control-Allow-Origin": "*"}}
        assert accepted(assert_cors_headers, response)

    def test_passes_with_specific_origin(self) -> None:
        response = {"headers": {"Access-Control-Allow-Origin": "https://example.com"}}
        assert accepted(assert_cors_headers, response)

    def test_fails_without_cors_header(self) -> None:
        response = {"headers": {"Content-Type": "application/json"}}
        with pytest.raises(AssertionError):
            assert_cors_headers(response)

    def test_fails_with_empty_headers(self) -> None:
        response: Dict[str, Any] = {"headers": {}}
        with pytest.raises(AssertionError):
            assert_cors_headers(response)
