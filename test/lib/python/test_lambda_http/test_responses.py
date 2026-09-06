import base64
import json
from typing import Any, Dict

from lambda_http import (
    CORS_HEADERS,
    dispatch,
    error_response,
    json_response,
    options_response,
    parse_body,
)


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


def test_error_response_sets_status_code() -> None:
    response = error_response(400, 'Bad request')
    assert response['statusCode'] == 400


def test_error_response_marks_failure() -> None:
    body = json.loads(error_response(400, 'Bad request')['body'])
    assert body['success'] is False


def test_error_response_carries_the_message() -> None:
    body = json.loads(error_response(400, 'Bad request')['body'])
    assert body['error'] == 'Bad request'


def test_error_response_includes_details_when_given() -> None:
    body = json.loads(error_response(400, 'Bad request', 'field missing')['body'])
    assert body['details'] == 'field missing'


def test_error_response_omits_details_when_empty() -> None:
    body = json.loads(error_response(400, 'Bad request', '')['body'])
    assert 'details' not in body


def test_options_response_returns_200() -> None:
    assert options_response()['statusCode'] == 200


def test_options_response_has_empty_body() -> None:
    assert options_response()['body'] == ''


def test_options_response_carries_cors_methods() -> None:
    headers = options_response()['headers']
    assert headers['Access-Control-Allow-Methods'] == 'GET,POST,DELETE,OPTIONS'


def test_options_response_headers_are_not_the_shared_dict() -> None:
    options_response()['headers']['Access-Control-Allow-Origin'] = 'mutated'
    assert CORS_HEADERS['Access-Control-Allow-Origin'] == '*'


def test_parses_base64_encoded_body() -> None:
    encoded = base64.b64encode(b'{"key": "value"}').decode('utf-8')
    result = parse_body({'body': encoded, 'isBase64Encoded': True})
    assert result == {'key': 'value'}


def test_ignores_base64_flag_for_dict_body() -> None:
    result = parse_body({'body': {'key': 'value'}, 'isBase64Encoded': True})
    assert result == {'key': 'value'}


def test_handles_none_body() -> None:
    assert parse_body({'body': None}) == {}


def test_handles_empty_string_body() -> None:
    assert parse_body({'body': ''}) == {}


def _always(_path: str, _method: str) -> bool:
    return True


def _never(_path: str, _method: str) -> bool:
    return False


def _marker(_event: Dict[str, Any]) -> Dict[str, Any]:
    return json_response(200, {'routed': True})


def test_dispatch_answers_options_without_consulting_routes() -> None:
    response = dispatch({'httpMethod': 'OPTIONS'}, ((_always, _marker),))
    assert response['body'] == ''


def test_dispatch_calls_the_first_matching_route() -> None:
    response = dispatch({'httpMethod': 'GET', 'path': '/x'}, ((_always, _marker),))
    assert json.loads(response['body'])['routed'] is True


def test_dispatch_skips_a_route_that_does_not_match() -> None:
    routes = ((_never, _marker), (_always, _marker))
    response = dispatch({'httpMethod': 'GET', 'path': '/x'}, routes)
    assert response['statusCode'] == 200


def test_dispatch_returns_404_when_no_route_matches() -> None:
    response = dispatch({'httpMethod': 'GET', 'path': '/x'}, ((_never, _marker),))
    assert response['statusCode'] == 404


def test_dispatch_404_names_not_found() -> None:
    response = dispatch({'httpMethod': 'GET', 'path': '/x'}, ())
    assert json.loads(response['body'])['error'] == 'Not found'
