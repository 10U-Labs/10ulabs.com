"""Unit tests for lambda_http response utilities."""
import json

from lambda_http import (
    json_response,
    success_response,
    error_response,
    parse_body,
    is_capacity_error,
)


class TestJsonResponse:
    """Tests for json_response function."""

    def test_returns_correct_status_code(self):
        """Test response has correct status code."""
        response = json_response(200, {'key': 'value'})
        assert response['statusCode'] == 200

    def test_returns_404_status_code(self):
        """Test response has 404 status code."""
        response = json_response(404, {'error': 'not found'})
        assert response['statusCode'] == 404

    def test_returns_json_content_type(self):
        """Test response has JSON content type header."""
        response = json_response(200, {})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_returns_cors_allow_origin(self):
        """Test response has CORS allow origin header."""
        response = json_response(200, {})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_returns_cors_allow_methods(self):
        """Test response has CORS allow methods header."""
        response = json_response(200, {})
        assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,DELETE,OPTIONS'

    def test_returns_cors_allow_headers(self):
        """Test response has CORS allow headers header."""
        response = json_response(200, {})
        assert 'x-api-key' in response['headers']['Access-Control-Allow-Headers']

    def test_serializes_body_as_json(self):
        """Test body is serialized as JSON."""
        response = json_response(200, {'key': 'value'})
        assert json.loads(response['body']) == {'key': 'value'}

    def test_serializes_empty_body(self):
        """Test empty body is serialized correctly."""
        response = json_response(200, {})
        assert json.loads(response['body']) == {}

    def test_serializes_nested_body(self):
        """Test nested body is serialized correctly."""
        response = json_response(200, {'nested': {'key': 'value'}})
        assert json.loads(response['body']) == {'nested': {'key': 'value'}}


class TestSuccessResponse:
    """Tests for success_response function."""

    def test_returns_200_for_success_true(self):
        """Test returns 200 when success is True."""
        response = success_response({'success': True})
        assert response['statusCode'] == 200

    def test_returns_200_for_implicit_success(self):
        """Test returns 200 when success key is missing."""
        response = success_response({'data': 'value'})
        assert response['statusCode'] == 200

    def test_returns_500_for_success_false(self):
        """Test returns 500 when success is False."""
        response = success_response({'success': False})
        assert response['statusCode'] == 500

    def test_body_contains_original_data(self):
        """Test body contains original data."""
        response = success_response({'success': True, 'data': 'value'})
        body = json.loads(response['body'])
        assert body['data'] == 'value'


class TestErrorResponse:
    """Tests for error_response function."""

    def test_returns_correct_status_code(self):
        """Test returns correct status code."""
        response = error_response(400, 'Bad request')
        assert response['statusCode'] == 400

    def test_includes_error_message(self):
        """Test body includes error message."""
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'

    def test_sets_success_to_false(self):
        """Test body sets success to False."""
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['success'] is False

    def test_includes_details_when_provided(self):
        """Test body includes details when provided."""
        response = error_response(400, 'Bad request', 'Missing field: name')
        body = json.loads(response['body'])
        assert body['details'] == 'Missing field: name'

    def test_excludes_details_when_not_provided(self):
        """Test body excludes details when not provided."""
        response = error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert 'details' not in body


class TestParseBody:
    """Tests for parse_body function."""

    def test_parses_json_string_body(self):
        """Test parses JSON string body."""
        event = {'body': '{"key": "value"}'}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_returns_dict_body_unchanged(self):
        """Test returns dict body unchanged."""
        event = {'body': {'key': 'value'}}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_handles_missing_body(self):
        """Test handles missing body key."""
        event = {}
        result = parse_body(event)
        assert result == {}

    def test_handles_empty_dict_body(self):
        """Test handles empty dict body."""
        event = {'body': {}}
        result = parse_body(event)
        assert result == {}

    def test_parses_nested_json(self):
        """Test parses nested JSON correctly."""
        event = {'body': '{"nested": {"key": "value"}}'}
        result = parse_body(event)
        assert result == {'nested': {'key': 'value'}}


class TestIsCapacityError:
    """Tests for is_capacity_error function."""

    def test_detects_capacity_in_string_error(self):
        """Test detects capacity in string error."""
        result = {'error': 'No capacity available'}
        assert is_capacity_error(result) is True

    def test_detects_capacity_case_insensitive(self):
        """Test detects CAPACITY case insensitive."""
        result = {'error': 'CAPACITY unavailable'}
        assert is_capacity_error(result) is True

    def test_detects_availability_zone_in_string(self):
        """Test detects availability zone in string error."""
        result = {'error': 'availability zone constraint violated'}
        assert is_capacity_error(result) is True

    def test_detects_capacity_in_list_error(self):
        """Test detects Capacity in list of error dicts."""
        result = {'error': [{'reason': 'InsufficientCapacity'}]}
        assert is_capacity_error(result) is True

    def test_returns_false_for_permission_error(self):
        """Test returns False for permission error."""
        result = {'error': 'Permission denied'}
        assert is_capacity_error(result) is False

    def test_returns_false_for_empty_error(self):
        """Test returns False for empty error."""
        result = {'error': ''}
        assert is_capacity_error(result) is False

    def test_returns_false_for_missing_error(self):
        """Test returns False for missing error key."""
        result = {}
        assert is_capacity_error(result) is False

    def test_returns_false_for_other_list_errors(self):
        """Test returns False for list without Capacity."""
        result = {'error': [{'reason': 'Unauthorized'}]}
        assert is_capacity_error(result) is False

    def test_returns_false_for_integer_error(self):
        """Test returns False when error is an integer."""
        result = {'error': 500}
        assert is_capacity_error(result) is False

    def test_returns_false_for_none_error(self):
        """Test returns False when error is None."""
        result = {'error': None}
        assert is_capacity_error(result) is False

    def test_returns_false_for_dict_error(self):
        """Test returns False when error is a dict (not a list)."""
        result = {'error': {'code': 'SomeError'}}
        assert is_capacity_error(result) is False
