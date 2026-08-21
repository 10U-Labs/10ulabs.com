"""Comprehensive tests for test_utils.aws_assertions module."""
from unittest.mock import MagicMock, patch

import pytest

from test_utils.aws_assertions import assert_lambda_exists


CONFIG = {'aws_region': 'us-east-1'}
FUNCTION_NAME = 'test-function'


class LambdaNotFound(Exception):
    """Stand-in for the Lambda client's ResourceNotFoundException."""


def _lambda_client_mock():
    """Build a Lambda client mock carrying the exception the helper catches."""
    client = MagicMock()
    client.exceptions.ResourceNotFoundException = LambdaNotFound
    return client


class TestAssertLambdaExists:
    """Tests for assert_lambda_exists function."""

    def test_raises_assertion_error_when_function_is_absent(self):
        """assert_lambda_exists raises AssertionError on a missing function."""
        client = _lambda_client_mock()
        client.get_function.side_effect = LambdaNotFound()
        with patch('boto3.client', return_value=client):
            with pytest.raises(AssertionError):
                assert_lambda_exists(FUNCTION_NAME, CONFIG)

    def test_returns_none_when_deployed_name_matches(self):
        """assert_lambda_exists returns None when the deployed name matches."""
        client = _lambda_client_mock()
        client.get_function.return_value = {
            'Configuration': {'FunctionName': FUNCTION_NAME}
        }
        with patch('boto3.client', return_value=client):
            assert assert_lambda_exists(FUNCTION_NAME, CONFIG) is None
