"""Tests for handler utility functions."""
import json
import sys
from unittest.mock import MagicMock

handler = sys.modules['handler']


class TestTestMode:
    """Tests for test mode functions."""

    def test_is_test_mode_returns_false_by_default(self):
        """Test that test mode is disabled by default."""
        assert handler.is_test_mode() is False

    def test_set_test_mode_enables_test_mode(self):
        """Test that set_test_mode can enable test mode."""
        handler.set_test_mode(True)
        assert handler.is_test_mode() is True

    def test_set_test_mode_disables_test_mode(self):
        """Test that set_test_mode can disable test mode."""
        handler.set_test_mode(True)
        handler.set_test_mode(False)
        assert handler.is_test_mode() is False


class TestGetHeaderCaseInsensitive:
    """Tests for case-insensitive header retrieval."""

    def test_returns_empty_string_for_none_headers(self):
        """Test that None headers return empty string."""
        assert handler.get_header_case_insensitive(None, 'test') == ''

    def test_returns_empty_string_for_empty_headers(self):
        """Test that empty headers return empty string."""
        assert handler.get_header_case_insensitive({}, 'test') == ''

    def test_returns_value_for_exact_match(self):
        """Test that exact case match returns value."""
        headers = {'Content-Type': 'application/json'}
        assert handler.get_header_case_insensitive(headers, 'Content-Type') == 'application/json'

    def test_returns_value_for_lowercase_match(self):
        """Test that lowercase match returns value."""
        headers = {'Content-Type': 'application/json'}
        assert handler.get_header_case_insensitive(headers, 'content-type') == 'application/json'

    def test_returns_value_for_uppercase_match(self):
        """Test that uppercase match returns value."""
        headers = {'content-type': 'application/json'}
        assert handler.get_header_case_insensitive(headers, 'CONTENT-TYPE') == 'application/json'

    def test_returns_empty_string_for_missing_header(self):
        """Test that missing header returns empty string."""
        headers = {'Content-Type': 'application/json'}
        assert handler.get_header_case_insensitive(headers, 'Authorization') == ''

    def test_returns_empty_string_for_none_value(self):
        """Test that None value returns empty string."""
        headers = {'Content-Type': None}
        assert handler.get_header_case_insensitive(headers, 'Content-Type') == ''


class TestGetEcrClient:
    """Tests for ECR client retrieval."""

    def test_returns_injected_client(self):
        """Test that injected client is returned."""
        mock_client = MagicMock()
        handler.set_client('ecr', mock_client)
        assert handler.get_ecr_client() == mock_client

    def test_returns_same_client_on_multiple_calls(self):
        """Test that same client is returned on multiple calls."""
        mock_client = MagicMock()
        handler.set_client('ecr', mock_client)
        first = handler.get_ecr_client()
        second = handler.get_ecr_client()
        assert first is second


class TestSetClient:
    """Tests for set_client function."""

    def test_sets_client_in_cache(self):
        """Test that client is set in cache."""
        mock_client = MagicMock()
        handler.set_client('ecr', mock_client)
        assert handler.get_ecr_client() == mock_client

    def test_overwrites_existing_client(self):
        """Test that existing client is overwritten."""
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        handler.set_client('ecr', mock_client1)
        handler.set_client('ecr', mock_client2)
        assert handler.get_ecr_client() == mock_client2


class TestJsonResponse:
    """Tests for JSON response builder."""

    def test_returns_correct_status_code(self):
        """Test that status code is set correctly."""
        response = handler.json_response(200, {'key': 'value'})
        assert response['statusCode'] == 200

    def test_includes_cors_allow_origin_header(self):
        """Test that CORS Allow-Origin header is included."""
        response = handler.json_response(200, {})
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_includes_get_in_allowed_methods(self):
        """Test that GET is in allowed methods."""
        response = handler.json_response(200, {})
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']

    def test_includes_post_in_allowed_methods(self):
        """Test that POST is in allowed methods."""
        response = handler.json_response(200, {})
        assert 'POST' in response['headers']['Access-Control-Allow-Methods']

    def test_includes_delete_in_allowed_methods(self):
        """Test that DELETE is in allowed methods."""
        response = handler.json_response(200, {})
        assert 'DELETE' in response['headers']['Access-Control-Allow-Methods']

    def test_includes_content_type_header(self):
        """Test that Content-Type header is set."""
        response = handler.json_response(200, {})
        assert response['headers']['Content-Type'] == 'application/json'

    def test_body_is_json_string(self):
        """Test that body is a JSON string."""
        response = handler.json_response(200, {'key': 'value'})
        assert response['body'] == '{"key": "value"}'

    def test_includes_x_test_mode_in_allowed_headers(self):
        """Test that x-test-mode is in allowed headers."""
        response = handler.json_response(200, {})
        assert 'x-test-mode' in response['headers']['Access-Control-Allow-Headers']


class TestSuccessResponse:
    """Tests for success response builder."""

    def test_returns_200_for_success_true(self):
        """Test that 200 is returned when success is True."""
        response = handler.success_response({'success': True, 'data': 'test'})
        assert response['statusCode'] == 200

    def test_returns_200_when_success_not_present(self):
        """Test that 200 is returned when success key is missing."""
        response = handler.success_response({'data': 'test'})
        assert response['statusCode'] == 200

    def test_returns_500_for_success_false(self):
        """Test that 500 is returned when success is False."""
        response = handler.success_response({'success': False, 'error': 'test'})
        assert response['statusCode'] == 500


class TestErrorResponse:
    """Tests for error response builder."""

    def test_returns_correct_status_code(self):
        """Test that status code is set correctly."""
        response = handler.error_response(400, 'Bad request')
        assert response['statusCode'] == 400

    def test_includes_success_false_in_body(self):
        """Test that body includes success: false."""
        response = handler.error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['success'] is False

    def test_includes_error_message(self):
        """Test that error message is included."""
        response = handler.error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'

    def test_includes_details_when_provided(self):
        """Test that details are included when provided."""
        response = handler.error_response(400, 'Bad request', 'Extra info')
        body = json.loads(response['body'])
        assert body['details'] == 'Extra info'

    def test_excludes_details_when_not_provided(self):
        """Test that details key is excluded when not provided."""
        response = handler.error_response(400, 'Bad request')
        body = json.loads(response['body'])
        assert 'details' not in body


class TestParseBody:
    """Tests for request body parser."""

    def test_parses_json_string_body(self):
        """Test that JSON string body is parsed."""
        event = {'body': '{"key": "value"}'}
        result = handler.parse_body(event)
        assert result == {'key': 'value'}

    def test_returns_dict_body_as_is(self):
        """Test that dict body is returned as-is."""
        event = {'body': {'key': 'value'}}
        result = handler.parse_body(event)
        assert result == {'key': 'value'}

    def test_returns_empty_dict_for_missing_body(self):
        """Test that empty dict is returned when body is missing."""
        event = {}
        result = handler.parse_body(event)
        assert result == {}

    def test_returns_empty_dict_for_empty_body(self):
        """Test that empty dict body is returned as-is."""
        event = {'body': {}}
        result = handler.parse_body(event)
        assert result == {}
