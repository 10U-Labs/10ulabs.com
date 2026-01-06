"""Unit tests for lambda_http module used by diagnostics handler."""
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

    def test_json_response_returns_status_code(self):
        """Verify json_response returns the specified status code."""
        response = json_response(200, {'key': 'value'})
        assert response['statusCode'] == 200

    def test_json_response_returns_content_type_header(self):
        """Verify json_response includes Content-Type header."""
        response = json_response(200, {'key': 'value'})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_json_response_returns_cors_origin_header(self):
        """Verify json_response includes CORS origin header."""
        response = json_response(200, {'key': 'value'})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_json_response_returns_cors_methods_header(self):
        """Verify json_response includes CORS methods header."""
        response = json_response(200, {'key': 'value'})
        assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,DELETE,OPTIONS'

    def test_json_response_returns_cors_headers_header(self):
        """Verify json_response includes CORS headers header."""
        response = json_response(200, {'key': 'value'})
        expected = 'Content-Type,x-api-key,x-test-mode'
        assert response['headers']['Access-Control-Allow-Headers'] == expected

    def test_json_response_body_is_json_string(self):
        """Verify json_response body is a JSON string."""
        response = json_response(200, {'key': 'value'})
        assert isinstance(response['body'], str)
        parsed = json.loads(response['body'])
        assert parsed == {'key': 'value'}


class TestSuccessResponse:
    """Tests for success_response function."""

    def test_success_response_with_success_true_returns_200(self):
        """Verify success_response returns 200 when success is True."""
        response = success_response({'success': True, 'data': 'test'})
        assert response['statusCode'] == 200

    def test_success_response_with_default_success_returns_200(self):
        """Verify success_response returns 200 when success key is missing."""
        response = success_response({'data': 'test'})
        assert response['statusCode'] == 200

    def test_success_response_with_success_false_returns_500(self):
        """Verify success_response returns 500 when success is False."""
        response = success_response({'success': False, 'error': 'Something went wrong'})
        assert response['statusCode'] == 500

    def test_success_response_includes_body(self):
        """Verify success_response includes the body data."""
        response = success_response({'data': 'test'})
        parsed = json.loads(response['body'])
        assert parsed['data'] == 'test'


class TestErrorResponse:
    """Tests for error_response function."""

    def test_error_response_returns_specified_status_code(self):
        """Verify error_response returns the specified status code."""
        response = error_response(400, 'Bad Request')
        assert response['statusCode'] == 400

    def test_error_response_body_has_success_false(self):
        """Verify error_response body has success=False."""
        response = error_response(400, 'Bad Request')
        parsed = json.loads(response['body'])
        assert parsed['success'] is False

    def test_error_response_body_has_error(self):
        """Verify error_response body has error message."""
        response = error_response(400, 'Bad Request')
        parsed = json.loads(response['body'])
        assert parsed['error'] == 'Bad Request'

    def test_error_response_without_details(self):
        """Verify error_response works without details."""
        response = error_response(400, 'Bad Request')
        parsed = json.loads(response['body'])
        assert 'details' not in parsed

    def test_error_response_with_details(self):
        """Verify error_response includes details when provided."""
        response = error_response(400, 'Bad Request', 'Missing required field')
        parsed = json.loads(response['body'])
        assert parsed['details'] == 'Missing required field'


class TestParseBody:
    """Tests for parse_body function."""

    def test_parse_body_with_string_body(self):
        """Verify parse_body parses JSON string body."""
        event = {'body': '{"key": "value"}'}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_parse_body_with_dict_body(self):
        """Verify parse_body returns dict body as-is."""
        event = {'body': {'key': 'value'}}
        result = parse_body(event)
        assert result == {'key': 'value'}

    def test_parse_body_with_empty_body(self):
        """Verify parse_body handles missing body."""
        event = {}
        result = parse_body(event)
        assert result == {}


class TestIsCapacityError:
    """Tests for is_capacity_error function."""

    def test_is_capacity_error_with_capacity_string(self):
        """Verify is_capacity_error detects capacity in string error."""
        result = {'error': 'Insufficient capacity available'}
        assert is_capacity_error(result) is True

    def test_is_capacity_error_with_availability_zone_string(self):
        """Verify is_capacity_error detects availability zone in string error."""
        result = {'error': 'No availability zone has capacity'}
        assert is_capacity_error(result) is True

    def test_is_capacity_error_with_other_string(self):
        """Verify is_capacity_error returns False for unrelated string error."""
        result = {'error': 'Network timeout'}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_list_containing_capacity(self):
        """Verify is_capacity_error detects Capacity in list of errors."""
        result = {'error': [{'reason': 'InsufficientCapacity'}]}
        assert is_capacity_error(result) is True

    def test_is_capacity_error_with_list_not_containing_capacity(self):
        """Verify is_capacity_error returns False for list without Capacity."""
        result = {'error': [{'reason': 'NetworkError'}]}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_empty_list(self):
        """Verify is_capacity_error returns False for empty error list."""
        result = {'error': []}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_no_error(self):
        """Verify is_capacity_error returns False when no error key."""
        result = {'success': True}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_non_dict_in_list(self):
        """Verify is_capacity_error handles non-dict items in list."""
        result = {'error': ['string error', {'reason': 'Capacity'}]}
        assert is_capacity_error(result) is True

    def test_is_capacity_error_with_only_non_dict_in_list(self):
        """Verify is_capacity_error returns False for list of non-dicts."""
        result = {'error': ['string error 1', 'string error 2']}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_int_error(self):
        """Verify is_capacity_error returns False for non-string, non-list error."""
        result = {'error': 42}
        assert is_capacity_error(result) is False

    def test_is_capacity_error_with_none_error(self):
        """Verify is_capacity_error returns False for None error."""
        result = {'error': None}
        assert is_capacity_error(result) is False
