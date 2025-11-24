import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import parse_response_body, assert_response_status, assert_json_content_type, assert_cors_headers


def test_lambda_handler_health_endpoint_returns_200_status_code(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_health_endpoint_returns_json_content_type(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_health_endpoint_returns_cors_header(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_health_endpoint_body_contains_status(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert 'status' in body


def test_lambda_handler_health_endpoint_status_is_healthy(health_handler, health_get_event, lambda_context):
    response = health_handler.handler(health_get_event, lambda_context)
    body = parse_response_body(response)
    assert body['status'] == 'healthy'


def test_lambda_handler_catchall_returns_404_for_unknown_path(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_catchall_returns_json_content_type(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_catchall_returns_cors_header(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_catchall_body_contains_error_message(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = parse_response_body(response)
    assert 'error' in body
