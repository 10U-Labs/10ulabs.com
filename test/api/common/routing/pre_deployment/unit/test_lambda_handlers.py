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


def test_lambda_handler_catchall_body_contains_message_field(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler body contains message field."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = json.loads(response['body'])
    assert 'message' in body


def test_lambda_handler_catchall_body_contains_path_field(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler body contains path field with event path."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = json.loads(response['body'])
    assert body['path'] == '/unknown'


def test_lambda_handler_catchall_path_defaults_to_unknown_when_missing(
    catchall_handler, lambda_context
):
    """Verify that catchall handler defaults path to 'unknown' when event has no path."""
    event_without_path = {'httpMethod': 'GET'}
    response = catchall_handler.handler(event_without_path, lambda_context)
    body = json.loads(response['body'])
    assert body['path'] == 'unknown'


def test_lambda_handler_catchall_error_value_is_not_found(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler error value is 'Not Found'."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = json.loads(response['body'])
    assert body['error'] == 'Not Found'


def test_lambda_handler_catchall_message_describes_missing_endpoint(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler message describes endpoint not found."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = json.loads(response['body'])
    assert 'endpoint does not exist' in body['message']


def test_lambda_handler_catchall_cors_header_allows_all_origins(
    catchall_handler, catchall_unknown_event, lambda_context
):
    """Verify that catchall handler CORS header allows all origins (*)."""
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
