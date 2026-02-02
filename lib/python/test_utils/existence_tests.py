"""Shared test classes for AWS resource existence tests."""
from test_utils import assert_lambda_exists


class AwsResourceExistsTestMixin:
    """Test mixin that verifies AWS resources exist.

    Provides a single test method to verify the Lambda function exists.
    Subclasses can add additional resource existence tests as needed.
    """

    def test_lambda_function_exists(self, function_name: str, cfg):
        """Lambda function exists in AWS."""
        assert_lambda_exists(function_name, cfg)

    @staticmethod
    def get_required_fixtures():
        """Return list of fixtures required by this mixin.

        Returns:
            List of fixture names required for existence tests.
        """
        return ["function_name", "cfg"]
