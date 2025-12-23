"""Unit tests for echo Lambda handler."""
import json
from typing import Any, Dict


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON response body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert that response has expected HTTP status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert that response has JSON content type header."""
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert that response includes CORS headers."""
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_echo_handler_returns_200_status_code(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler returns 200 status code."""
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_echo_handler_returns_json_content_type(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler returns JSON content type."""
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_json_content_type(response)


def test_echo_handler_returns_cors_header(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler includes CORS headers."""
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_cors_headers(response)


def test_echo_handler_echoes_input_data(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler returns the input data."""
    payload = {'message': 'hello', 'number': 42}
    event = echo_post_event_factory(body_data=payload)
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    echoed_data_matches = body['echo'] == payload
    assert echoed_data_matches


def test_echo_handler_includes_received_at(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler includes received_at timestamp."""
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_received_at = 'received_at' in body
    assert has_received_at


def test_echo_handler_with_invalid_json_returns_400(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler returns 400 for invalid JSON."""
    event = echo_post_event_factory()
    event['body'] = 'not valid json'
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 400)


def test_echo_handler_body_contains_echo_key(
    echo_handler, echo_post_event_factory, lambda_context
):
    """Test that echo handler response body contains echo key."""
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_echo_key = 'echo' in body
    assert has_echo_key


def test_echo_handler_options_returns_200(echo_handler, lambda_context):
    """Test that OPTIONS request returns 200."""
    event = {'path': '/diagnostics/echo', 'httpMethod': 'OPTIONS'}
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_echo_handler_unknown_route_returns_404(echo_handler, lambda_context):
    """Test that unknown route returns 404."""
    event = {'path': '/v1/unknown', 'httpMethod': 'POST', 'body': '{}'}
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 404)
