"""Utilities for parsing and asserting on Lambda responses."""
import json
from typing import Any, Dict


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON body from Lambda response.

    Args:
        response: Lambda response dict with 'body' key.

    Returns:
        Parsed JSON content from the response body.
    """
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert that response has expected HTTP status code.

    Args:
        response: Lambda response dict with 'statusCode' key.
        expected_code: Expected HTTP status code.

    Raises:
        AssertionError: If status code doesn't match.
    """
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert that response has JSON content type header.

    Args:
        response: Lambda response dict with 'headers' key.

    Raises:
        AssertionError: If Content-Type header is not JSON.
    """
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert that response includes CORS headers.

    Args:
        response: Lambda response dict with 'headers' key.

    Raises:
        AssertionError: If Access-Control-Allow-Origin header is missing.
    """
    assert 'Access-Control-Allow-Origin' in response['headers']
