"""Comprehensive tests for test_utils.existence_tests module."""
from unittest.mock import MagicMock, call, patch

from test_utils.existence_tests import AwsResourceExistsTestMixin


class TestAwsResourceExistsTestMixin:
    """Tests for AwsResourceExistsTestMixin class."""

    def test_get_required_fixtures_names_the_test_arguments(self):
        """get_required_fixtures lists the fixtures the test method takes."""
        assert AwsResourceExistsTestMixin.get_required_fixtures() == [
            "function_name",
            "cfg",
        ]

    def test_lambda_function_exists_delegates_to_assert_lambda_exists(self):
        """test_lambda_function_exists passes its arguments straight through."""
        delegate = MagicMock()
        target = "test_utils.existence_tests.assert_lambda_exists"
        with patch(target, delegate):
            AwsResourceExistsTestMixin().test_lambda_function_exists(
                "some-function", {"aws_region": "eu-west-1"}
            )
        assert delegate.call_args == call(
            "some-function", {"aws_region": "eu-west-1"}
        )
