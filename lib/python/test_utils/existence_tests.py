"""Shared test classes for AWS resource existence tests."""
from test_utils import assert_lambda_exists


class AwsResourceExistsTestMixin:
    """Test mixin that verifies AWS resources exist."""

    def test_lambda_function_exists(self, function_name: str, cfg):
        """Lambda function exists in AWS."""
        assert_lambda_exists(function_name, cfg)
