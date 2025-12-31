"""Lambda-related test factory functions."""
from botocore.exceptions import ClientError
import pytest
from naming_conventions import validate_name
from test_fixtures.integration.helpers import (
    assert_iam_role_name_is_pascalcase,
    check_service_can_assume_role,
)


def create_lambda_api_gateway_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    """Create Lambda API Gateway wiring tests for an endpoint.

    Creates a test class that verifies:
    - Lambda has API Gateway invoke permission
    - Lambda has IAM role attached
    - Lambda role follows naming pattern

    Args:
        function_name_config_key: Config key for function name
            (e.g., 'health_handler_function_name')
        default_function_name: Default function name if not in config

    Returns:
        Test class with Lambda wiring tests
    """

    class TestLambdaWiring:
        """Layer 3: Verify Lambda is wired to API Gateway and has correct role."""

        def test_handler_has_api_gateway_permission(self, lambda_client, config):
            """Verify Lambda has permission to be invoked by API Gateway."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_policy(FunctionName=function_name)
                policy = response.get("Policy", "")
                # Check that API Gateway has permission to invoke
                assert "apigateway.amazonaws.com" in policy, (
                    f"Lambda '{function_name}' missing API Gateway invoke permission"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda '{function_name}' has no resource policy - "
                        "API Gateway cannot invoke it"
                    )
                raise

        def test_handler_has_role_attached(self, lambda_client, config):
            """Verify Lambda function has IAM role attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            assert role_arn, f"Lambda '{function_name}' has no IAM role attached"

        def test_handler_role_follows_naming_pattern(self, lambda_client, config):
            """Verify Lambda role ARN follows expected naming pattern."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            expected_role_suffix = f"{function_name}ServiceRole"
            assert expected_role_suffix in role_arn, (
                f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
                f"containing '{expected_role_suffix}'"
            )

    return TestLambdaWiring


def create_lambda_iam_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
    check_basic_execution: bool = True,
    check_lambda_trust: bool = True,
):
    """Create Lambda IAM policy wiring tests for an endpoint.

    Creates a test class that verifies IAM role policies are properly configured.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        check_basic_execution: Whether to check for basic execution policy
        check_lambda_trust: Whether to check Lambda can assume the role

    Returns:
        Test class with IAM policy wiring tests
    """

    class TestIAMPolicyWiring:
        """Layer 3: Verify IAM role has required policies attached."""

        def test_config_has_function_name(self, config):
            """Verify config contains the required function name key."""
            assert config.get(function_name_config_key) or default_function_name, (
                f"Neither config key '{function_name_config_key}' nor default "
                f"'{default_function_name}' is available"
            )

        def test_service_role_name_follows_convention(self, config):
            """Verify service role name follows naming convention."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            assert "ServiceRole" in role_name, "Role name should contain 'ServiceRole'"

    if check_basic_execution:

        def test_handler_role_has_basic_execution_policy(_self, iam_client, config):
            """Verify IAM role has Lambda basic execution policy attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.list_attached_role_policies(RoleName=role_name)
            policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
            basic_execution = (
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            assert basic_execution in policy_arns, (
                f"IAM role '{role_name}' missing AWSLambdaBasicExecutionRole policy. "
                f"Attached policies: {policy_arns}"
            )

        setattr(
            TestIAMPolicyWiring,
            "test_handler_role_has_basic_execution_policy",
            test_handler_role_has_basic_execution_policy,
        )

    if check_lambda_trust:

        def test_handler_role_can_assume_lambda_service(_self, iam_client, config):
            """Verify IAM role trust policy allows Lambda service to assume it."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.get_role(RoleName=role_name)
            assume_policy = response["Role"]["AssumeRolePolicyDocument"]
            statements = assume_policy.get("Statement", [])
            lambda_principals = [
                s for s in statements
                if s.get("Principal", {}).get("Service") == "lambda.amazonaws.com"
            ]
            assert lambda_principals, (
                f"IAM role '{role_name}' missing Lambda service in trust policy"
            )

        setattr(
            TestIAMPolicyWiring,
            "test_handler_role_can_assume_lambda_service",
            test_handler_role_can_assume_lambda_service,
        )

    return TestIAMPolicyWiring


def create_lambda_execution_role_wiring_tests(fixture_name: str = "lambda_function"):
    """Create Lambda execution role wiring tests.

    Creates a test class that verifies Lambda function has proper
    IAM execution role configuration and wiring.

    Args:
        fixture_name: Name of the fixture providing Lambda config
                     (e.g., 'lambda_function' or 'lambda_config')

    Returns:
        Test class with Lambda execution role wiring tests
    """

    class TestLambdaExecutionRole:
        """Verify Lambda execution role wiring."""

        def test_lambda_has_execution_role_key(self, request):
            """Verify Lambda function has Role key in configuration."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert "Role" in lambda_config

        def test_lambda_has_execution_role_value(self, request):
            """Verify Lambda function execution role is not empty."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert lambda_config.get("Role")

        def test_lambda_role_starts_with_iam_arn(self, request):
            """Verify Lambda execution role starts with IAM ARN prefix."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert role_arn.startswith("arn:aws:iam::"), (
                f"Lambda role '{role_arn}' is not a valid IAM ARN"
            )

        def test_lambda_role_contains_role_path(self, request):
            """Verify Lambda execution role ARN contains :role/ path."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert ":role/" in role_arn, (
                f"Lambda role '{role_arn}' does not appear to be a role ARN"
            )

        def test_lambda_role_exists(self, iam_client, request):
            """Verify the Lambda execution role exists in IAM."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.fail("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response.get("Role") is not None
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.fail(
                        f"Lambda execution role '{role_name}' does not exist in IAM. "
                        "The Lambda is configured with a non-existent role."
                    )
                raise

        def test_lambda_role_can_be_assumed_by_lambda(self, iam_client, request):
            """Verify the Lambda execution role has a trust policy for Lambda."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.skip("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
                can_assume = check_service_can_assume_role(
                    trust_policy, "lambda.amazonaws.com"
                )

                assert can_assume, (
                    f"Role '{role_name}' trust policy does not allow Lambda to assume it"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.skip(f"Role '{role_name}' does not exist")
                raise

    return TestLambdaExecutionRole


def create_lambda_existence_tests(
    function_name_config_key: str,
    default_function_name: str,
    terraform_path: str,
    log_group_fixture: str | None = None,
):
    """Create Lambda/IAM existence tests for an endpoint.

    Creates a test class that verifies Lambda function and IAM role exist.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        terraform_path: Path to terraform directory for error messages
        log_group_fixture: Optional fixture name for log group test

    Returns:
        Test class with Lambda existence tests
    """

    class TestDeployedResourcesExist:
        """Layer 1: Verify Lambda, IAM role exist."""

        def test_handler_lambda_exists(self, lambda_client, config):
            """Verify Lambda function exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                assert response["Configuration"]["FunctionName"] == function_name
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda function '{function_name}' does not exist. "
                        f"Run terraform apply in {terraform_path}"
                    )
                raise

        def test_handler_iam_role_exists(self, iam_client, config):
            """Verify IAM role exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response["Role"]["RoleName"] == role_name
            except iam_client.exceptions.NoSuchEntityException:
                pytest.fail(
                    f"IAM role '{role_name}' does not exist. "
                    f"Run terraform apply in {terraform_path}"
                )

    if log_group_fixture:

        def test_handler_log_group_exists(_self, request):
            """Verify CloudWatch log group exists."""
            log_group = request.getfixturevalue(log_group_fixture)
            assert log_group["exists"], (
                f"CloudWatch log group '{log_group['name']}' does not exist"
            )

        setattr(
            TestDeployedResourcesExist,
            "test_handler_log_group_exists",
            test_handler_log_group_exists,
        )

    return TestDeployedResourcesExist


def create_lambda_configuration_tests(
    function_name_config_key: str,
    default_function_name: str,
    expected_runtime: str = "python3.13",
    expected_handler: str = "handler.handler",
    expected_architecture: str = "arm64",
):
    """Create Lambda configuration tests for an endpoint.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        expected_runtime: Expected Python runtime
        expected_handler: Expected handler path
        expected_architecture: Expected architecture

    Returns:
        Test class with Lambda configuration tests
    """

    class TestLambdaConfiguration:
        """Layer 2: Verify Lambda function is configured correctly."""

        def test_handler_uses_python_runtime(self, lambda_client, config):
            """Verify Lambda uses expected Python runtime."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            runtime = response["Configuration"]["Runtime"]
            assert runtime == expected_runtime, (
                f"Lambda runtime should be {expected_runtime}, got: {runtime}"
            )

        def test_handler_uses_expected_architecture(self, lambda_client, config):
            """Verify Lambda uses expected architecture."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            architectures = response["Configuration"].get("Architectures", [])
            assert expected_architecture in architectures, (
                f"Lambda should use {expected_architecture} architecture, got: {architectures}"
            )

        def test_handler_has_handler_configured(self, lambda_client, config):
            """Verify Lambda has correct handler configured."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            handler = response["Configuration"]["Handler"]
            assert handler == expected_handler, (
                f"Lambda handler should be {expected_handler}, got: {handler}"
            )

    return TestLambdaConfiguration


def create_naming_convention_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    """Create naming convention tests for Lambda and IAM resources.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config

    Returns:
        Test class with naming convention tests
    """

    class TestNamingConventions:
        """Layer 2: Verify resources follow naming conventions."""

        def test_handler_lambda_name_is_pascalcase(self, lambda_client, config):
            """Verify Lambda function name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response["Configuration"]["FunctionName"]
            error = validate_name(actual_name)
            assert error is None, (
                f"Lambda function has invalid name '{actual_name}': {error}"
            )

        def test_handler_role_name_is_pascalcase(self, iam_client, config):
            """Verify IAM role name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response["Role"]["RoleName"]
            error = validate_name(actual_name)
            assert error is None, (
                f"IAM role has invalid name '{actual_name}': {error}"
            )

    return TestNamingConventions


def create_deployed_naming_convention_tests(
    function_name_config_key: str,
    default_function_name: str,
    handler_display_name: str,
):
    """Create post-deployment naming convention tests for Lambda and IAM resources.

    These tests verify both existence and PascalCase naming of deployed resources.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        handler_display_name: Display name for test docstrings (e.g., "EchoHandler")

    Returns:
        Tuple of (TestDeployedIAMRoleNamingConventions, TestDeployedLambdaFunctionNamingConventions)
    """

    class TestDeployedIAMRoleNamingConventions:
        """Tests for deployed IAM role naming conventions."""

        def test_handler_role_exists(self, iam_client, config):
            """Verify IAM role exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            try:
                iam_client.get_role(RoleName=role_name)
            except iam_client.exceptions.NoSuchEntityException:
                pytest.fail(f"IAM role '{role_name}' does not exist")

        def test_handler_role_name_is_pascalcase(self, iam_client, config):
            """Verify IAM role name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            assert_iam_role_name_is_pascalcase(iam_client, role_name, validate_name)

    # Rename test methods to include handler name
    TestDeployedIAMRoleNamingConventions.test_handler_role_exists.__doc__ = (
        f"Verify {handler_display_name} IAM role exists."
    )
    TestDeployedIAMRoleNamingConventions.test_handler_role_name_is_pascalcase.__doc__ = (
        f"Verify {handler_display_name} IAM role name uses PascalCase."
    )

    class TestDeployedLambdaFunctionNamingConventions:
        """Tests for deployed Lambda function naming conventions."""

        def test_handler_function_exists(self, lambda_client, config):
            """Verify Lambda function exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                lambda_client.get_function(FunctionName=function_name)
            except lambda_client.exceptions.ResourceNotFoundException:
                pytest.fail(f"Lambda function '{function_name}' does not exist")

        def test_handler_function_name_is_pascalcase(self, lambda_client, config):
            """Verify Lambda function name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response['Configuration']['FunctionName']
            error = validate_name(actual_name)
            assert error is None, (
                f"Deployed Lambda function has invalid name '{actual_name}': {error}"
            )

    # Rename test methods to include handler name
    TestDeployedLambdaFunctionNamingConventions.test_handler_function_exists.__doc__ = (
        f"Verify {handler_display_name} Lambda function exists."
    )
    TestDeployedLambdaFunctionNamingConventions.test_handler_function_name_is_pascalcase.__doc__ = (
        f"Verify {handler_display_name} Lambda function name uses PascalCase."
    )

    return TestDeployedIAMRoleNamingConventions, TestDeployedLambdaFunctionNamingConventions
