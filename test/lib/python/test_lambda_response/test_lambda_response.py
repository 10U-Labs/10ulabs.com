"""Comprehensive tests for lambda_response module."""
import json
import pytest

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)


# === parse_response_body ===


class TestParseResponseBody:
    """Tests for parse_response_body function."""

    def test_parses_json_body(self):
        """parse_response_body parses JSON body."""
        response = {"body": '{"key": "value"}'}
        result = parse_response_body(response)
        assert result == {"key": "value"}

    def test_parses_nested_json(self):
        """parse_response_body parses nested JSON."""
        response = {"body": '{"nested": {"key": "value"}}'}
        result = parse_response_body(response)
        assert result == {"nested": {"key": "value"}}

    def test_parses_array_body(self):
        """parse_response_body parses array body."""
        response = {"body": '[1, 2, 3]'}
        result = parse_response_body(response)
        assert result == [1, 2, 3]

    def test_parses_empty_object(self):
        """parse_response_body parses empty object."""
        response = {"body": "{}"}
        result = parse_response_body(response)
        assert result == {}

    def test_parses_string_value(self):
        """parse_response_body parses string value."""
        response = {"body": '"hello"'}
        result = parse_response_body(response)
        assert result == "hello"

    def test_parses_number_value(self):
        """parse_response_body parses number value."""
        response = {"body": "42"}
        result = parse_response_body(response)
        assert result == 42


# === assert_response_status ===


class TestAssertResponseStatus:
    """Tests for assert_response_status function."""

    def test_passes_for_matching_status(self):
        """assert_response_status passes when status matches."""
        response = {"statusCode": 200}
        assert_response_status(response, 200)  # Should not raise

    def test_passes_for_404_status(self):
        """assert_response_status passes for 404."""
        response = {"statusCode": 404}
        assert_response_status(response, 404)  # Should not raise

    def test_fails_for_mismatched_status(self):
        """assert_response_status fails when status doesn't match."""
        response = {"statusCode": 500}
        with pytest.raises(AssertionError):
            assert_response_status(response, 200)

    def test_fails_when_expecting_200_got_400(self):
        """assert_response_status fails when expecting 200 but got 400."""
        response = {"statusCode": 400}
        with pytest.raises(AssertionError):
            assert_response_status(response, 200)


# === assert_json_content_type ===


class TestAssertJsonContentType:
    """Tests for assert_json_content_type function."""

    def test_passes_for_application_json(self):
        """assert_json_content_type passes for application/json."""
        response = {"headers": {"Content-Type": "application/json"}}
        assert_json_content_type(response)  # Should not raise

    def test_passes_for_json_with_charset(self):
        """assert_json_content_type passes for json with charset."""
        response = {"headers": {"Content-Type": "application/json; charset=utf-8"}}
        assert_json_content_type(response)  # Should not raise

    def test_fails_for_text_html(self):
        """assert_json_content_type fails for text/html."""
        response = {"headers": {"Content-Type": "text/html"}}
        with pytest.raises(AssertionError):
            assert_json_content_type(response)

    def test_fails_for_text_plain(self):
        """assert_json_content_type fails for text/plain."""
        response = {"headers": {"Content-Type": "text/plain"}}
        with pytest.raises(AssertionError):
            assert_json_content_type(response)


# === assert_cors_headers ===


class TestAssertCorsHeaders:
    """Tests for assert_cors_headers function."""

    def test_passes_with_allow_origin(self):
        """assert_cors_headers passes with Access-Control-Allow-Origin."""
        response = {"headers": {"Access-Control-Allow-Origin": "*"}}
        assert_cors_headers(response)  # Should not raise

    def test_passes_with_specific_origin(self):
        """assert_cors_headers passes with specific origin."""
        response = {"headers": {"Access-Control-Allow-Origin": "https://example.com"}}
        assert_cors_headers(response)  # Should not raise

    def test_fails_without_cors_header(self):
        """assert_cors_headers fails without CORS header."""
        response = {"headers": {"Content-Type": "application/json"}}
        with pytest.raises(AssertionError):
            assert_cors_headers(response)

    def test_fails_with_empty_headers(self):
        """assert_cors_headers fails with empty headers."""
        response = {"headers": {}}
        with pytest.raises(AssertionError):
            assert_cors_headers(response)
