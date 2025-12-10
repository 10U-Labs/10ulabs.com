"""Integration tests to verify deployed IAM roles and Lambda functions use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions."""

    @pytest.mark.parametrize(
        "role_name",
        [
            "TenULabsCircuitBreakerRemediationRole",
            "TenULabsDLQReprocessorRole",
            "TenULabsCircuitBreakerRecoveryRole",
            "TenULabsDriftRecoveryRole",
            "TenULabsSpotInterruptionHandlerRole",
            "TenULabsStaleRunnerCleanupRole",
        ],
        ids=[
            "circuit_breaker_remediation",
            "dlq_reprocessor",
            "circuit_breaker_recovery",
            "drift_recovery",
            "spot_interruption_handler",
            "stale_runner_cleanup",
        ],
    )
    def test_iam_role_name_is_pascalcase(self, iam_client, role_name):
        """Verify IAM role name uses PascalCase."""
        try:
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response['Role']['RoleName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed IAM role has invalid name '{actual_name}': {error}"
            )
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"IAM role '{role_name}' not deployed")


class TestDeployedLambdaFunctionNamingConventions:
    """Tests for deployed Lambda function naming conventions."""

    @pytest.mark.parametrize(
        "function_name",
        [
            "TenULabs-CircuitBreakerRemediation",
            "TenULabs-DLQReprocessor",
            "TenULabs-CircuitBreakerRecovery",
            "TenULabs-DriftRecovery",
            "TenULabs-SpotInterruptionHandler",
            "TenULabs-StaleRunnerCleanup",
        ],
        ids=[
            "circuit_breaker_remediation",
            "dlq_reprocessor",
            "circuit_breaker_recovery",
            "drift_recovery",
            "spot_interruption_handler",
            "stale_runner_cleanup",
        ],
    )
    def test_lambda_function_name_is_pascalcase(self, lambda_client, function_name):
        """Verify Lambda function name uses PascalCase."""
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Lambda function '{function_name}' not deployed")
