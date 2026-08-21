"""Comprehensive tests for test_utils.aws_assertions module."""
from unittest.mock import MagicMock, patch

import pytest

from test_utils.aws_assertions import assert_lambda_exists, role_has_permission


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


def _iam_client_mock(action):
    """Build an IAM client stub whose one inline policy grants action."""
    client = MagicMock()
    client.list_role_policies.return_value = {"PolicyNames": ["inline"]}
    client.get_role_policy.return_value = {
        "PolicyDocument": {"Statement": [{"Action": action}]}
    }
    return client


class TestRoleHasPermission:
    """Tests for role_has_permission function."""

    def test_returns_true_when_a_policy_grants_the_action(self):
        """role_has_permission finds the action in a list of actions."""
        client = _iam_client_mock(["s3:GetObject", "ssm:GetParameter"])
        assert role_has_permission(client, "some-role", "ssm:GetParameter")

    def test_returns_false_when_no_policy_grants_the_action(self):
        """role_has_permission reports a role without the action."""
        client = _iam_client_mock(["s3:GetObject"])
        assert not role_has_permission(client, "some-role", "ssm:GetParameter")

    def test_returns_true_when_action_is_a_bare_string(self):
        """role_has_permission handles an Action given as a single string."""
        client = _iam_client_mock("ssm:GetParameter")
        assert role_has_permission(client, "some-role", "ssm:GetParameter")
