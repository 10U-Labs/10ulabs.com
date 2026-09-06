import json
from typing import Any, Dict

from lambda_http import json_response, parse_body


def test_returns_correct_status_code() -> None:
    response = json_response(200, {'key': 'value'})
    assert response['statusCode'] == 200


def test_returns_404_status_code() -> None:
    response = json_response(404, {'error': 'not found'})
    assert response['statusCode'] == 404


def test_returns_json_content_type() -> None:
    response = json_response(200, {})
    assert response['headers']['Content-Type'] == 'application/json'


def test_returns_cors_allow_origin() -> None:
    response = json_response(200, {})
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_returns_cors_allow_methods() -> None:
    response = json_response(200, {})
    assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,DELETE,OPTIONS'


def test_returns_cors_allow_headers() -> None:
    response = json_response(200, {})
    assert 'x-api-key' in response['headers']['Access-Control-Allow-Headers']


def test_serializes_body_as_json() -> None:
    response = json_response(200, {'key': 'value'})
    assert json.loads(response['body']) == {'key': 'value'}


def test_serializes_empty_body() -> None:
    response = json_response(200, {})
    assert json.loads(response['body']) == {}


def test_serializes_nested_body() -> None:
    response = json_response(200, {'nested': {'key': 'value'}})
    assert json.loads(response['body']) == {'nested': {'key': 'value'}}


def test_parses_json_string_body() -> None:
    event = {'body': '{"key": "value"}'}
    result = parse_body(event)
    assert result == {'key': 'value'}


def test_returns_dict_body_unchanged() -> None:
    event = {'body': {'key': 'value'}}
    result = parse_body(event)
    assert result == {'key': 'value'}


def test_handles_missing_body() -> None:
    event: Dict[str, Any] = {}
    result = parse_body(event)
    assert result == {}


def test_handles_empty_dict_body() -> None:
    event: Dict[str, Any] = {'body': {}}
    result = parse_body(event)
    assert result == {}


def test_parses_nested_json() -> None:
    event = {'body': '{"nested": {"key": "value"}}'}
    result = parse_body(event)
    assert result == {'nested': {'key': 'value'}}
