"""Unit tests for lambda_utils module."""
import json
from unittest.mock import patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture(name="lambda_utils_module")
def lambda_utils_module_fixture():
    """Load lambda_utils module for testing."""
    module = load_lambda_module("common/lambda_utils.py", "lambda_utils")
    yield module


class TestGetSqsRecords:
    """Tests for get_sqs_records function."""

    def test_returns_records_when_present(self, lambda_utils_module):
        """Test that records are returned when present."""
        event = {"Records": [{"body": "test1"}, {"body": "test2"}]}
        result = lambda_utils_module.get_sqs_records(event)
        assert result == [{"body": "test1"}, {"body": "test2"}]

    def test_returns_none_when_records_empty(self, lambda_utils_module):
        """Test that None is returned when Records is empty."""
        event = {"Records": []}
        result = lambda_utils_module.get_sqs_records(event)
        assert result is None

    def test_returns_none_when_records_missing(self, lambda_utils_module):
        """Test that None is returned when Records key is missing."""
        event = {}
        result = lambda_utils_module.get_sqs_records(event)
        assert result is None


class TestEmptyRecordsResponse:
    """Tests for empty_records_response function."""

    def test_returns_200_status_code(self, lambda_utils_module):
        """Test that 200 status code is returned."""
        result = lambda_utils_module.empty_records_response()
        assert result["statusCode"] == 200

    def test_returns_json_body(self, lambda_utils_module):
        """Test that body contains JSON message."""
        result = lambda_utils_module.empty_records_response()
        body = json.loads(result["body"])
        assert body["message"] == "No records to process"


class TestCountResults:
    """Tests for count_results function."""

    def test_counts_successful_results(self, lambda_utils_module):
        """Test counting successful results."""
        results = [{"success": True}, {"success": True}, {"success": False}]
        success, fail = lambda_utils_module.count_results(results)
        assert (success, fail) == (2, 1)

    def test_counts_failed_results(self, lambda_utils_module):
        """Test counting failed results."""
        results = [{"success": False}, {"success": False}]
        success, fail = lambda_utils_module.count_results(results)
        assert (success, fail) == (0, 2)

    def test_handles_empty_list(self, lambda_utils_module):
        """Test handling of empty results list."""
        success, fail = lambda_utils_module.count_results([])
        assert (success, fail) == (0, 0)

    def test_handles_missing_success_key(self, lambda_utils_module):
        """Test handling of results without success key (treated as failure)."""
        results = [{"other": "data"}]
        success, fail = lambda_utils_module.count_results(results)
        assert (success, fail) == (0, 1)


class TestParseErrorResponse:
    """Tests for parse_error_response function."""

    def test_returns_success_false(self, lambda_utils_module):
        """Test that success is False in error response."""
        result = lambda_utils_module.parse_error_response(ValueError("test error"))
        assert result["success"] is False

    def test_includes_error_message(self, lambda_utils_module):
        """Test that error message is included."""
        result = lambda_utils_module.parse_error_response(ValueError("test error"))
        assert "test error" in result["error"]

    def test_includes_parse_error_prefix(self, lambda_utils_module):
        """Test that error has Parse error prefix."""
        result = lambda_utils_module.parse_error_response(ValueError("test"))
        assert result["error"].startswith("Parse error:")
