"""Tests for Lambda handler functions."""

from .conftest import (
    assert_cors_headers,
    assert_json_content_type,
    assert_response_status,
    parse_response_body,
)


def test_lambda_handler_catchall_returns_404_for_unknown_path(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns 404 for unknown path."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_catchall_returns_json_content_type(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns JSON content type."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_catchall_returns_cors_header(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns CORS headers."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_catchall_body_contains_error_message(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler body contains error message."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = parse_response_body(response)
    assert 'error' in body
