"""Layer 2: Configuration tests for contact endpoint post-deployment.

Tests that resources have correct settings. Assumes existence tests passed.
These tests verify that resources created by THIS workflow are configured correctly.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""

import pytest
from test_fixtures.integration import create_naming_convention_tests


pytestmark = pytest.mark.layer(2)


class TestLambdaConfiguration:
    """Layer 2: Verify Lambda function is configured correctly."""

    def test_contact_handler_uses_python_runtime(
        self, lambda_client, shared_config
    ):
        """Verify Lambda uses Python 3.13 runtime."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        runtime = response["Configuration"]["Runtime"]
        assert runtime == "python3.13", (
            f"Lambda runtime should be python3.13, got: {runtime}"
        )

    def test_contact_handler_uses_arm64_architecture(
        self, lambda_client, shared_config
    ):
        """Verify Lambda uses ARM64 architecture."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        architectures = response["Configuration"].get("Architectures", [])
        assert "arm64" in architectures, (
            f"Lambda should use arm64 architecture, got: {architectures}"
        )

    def test_contact_handler_has_handler_configured(
        self, lambda_client, shared_config
    ):
        """Verify Lambda has correct handler configured."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        handler = response["Configuration"]["Handler"]
        assert handler == "handler.handler", (
            f"Lambda handler should be handler.handler, got: {handler}"
        )

    def test_contact_handler_has_10_second_timeout(
        self, lambda_client, shared_config
    ):
        """Verify Lambda has 10 second timeout."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        timeout = response["Configuration"]["Timeout"]
        assert timeout == 10, (
            f"Lambda timeout should be 10 seconds, got: {timeout}"
        )

    def test_contact_handler_has_contact_email_env_var(
        self, contact_handler_env_vars
    ):
        """Verify Lambda has CONTACT_EMAIL environment variable."""
        assert "CONTACT_EMAIL" in contact_handler_env_vars, (
            "Lambda missing CONTACT_EMAIL environment variable"
        )

    def test_contact_handler_has_recaptcha_param_env_var(
        self, contact_handler_env_vars
    ):
        """Verify Lambda has RECAPTCHA_SECRET_PARAMETER_NAME environment variable."""
        assert "RECAPTCHA_SECRET_PARAMETER_NAME" in contact_handler_env_vars, (
            "Lambda missing RECAPTCHA_SECRET_PARAMETER_NAME environment variable"
        )


class TestCloudWatchLogsConfiguration:
    """Layer 2: Verify CloudWatch log group is configured correctly."""

    def test_contact_handler_log_group_has_retention_set(
        self, contact_handler_log_group
    ):
        """Verify log group has retention period set."""
        assert contact_handler_log_group["retention"] is not None, (
            f"Log group '{contact_handler_log_group['name']}' "
            "should have retention set"
        )

    def test_contact_handler_log_group_retention_is_7_days(
        self, contact_handler_log_group
    ):
        """Verify log group retention is 7 days."""
        retention = contact_handler_log_group["retention"]
        assert retention == 7, (
            f"Log group retention should be 7 days, got: {retention}"
        )


# Use factory for naming convention tests
TestNamingConventions = create_naming_convention_tests(
    function_name_config_key="contact_handler_function_name",
    default_function_name="TenULabsContactHandler",
)
