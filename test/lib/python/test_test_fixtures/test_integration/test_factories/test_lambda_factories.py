"""Unit tests for test_fixtures.integration.factories.lambda_factories module."""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration.factories.lambda_factories import (
    create_deployed_naming_convention_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
    create_naming_convention_tests,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


# === create_lambda_api_gateway_wiring_tests ===


class TestCreateLambdaApiGatewayWiringTestsReturnsClass:
    """Tests for create_lambda_api_gateway_wiring_tests return type."""

    def test_returns_class(self):
        """create_lambda_api_gateway_wiring_tests returns a class."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_lambda_api_gateway_wiring_tests returns class named TestLambdaWiring."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestLambdaWiring"


class TestCreateLambdaApiGatewayWiringTestsHasMethods:
    """Tests for create_lambda_api_gateway_wiring_tests class methods."""

    def test_has_test_handler_has_api_gateway_permission(self):
        """create_lambda_api_gateway_wiring_tests has test_handler_has_api_gateway_permission."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_api_gateway_permission")

    def test_has_test_handler_has_role_attached(self):
        """create_lambda_api_gateway_wiring_tests has test_handler_has_role_attached."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_role_attached")

    def test_has_test_handler_role_follows_naming_pattern(self):
        """create_lambda_api_gateway_wiring_tests has test_handler_role_follows_naming_pattern."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_role_follows_naming_pattern")


class TestCreateLambdaApiGatewayWiringTestsExecution:
    """Tests that execute create_lambda_api_gateway_wiring_tests methods."""

    def test_handler_has_api_gateway_permission_success(self):
        """test_handler_has_api_gateway_permission passes when permission exists."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_has_api_gateway_permission(mock_client, config)
        assert result is None

    def test_handler_has_api_gateway_permission_uses_default(self):
        """test_handler_has_api_gateway_permission uses default function name."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config = {}
        instance.test_handler_has_api_gateway_permission(mock_client, config)
        mock_client.get_policy.assert_called_with(FunctionName="DefaultFunc")

    def test_handler_has_api_gateway_permission_fails_when_no_permission(self):
        """test_handler_has_api_gateway_permission fails when no API Gateway permission."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {"Policy": '{"Statement":[]}'}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_fails_on_resource_not_found(self):
        """test_handler_has_api_gateway_permission fails when no resource policy."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = _create_client_error("ResourceNotFoundException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_reraises_other_errors(self):
        """test_handler_has_api_gateway_permission reraises other errors."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = _create_client_error("ServiceException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(ClientError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_role_attached_success(self):
        """test_handler_has_role_attached passes when role attached."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_has_role_attached(mock_client, config)
        assert result is None

    def test_handler_has_role_attached_fails_when_no_role(self):
        """test_handler_has_role_attached fails when no role attached."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"Role": ""}}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_role_attached(mock_client, config)

    def test_handler_role_follows_naming_pattern_success(self):
        """test_handler_role_follows_naming_pattern passes when pattern matches."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_role_follows_naming_pattern(mock_client, config)
        assert result is None

    def test_handler_role_follows_naming_pattern_fails_when_pattern_mismatch(self):
        """test_handler_role_follows_naming_pattern fails when pattern doesn't match."""
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/OtherRole"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_role_follows_naming_pattern(mock_client, config)


# === create_lambda_iam_wiring_tests ===


class TestCreateLambdaIamWiringTestsReturnsClass:
    """Tests for create_lambda_iam_wiring_tests return type."""

    def test_returns_class(self):
        """create_lambda_iam_wiring_tests returns a class."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_lambda_iam_wiring_tests returns class named TestIAMPolicyWiring."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestIAMPolicyWiring"


class TestCreateLambdaIamWiringTestsHasMethods:
    """Tests for create_lambda_iam_wiring_tests class methods."""

    def test_has_test_config_has_function_name(self):
        """create_lambda_iam_wiring_tests has test_config_has_function_name."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_config_has_function_name")

    def test_has_test_service_role_name_follows_convention(self):
        """create_lambda_iam_wiring_tests has test_service_role_name_follows_convention."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_service_role_name_follows_convention")

    def test_has_basic_execution_policy_test_when_enabled(self):
        """create_lambda_iam_wiring_tests has basic execution test when enabled."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        assert hasattr(test_class, "test_handler_role_has_basic_execution_policy")

    def test_has_lambda_trust_test_when_enabled(self):
        """create_lambda_iam_wiring_tests has lambda trust test when enabled."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=True
        )
        assert hasattr(test_class, "test_handler_role_can_assume_lambda_service")


class TestCreateLambdaIamWiringTestsExecution:
    """Tests that execute create_lambda_iam_wiring_tests methods."""

    def test_config_has_function_name_success(self):
        """test_config_has_function_name passes when config has key."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        result = instance.test_config_has_function_name(config)
        assert result is None

    def test_config_has_function_name_uses_default(self):
        """test_config_has_function_name passes with default name."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {}
        result = instance.test_config_has_function_name(config)
        assert result is None

    def test_service_role_name_follows_convention_success(self):
        """test_service_role_name_follows_convention passes when convention followed."""
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        result = instance.test_service_role_name_follows_convention(config)
        assert result is None

    def test_handler_role_has_basic_execution_policy_success(self):
        """test_handler_role_has_basic_execution_policy passes when policy attached."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{
                "PolicyArn": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            }]
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_role_has_basic_execution_policy(mock_client, config)
        assert result is None

    def test_handler_role_has_basic_execution_policy_fails_when_missing(self):
        """test_handler_role_has_basic_execution_policy fails when policy missing."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_role_has_basic_execution_policy(mock_client, config)

    def test_handler_role_can_assume_lambda_service_success(self):
        """test_handler_role_can_assume_lambda_service passes when trust exists."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {
                "AssumeRolePolicyDocument": {
                    "Statement": [{"Principal": {"Service": "lambda.amazonaws.com"}}]
                }
            }
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_role_can_assume_lambda_service(mock_client, config)
        assert result is None

    def test_handler_role_can_assume_lambda_service_fails_when_no_trust(self):
        """test_handler_role_can_assume_lambda_service fails when trust missing."""
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"AssumeRolePolicyDocument": {"Statement": []}}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_role_can_assume_lambda_service(mock_client, config)


# === create_lambda_execution_role_wiring_tests ===


class TestCreateLambdaExecutionRoleWiringTestsReturnsClass:
    """Tests for create_lambda_execution_role_wiring_tests return type."""

    def test_returns_class(self):
        """create_lambda_execution_role_wiring_tests returns a class."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_lambda_execution_role_wiring_tests returns TestLambdaExecutionRole."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert test_class.__name__ == "TestLambdaExecutionRole"


class TestCreateLambdaExecutionRoleWiringTestsHasMethods:
    """Tests for create_lambda_execution_role_wiring_tests class methods."""

    def test_has_test_lambda_has_execution_role_key(self):
        """create_lambda_execution_role_wiring_tests has test_lambda_has_execution_role_key."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_key")

    def test_has_test_lambda_has_execution_role_value(self):
        """create_lambda_execution_role_wiring_tests has test_lambda_has_execution_role_value."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_value")

    def test_has_test_lambda_role_starts_with_iam_arn(self):
        """create_lambda_execution_role_wiring_tests has test_lambda_role_starts_with_iam_arn."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_starts_with_iam_arn")

    def test_has_test_lambda_role_contains_role_path(self):
        """create_lambda_execution_role_wiring_tests has test_lambda_role_contains_role_path."""
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_contains_role_path")


class TestCreateLambdaExecutionRoleWiringTestsExecution:
    """Tests that execute create_lambda_execution_role_wiring_tests methods."""

    def test_lambda_has_execution_role_key_success(self):
        """test_lambda_has_execution_role_key passes when Role key exists."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        result = instance.test_lambda_has_execution_role_key(mock_request)
        assert result is None

    def test_lambda_has_execution_role_value_success(self):
        """test_lambda_has_execution_role_value passes when Role value exists."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        result = instance.test_lambda_has_execution_role_value(mock_request)
        assert result is None

    def test_lambda_has_execution_role_value_fails_when_empty(self):
        """test_lambda_has_execution_role_value fails when Role value empty."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": ""}
        with pytest.raises(AssertionError):
            instance.test_lambda_has_execution_role_value(mock_request)

    def test_lambda_role_starts_with_iam_arn_success(self):
        """test_lambda_role_starts_with_iam_arn passes with valid ARN."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        result = instance.test_lambda_role_starts_with_iam_arn(mock_request)
        assert result is None

    def test_lambda_role_starts_with_iam_arn_fails_when_invalid(self):
        """test_lambda_role_starts_with_iam_arn fails with invalid ARN."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-role"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_starts_with_iam_arn(mock_request)

    def test_lambda_role_contains_role_path_success(self):
        """test_lambda_role_contains_role_path passes when :role/ present."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        result = instance.test_lambda_role_contains_role_path(mock_request)
        assert result is None

    def test_lambda_role_contains_role_path_fails_when_missing(self):
        """test_lambda_role_contains_role_path fails when :role/ missing."""
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:user/MyUser"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_contains_role_path(mock_request)


# === create_lambda_existence_tests ===


class TestCreateLambdaExistenceTestsReturnsClass:
    """Tests for create_lambda_existence_tests return type."""

    def test_returns_class(self):
        """create_lambda_existence_tests returns a class."""
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_lambda_existence_tests returns TestDeployedResourcesExist."""
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert test_class.__name__ == "TestDeployedResourcesExist"


class TestCreateLambdaExistenceTestsHasMethods:
    """Tests for create_lambda_existence_tests class methods."""

    def test_has_test_handler_lambda_exists(self):
        """create_lambda_existence_tests has test_handler_lambda_exists."""
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_lambda_exists")

    def test_has_test_handler_iam_role_exists(self):
        """create_lambda_existence_tests has test_handler_iam_role_exists."""
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_iam_role_exists")

    def test_has_log_group_test_when_fixture_provided(self):
        """create_lambda_existence_tests has log group test when fixture provided."""
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        assert hasattr(test_class, "test_handler_log_group_exists")


class TestCreateLambdaExistenceTestsExecution:
    """Tests that execute create_lambda_existence_tests methods."""

    def test_handler_iam_role_exists_success(self):
        """test_handler_iam_role_exists passes when role exists."""
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyFunctionServiceRole"}}
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_iam_role_exists(mock_client, config)
        assert result is None

    def test_handler_log_group_exists_success(self):
        """test_handler_log_group_exists passes when log group exists."""
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "exists": True, "name": "/aws/lambda/MyFunction"
        }
        result = instance.test_handler_log_group_exists(mock_request)
        assert result is None

    def test_handler_log_group_exists_fails_when_not_exists(self):
        """test_handler_log_group_exists fails when log group doesn't exist."""
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "exists": False, "name": "/aws/lambda/MyFunction"
        }
        with pytest.raises(AssertionError):
            instance.test_handler_log_group_exists(mock_request)


# === create_lambda_configuration_tests ===


class TestCreateLambdaConfigurationTestsReturnsClass:
    """Tests for create_lambda_configuration_tests return type."""

    def test_returns_class(self):
        """create_lambda_configuration_tests returns a class."""
        test_class = create_lambda_configuration_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_lambda_configuration_tests returns TestLambdaConfiguration."""
        test_class = create_lambda_configuration_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestLambdaConfiguration"


class TestCreateLambdaConfigurationTestsHasMethods:
    """Tests for create_lambda_configuration_tests class methods."""

    def test_has_test_handler_uses_python_runtime(self):
        """create_lambda_configuration_tests has test_handler_uses_python_runtime."""
        test_class = create_lambda_configuration_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_uses_python_runtime")

    def test_has_test_handler_uses_expected_architecture(self):
        """create_lambda_configuration_tests has test_handler_uses_expected_architecture."""
        test_class = create_lambda_configuration_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_uses_expected_architecture")

    def test_has_test_handler_has_handler_configured(self):
        """create_lambda_configuration_tests has test_handler_has_handler_configured."""
        test_class = create_lambda_configuration_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_handler_configured")


class TestCreateLambdaConfigurationTestsExecution:
    """Tests that execute create_lambda_configuration_tests methods."""

    def test_handler_uses_python_runtime_success(self):
        """test_handler_uses_python_runtime passes when runtime matches."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_runtime="python3.13"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Runtime": "python3.13"}
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_uses_python_runtime(mock_client, config)
        assert result is None

    def test_handler_uses_python_runtime_fails_when_different(self):
        """test_handler_uses_python_runtime fails when runtime differs."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_runtime="python3.13"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Runtime": "python3.11"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_uses_python_runtime(mock_client, config)

    def test_handler_uses_expected_architecture_success(self):
        """test_handler_uses_expected_architecture passes when arch matches."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_architecture="arm64"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Architectures": ["arm64"]}
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_uses_expected_architecture(mock_client, config)
        assert result is None

    def test_handler_uses_expected_architecture_fails_when_different(self):
        """test_handler_uses_expected_architecture fails when arch differs."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_architecture="arm64"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Architectures": ["x86_64"]}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_uses_expected_architecture(mock_client, config)

    def test_handler_has_handler_configured_success(self):
        """test_handler_has_handler_configured passes when handler matches."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.handler"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Handler": "handler.handler"}
        }
        config = {"func_key": "MyFunction"}
        result = instance.test_handler_has_handler_configured(mock_client, config)
        assert result is None

    def test_handler_has_handler_configured_fails_when_different(self):
        """test_handler_has_handler_configured fails when handler differs."""
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.handler"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Handler": "main.handler"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_handler_configured(mock_client, config)


# === create_naming_convention_tests ===


class TestCreateNamingConventionTestsReturnsClass:
    """Tests for create_naming_convention_tests return type."""

    def test_returns_class(self):
        """create_naming_convention_tests returns a class."""
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_naming_convention_tests returns TestNamingConventions."""
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestNamingConventions"


class TestCreateNamingConventionTestsHasMethods:
    """Tests for create_naming_convention_tests class methods."""

    def test_has_test_handler_lambda_name_is_pascalcase(self):
        """create_naming_convention_tests has test_handler_lambda_name_is_pascalcase."""
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_lambda_name_is_pascalcase")

    def test_has_test_handler_role_name_is_pascalcase(self):
        """create_naming_convention_tests has test_handler_role_name_is_pascalcase."""
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_role_name_is_pascalcase")


# === create_deployed_naming_convention_tests ===


class TestCreateDeployedNamingConventionTestsReturnsTuple:
    """Tests for create_deployed_naming_convention_tests return type."""

    def test_returns_tuple(self):
        """create_deployed_naming_convention_tests returns a tuple."""
        result = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert isinstance(result, tuple)

    def test_returns_tuple_of_two(self):
        """create_deployed_naming_convention_tests returns tuple of two classes."""
        result = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert len(result) == 2

    def test_first_is_iam_class(self):
        """create_deployed_naming_convention_tests first element is IAM class."""
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert iam_class.__name__ == "TestDeployedIAMRoleNamingConventions"

    def test_second_is_lambda_class(self):
        """create_deployed_naming_convention_tests second element is Lambda class."""
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert lambda_class.__name__ == "TestDeployedLambdaFunctionNamingConventions"


class TestCreateDeployedNamingConventionTestsHasMethods:
    """Tests for create_deployed_naming_convention_tests class methods."""

    def test_iam_class_has_test_handler_role_exists(self):
        """IAM class has test_handler_role_exists."""
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(iam_class, "test_handler_role_exists")

    def test_iam_class_has_test_handler_role_name_is_pascalcase(self):
        """IAM class has test_handler_role_name_is_pascalcase."""
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(iam_class, "test_handler_role_name_is_pascalcase")

    def test_lambda_class_has_test_handler_function_exists(self):
        """Lambda class has test_handler_function_exists."""
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(lambda_class, "test_handler_function_exists")

    def test_lambda_class_has_test_handler_function_name_is_pascalcase(self):
        """Lambda class has test_handler_function_name_is_pascalcase."""
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(lambda_class, "test_handler_function_name_is_pascalcase")
