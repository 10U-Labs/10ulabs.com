import json

from lambda_http import (
    json_response,
    success_response,
    error_response,
    parse_body,
    is_capacity_error,
)


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


class TestSuccessResponse:
    def test_returns_200_for_success_true(self):
        response = success_response({'success': True})
        assert response['statusCode'] == 200

    def test_returns_200_for_implicit_success(self):
        response = success_response({'data': 'value'})
        assert response['statusCode'] == 200

    def test_returns_500_for_success_false(self):
        response = success_response({'success': False})
        assert response['statusCode'] == 500

    def test_body_contains_original_data(self):
        response = success_response({'success': True, 'data': 'value'})
        body = json.loads(response['body'])
        assert body['data'] == 'value'


class TestErrorResponse:
    def test_returns_correct_status_code(self):
        response = error_response(400, 'Bad request')
        assert response['statusCode'] == 400

    def test_includes_error_message(self):
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'

    def test_sets_success_to_false(self):
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['success'] is False

    def test_includes_details_when_provided(self):
        response = error_response(400, 'Bad request', 'Missing field: name')
        body = json.loads(response['body'])
        assert body['details'] == 'Missing field: name'

    def test_excludes_details_when_not_provided(self):
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert 'details' not in body


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


class TestIsCapacityError:
    def test_detects_capacity_in_string_error(self):
        result = {'error': 'No capacity available'}
        assert is_capacity_error(result) is True

    def test_detects_capacity_case_insensitive(self):
        result = {'error': 'CAPACITY unavailable'}
        assert is_capacity_error(result) is True

    def test_detects_availability_zone_in_string(self):
        result = {'error': 'availability zone constraint violated'}
        assert is_capacity_error(result) is True

    def test_detects_capacity_in_list_error(self):
        result = {'error': [{'reason': 'InsufficientCapacity'}]}
        assert is_capacity_error(result) is True

    def test_ignores_non_dict_items_in_list(self):
        result = {'error': ['string error', {'reason': 'Capacity'}]}
        assert is_capacity_error(result) is True

    def test_returns_false_for_permission_error(self):
        result = {'error': 'Permission denied'}
        assert is_capacity_error(result) is False

    def test_returns_false_for_empty_error(self):
        result = {'error': ''}
        assert is_capacity_error(result) is False

    def test_returns_false_for_missing_error(self):
        result = {}
        assert is_capacity_error(result) is False

    def test_returns_false_for_other_list_errors(self):
        result = {'error': [{'reason': 'Unauthorized'}]}
        assert is_capacity_error(result) is False

    def test_returns_false_for_list_of_non_dicts(self):
        result = {'error': ['string error 1', 'string error 2']}
        assert is_capacity_error(result) is False

    def test_returns_false_for_empty_list(self):
        result = {'error': []}
        assert is_capacity_error(result) is False

    def test_returns_false_for_integer_error(self):
        result = {'error': 500}
        assert is_capacity_error(result) is False

    def test_returns_false_for_none_error(self):
        result = {'error': None}
        assert is_capacity_error(result) is False

    def test_returns_false_for_dict_error(self):
        result = {'error': {'code': 'SomeError'}}
        assert is_capacity_error(result) is False
