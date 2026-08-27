import json

from lambda_http import json_response, parse_body


class TestJsonResponse:
    def test_returns_correct_status_code(self):
        response = json_response(200, {'key': 'value'})
        assert response['statusCode'] == 200

    def test_returns_404_status_code(self):
        response = json_response(404, {'error': 'not found'})
        assert response['statusCode'] == 404

    def test_returns_json_content_type(self):
        response = json_response(200, {})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_returns_cors_allow_origin(self):
        response = json_response(200, {})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_returns_cors_allow_methods(self):
        response = json_response(200, {})
        assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,DELETE,OPTIONS'

    def test_returns_cors_allow_headers(self):
        response = json_response(200, {})
        assert 'x-api-key' in response['headers']['Access-Control-Allow-Headers']

    def test_serializes_body_as_json(self):
        response = json_response(200, {'key': 'value'})
        assert json.loads(response['body']) == {'key': 'value'}

    def test_serializes_empty_body(self):
        response = json_response(200, {})
        assert json.loads(response['body']) == {}

    def test_serializes_nested_body(self):
        response = json_response(200, {'nested': {'key': 'value'}})
        assert json.loads(response['body']) == {'nested': {'key': 'value'}}


class TestParseBody:
    def test_parses_json_string_body(self):
        event = {'body': '{"key": "value"}'}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_returns_dict_body_unchanged(self):
        event = {'body': {'key': 'value'}}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_handles_missing_body(self):
        event = {}
        result = parse_body(event)
        assert result == {}

    def test_handles_empty_dict_body(self):
        event = {'body': {}}
        result = parse_body(event)
        assert result == {}

    def test_parses_nested_json(self):
        event = {'body': '{"nested": {"key": "value"}}'}
        result = parse_body(event)
        assert result == {'nested': {'key': 'value'}}

