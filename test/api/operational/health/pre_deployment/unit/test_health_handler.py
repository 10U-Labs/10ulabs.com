"""Unit tests for health endpoint handler."""
from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)


def test_health_handler_returns_200_status_code(
    health_handler, health_get_event, lambda_context
):
    """Verify handler returns HTTP 200."""
    response = health_handler.handler(health_get_event, lambda_context)
    assert_response_status(response, 200)


def test_health_handler_returns_json_content_type(
    health_handler, health_get_event, lambda_context
):
    """Verify handler returns JSON content type."""
    response = health_handler.handler(health_get_event, lambda_context)
    assert_json_content_type(response)


def test_health_handler_returns_cors_header(
    health_handler, health_get_event, lambda_context
):
    """Verify handler returns CORS headers."""
    response = health_handler.handler(health_get_event, lambda_context)
    assert_cors_headers(response)


def test_health_handler_body_contains_status(
    health_handler, health_get_event, lambda_context
):
    """Verify response body contains status field."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert 'status' in body


def test_health_handler_status_is_healthy(
    health_handler, health_get_event, lambda_context
):
    """Verify status is healthy."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert body['status'] == 'healthy'


def test_health_handler_body_contains_service(
    health_handler, health_get_event, lambda_context
):
    """Verify response body contains service field."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert 'service' in body


def test_health_handler_service_is_10u_labs_api(
    health_handler, health_get_event, lambda_context
):
    """Verify service is '10U Labs API'."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert body['service'] == '10U Labs API'


def test_health_handler_body_contains_version(
    health_handler, health_get_event, lambda_context
):
    """Verify response body contains version field."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert 'version' in body


def test_health_handler_version_is_1_0_0(
    health_handler, health_get_event, lambda_context
):
    """Verify version is '1.0.0'."""
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert body['version'] == '1.0.0'


def test_handler_returns_404_for_unknown_path(health_handler, lambda_context):
    """Verify handler returns 404 for unknown path."""
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    response = health_handler.handler(event, lambda_context)
    assert_response_status(response, 404)


def test_handler_returns_404_for_unknown_method(health_handler, lambda_context):
    """Verify handler returns 404 for unknown HTTP method."""
    event = {'path': '/health', 'httpMethod': 'POST'}
    response = health_handler.handler(event, lambda_context)
    assert_response_status(response, 404)


def test_handler_404_response_contains_error_field(health_handler, lambda_context):
    """Verify 404 response body contains error field."""
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    response = health_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'error' in body
