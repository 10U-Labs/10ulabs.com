"""Tests for Lambda handler functions."""

import json


def test_lambda_handler_catchall_returns_404_for_unknown_path(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns 404 for unknown path."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert response['statusCode'] == 404


def test_lambda_handler_catchall_returns_json_content_type(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns JSON content type."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


def test_lambda_handler_catchall_returns_cors_header(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler returns CORS headers."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_lambda_handler_catchall_body_contains_error_message(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler body contains error message."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = json.loads(response['body'])
    assert 'error' in body
