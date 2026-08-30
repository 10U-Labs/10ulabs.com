from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration.helpers import (
    check_iam_role_exists,
    check_lambda_function_exists,
    check_service_can_assume_role,
)


def _lambda_role_name(lambda_config):
    role_arn = lambda_config.get("Role", "")
    return role_arn.split("/")[-1] if "/" in role_arn else ""


def create_lambda_api_gateway_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    class TestLambdaWiring:
        def test_handler_has_api_gateway_permission(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_policy(FunctionName=function_name)
                policy = response.get("Policy", "")
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
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            assert role_arn, f"Lambda '{function_name}' has no IAM role attached"

        def test_handler_role_follows_naming_pattern(self, lambda_client, config):
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
    class TestIAMPolicyWiring:
        def test_config_has_function_name(self, config):
            assert config.get(function_name_config_key) or default_function_name, (
                f"Neither config key '{function_name_config_key}' nor default "
                f"'{default_function_name}' is available"
            )

        def test_service_role_name_follows_convention(self, config):
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            assert "ServiceRole" in role_name, "Role name should contain 'ServiceRole'"

    if check_basic_execution:

        def test_handler_role_has_basic_execution_policy(_self, iam_client, config):
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
    class TestLambdaExecutionRole:
        def test_lambda_has_execution_role_key(self, request):
            lambda_config = request.getfixturevalue(fixture_name)
            assert "Role" in lambda_config

        def test_lambda_has_execution_role_value(self, request):
            lambda_config = request.getfixturevalue(fixture_name)
            assert lambda_config.get("Role")

        def test_lambda_role_starts_with_iam_arn(self, request):
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert role_arn.startswith("arn:aws:iam::"), (
                f"Lambda role '{role_arn}' is not a valid IAM ARN"
            )

        def test_lambda_role_contains_role_path(self, request):
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert ":role/" in role_arn, (
                f"Lambda role '{role_arn}' does not appear to be a role ARN"
            )

        def test_lambda_role_exists(self, iam_client, request):
            role_name = _lambda_role_name(request.getfixturevalue(fixture_name))
            if not role_name:
                pytest.fail("Could not extract role name from Lambda configuration")

            check_iam_role_exists(iam_client, role_name, "the Lambda's deployment")

        def test_lambda_role_can_be_assumed_by_lambda(self, iam_client, request):
            role_name = _lambda_role_name(request.getfixturevalue(fixture_name))
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
    class TestDeployedResourcesExist:
        def test_handler_lambda_exists(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            check_lambda_function_exists(lambda_client, function_name, terraform_path)

        def test_handler_iam_role_exists(self, iam_client, config):
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
    expected_handler: str,
    expected_runtime: str = "python3.13",
    expected_architecture: str = "arm64",
):
    class TestLambdaConfiguration:
        def test_handler_uses_python_runtime(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            runtime = response["Configuration"]["Runtime"]
            assert runtime == expected_runtime, (
                f"Lambda runtime should be {expected_runtime}, got: {runtime}"
            )

        def test_handler_uses_expected_architecture(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            architectures = response["Configuration"].get("Architectures", [])
            assert expected_architecture in architectures, (
                f"Lambda should use {expected_architecture} architecture, got: {architectures}"
            )

        def test_handler_has_handler_configured(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            handler = response["Configuration"]["Handler"]
            assert handler == expected_handler, (
                f"Lambda handler should be {expected_handler}, got: {handler}"
            )

    return TestLambdaConfiguration


def create_deployed_resource_existence_tests(
    function_name_config_key: str,
    default_function_name: str,
    handler_display_name: str,
):
    class TestDeployedHandlerResourcesExist:
        def test_handler_role_exists(self, iam_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            try:
                iam_client.get_role(RoleName=role_name)
            except iam_client.exceptions.NoSuchEntityException:
                pytest.fail(f"IAM role '{role_name}' does not exist")

        def test_handler_function_exists(self, lambda_client, config):
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                lambda_client.get_function(FunctionName=function_name)
            except lambda_client.exceptions.ResourceNotFoundException:
                pytest.fail(f"Lambda function '{function_name}' does not exist")

    TestDeployedHandlerResourcesExist.test_handler_role_exists.__doc__ = (
        f"Verify {handler_display_name} IAM role exists."
    )
    TestDeployedHandlerResourcesExist.test_handler_function_exists.__doc__ = (
        f"Verify {handler_display_name} Lambda function exists."
    )

    return TestDeployedHandlerResourcesExist
