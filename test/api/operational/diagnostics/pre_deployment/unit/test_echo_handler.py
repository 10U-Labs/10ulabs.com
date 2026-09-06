from types import ModuleType
from typing import Any, Callable, Dict
from unittest.mock import Mock

from lambda_response import parse_response_body


def _echoed_body(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> Dict[str, Any]:
    event = echo_post_event_factory()
    response = echo_handler.lambda_handler(event, lambda_context)
    return parse_response_body(response)


def test_echo_handler_returns_200_status_code(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    event = echo_post_event_factory()
    response = echo_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_echo_handler_returns_json_content_type(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    event = echo_post_event_factory()
    response = echo_handler.lambda_handler(event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


def test_echo_handler_returns_cors_header(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    event = echo_post_event_factory()
    response = echo_handler.lambda_handler(event, lambda_context)
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_echo_handler_echoes_input_data(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    payload = {'message': 'hello', 'number': 42}
    event = echo_post_event_factory(body_data=payload)
    response = echo_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    echoed_data_matches = body['echo'] == payload
    assert echoed_data_matches


def test_echo_handler_includes_received_at(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    body = _echoed_body(echo_handler, echo_post_event_factory, lambda_context)
    has_received_at = 'received_at' in body
    assert has_received_at


def test_echo_handler_with_invalid_json_returns_400(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    event = echo_post_event_factory()
    event['body'] = 'not valid json'
    response = echo_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_echo_handler_body_contains_echo_key(
    echo_handler: ModuleType,
    echo_post_event_factory: Callable[..., Dict[str, Any]],
    lambda_context: Mock
) -> None:
    body = _echoed_body(echo_handler, echo_post_event_factory, lambda_context)
    has_echo_key = 'echo' in body
    assert has_echo_key


def test_echo_handler_options_returns_200(echo_handler: ModuleType, lambda_context: Mock) -> None:
    event = {'path': '/diagnostics/echo', 'httpMethod': 'OPTIONS'}
    response = echo_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_echo_handler_unknown_route_returns_404(
    echo_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = {'path': '/v1/unknown', 'httpMethod': 'POST', 'body': '{}'}
    response = echo_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 404
