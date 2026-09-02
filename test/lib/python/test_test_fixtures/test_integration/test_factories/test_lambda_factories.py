import inspect
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.factories.lambda_factories import (
    create_deployed_resource_existence_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
)
from test_fixtures.outcomes import accepted


class TestCreateLambdaApiGatewayWiringTestsReturnsClass:
    def test_returns_class(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestLambdaWiring"


class TestCreateLambdaApiGatewayWiringTestsHasMethods:
    def test_has_test_handler_has_api_gateway_permission(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_api_gateway_permission")

    def test_has_test_handler_has_role_attached(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_role_attached")

    def test_has_test_handler_role_follows_naming_pattern(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_role_follows_naming_pattern")


class TestCreateLambdaApiGatewayWiringTestsExecution:
    def test_handler_has_api_gateway_permission_success(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_has_api_gateway_permission(mock_client, config)
        assert mock_client.get_policy.called

    def test_handler_has_api_gateway_permission_uses_default(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config: Dict[str, Any] = {}
        instance.test_handler_has_api_gateway_permission(mock_client, config)
        assert mock_client.get_policy.call_args[1]["FunctionName"] == "DefaultFunc"

    def test_handler_has_api_gateway_permission_fails_when_no_permission(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {"Policy": '{"Statement":[]}'}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_fails_on_resource_not_found(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = create_client_error("ResourceNotFoundException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_reraises_other_errors(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = create_client_error("ServiceException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(ClientError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_role_attached_success(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_has_role_attached(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_has_role_attached_fails_when_no_role(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"Role": ""}}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_role_attached(mock_client, config)

    def test_handler_role_follows_naming_pattern_success(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_role_follows_naming_pattern(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_role_follows_naming_pattern_fails_when_pattern_mismatch(self) -> None:
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/OtherRole"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_role_follows_naming_pattern(mock_client, config)


class TestCreateLambdaIamWiringTestsReturnsClass:
    def test_returns_class(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestIAMPolicyWiring"


class TestCreateLambdaIamWiringTestsHasMethods:
    def test_has_test_config_has_function_name(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_config_has_function_name")

    def test_has_test_service_role_name_follows_convention(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_service_role_name_follows_convention")

    def test_has_basic_execution_policy_test_when_enabled(self) -> None:
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        assert hasattr(test_class, "test_handler_role_has_basic_execution_policy")

    def test_has_lambda_trust_test_when_enabled(self) -> None:
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=True
        )
        assert hasattr(test_class, "test_handler_role_can_assume_lambda_service")

    def test_no_basic_execution_test_when_disabled(self) -> None:
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=False
        )
        assert not hasattr(test_class, "test_handler_role_has_basic_execution_policy")

    def test_no_lambda_trust_test_when_disabled(self) -> None:
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=False
        )
        assert not hasattr(test_class, "test_handler_role_can_assume_lambda_service")


class TestCreateLambdaIamWiringTestsExecution:
    def test_config_has_function_name_success(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        assert accepted(instance.test_config_has_function_name, config)

    def test_config_has_function_name_uses_default(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config: Dict[str, Any] = {}
        assert accepted(instance.test_config_has_function_name, config)

    def test_service_role_name_follows_convention_success(self) -> None:
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        assert accepted(instance.test_service_role_name_follows_convention, config)

    def test_handler_role_has_basic_execution_policy_success(self) -> None:
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
        assert getattr(
            instance, "test_handler_role_has_basic_execution_policy"
        )(mock_client, config) is None

    def test_handler_role_has_basic_execution_policy_fails_when_missing(self) -> None:
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            getattr(instance, "test_handler_role_has_basic_execution_policy")(mock_client, config)

    def test_handler_role_can_assume_lambda_service_success(self) -> None:
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
        assert getattr(
            instance, "test_handler_role_can_assume_lambda_service"
        )(mock_client, config) is None

    def test_handler_role_can_assume_lambda_service_fails_when_no_trust(self) -> None:
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
            getattr(instance, "test_handler_role_can_assume_lambda_service")(mock_client, config)


class TestCreateLambdaExecutionRoleWiringTestsReturnsClass:
    def test_returns_class(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert test_class.__name__ == "TestLambdaExecutionRole"


class TestCreateLambdaExecutionRoleWiringTestsHasMethods:
    def test_has_test_lambda_has_execution_role_key(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_key")

    def test_has_test_lambda_has_execution_role_value(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_value")

    def test_has_test_lambda_role_starts_with_iam_arn(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_starts_with_iam_arn")

    def test_has_test_lambda_role_contains_role_path(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_contains_role_path")


class TestCreateLambdaExecutionRoleWiringTestsExecution:
    def test_lambda_has_execution_role_key_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_has_execution_role_key(mock_request)
        assert mock_request.getfixturevalue.called

    def test_lambda_has_execution_role_value_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_has_execution_role_value(mock_request)
        assert mock_request.getfixturevalue.called

    def test_lambda_has_execution_role_value_fails_when_empty(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": ""}
        with pytest.raises(AssertionError):
            instance.test_lambda_has_execution_role_value(mock_request)

    def test_lambda_role_starts_with_iam_arn_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_role_starts_with_iam_arn(mock_request)
        assert mock_request.getfixturevalue.called

    def test_lambda_role_starts_with_iam_arn_fails_when_invalid(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-role"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_starts_with_iam_arn(mock_request)

    def test_lambda_role_contains_role_path_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_role_contains_role_path(mock_request)
        assert mock_request.getfixturevalue.called

    def test_lambda_role_contains_role_path_fails_when_missing(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:user/MyUser"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_contains_role_path(mock_request)

    def test_lambda_role_exists_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_role_exists(mock_client, mock_request)
        assert mock_client.get_role.called

    def test_lambda_role_exists_fails_when_no_role_name_extracted(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-no-slash"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_lambda_role_exists(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_success(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {
                "AssumeRolePolicyDocument": {
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"}
                    }]
                }
            }
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)
        assert mock_client.get_role.called

    def test_lambda_role_can_be_assumed_by_lambda_skips_when_no_role_name(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-no-slash"}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_fails_when_no_trust(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {
                "AssumeRolePolicyDocument": {
                    "Statement": [{"Principal": {"Service": "ec2.amazonaws.com"}}]
                }
            }
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_skips_on_no_such_entity(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_reraises_other_errors(self) -> None:
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        with pytest.raises(ClientError):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)


class TestCreateLambdaExistenceTestsReturnsClass:
    def test_returns_class(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert test_class.__name__ == "TestDeployedResourcesExist"


class TestCreateLambdaExistenceTestsHasMethods:
    def test_has_test_handler_lambda_exists(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_lambda_exists")

    def test_has_test_handler_iam_role_exists(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_iam_role_exists")

    def test_has_log_group_test_when_fixture_provided(self) -> None:
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        assert hasattr(test_class, "test_handler_log_group_exists")


class TestCreateLambdaExistenceTestsExecution:
    def test_handler_iam_role_exists_success(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyFunctionServiceRole"}}
        config = {"func_key": "MyFunction"}
        instance.test_handler_iam_role_exists(mock_client, config)
        assert mock_client.get_role.called

    def test_handler_log_group_exists_success(self) -> None:
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "exists": True, "name": "/aws/lambda/MyFunction"
        }
        assert getattr(instance, "test_handler_log_group_exists")(mock_request) is None

    def test_handler_log_group_exists_fails_when_not_exists(self) -> None:
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "exists": False, "name": "/aws/lambda/MyFunction"
        }
        with pytest.raises(AssertionError):
            getattr(instance, "test_handler_log_group_exists")(mock_request)

    def test_handler_lambda_exists_success(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"FunctionName": "MyFunction"}}
        config = {"func_key": "MyFunction"}
        instance.test_handler_lambda_exists(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_iam_role_exists_fails_when_no_such_entity(self) -> None:
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        NoSuchEntityException = type("NoSuchEntityException", (Exception,), {})
        mock_client.exceptions.NoSuchEntityException = NoSuchEntityException
        mock_client.get_role.side_effect = NoSuchEntityException("Role not found")
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_iam_role_exists(mock_client, config)


class TestCreateLambdaConfigurationTestsDemandsHandler:
    def test_expected_handler_has_no_default(self) -> None:
        parameters = inspect.signature(create_lambda_configuration_tests).parameters
        assert parameters["expected_handler"].default is inspect.Parameter.empty

    def test_other_configuration_arguments_keep_their_defaults(self) -> None:
        parameters = inspect.signature(create_lambda_configuration_tests).parameters
        assert all(
            parameters[name].default is not inspect.Parameter.empty
            for name in ("expected_runtime", "expected_architecture")
        )


class TestCreateLambdaConfigurationTestsReturnsClass:
    def test_returns_class(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert test_class.__name__ == "TestLambdaConfiguration"


class TestCreateLambdaConfigurationTestsHasMethods:
    def test_has_test_handler_uses_python_runtime(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_uses_python_runtime")

    def test_has_test_handler_uses_expected_architecture(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_uses_expected_architecture")

    def test_has_test_handler_has_handler_configured(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_has_handler_configured")


class TestCreateLambdaConfigurationTestsExecution:
    def test_handler_uses_python_runtime_success(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_runtime="python3.13"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Runtime": "python3.13"}
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_uses_python_runtime(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_uses_python_runtime_fails_when_different(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_runtime="python3.13"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Runtime": "python3.11"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_uses_python_runtime(mock_client, config)

    def test_handler_uses_expected_architecture_success(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_architecture="arm64"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Architectures": ["arm64"]}
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_uses_expected_architecture(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_uses_expected_architecture_fails_when_different(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_architecture="arm64"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Architectures": ["x86_64"]}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_uses_expected_architecture(mock_client, config)

    def test_handler_has_handler_configured_success(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Handler": "handler.lambda_handler"}
        }
        config = {"func_key": "MyFunction"}
        instance.test_handler_has_handler_configured(mock_client, config)
        assert mock_client.get_function.called

    def test_handler_has_handler_configured_fails_when_different(self) -> None:
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Handler": "main.handler"}
        }
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_handler_configured(mock_client, config)


class TestCreateDeployedResourceExistenceTestsReturnsClass:
    def test_returns_class(self) -> None:
        result = create_deployed_resource_existence_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert isinstance(result, type)

    def test_returns_class_with_name(self) -> None:
        result = create_deployed_resource_existence_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert result.__name__ == "TestDeployedHandlerResourcesExist"


class TestCreateDeployedResourceExistenceTestsHasMethods:
    def test_has_test_handler_role_exists(self) -> None:
        test_class = create_deployed_resource_existence_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(test_class, "test_handler_role_exists")

    def test_has_test_handler_function_exists(self) -> None:
        test_class = create_deployed_resource_existence_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(test_class, "test_handler_function_exists")


class TestCreateDeployedResourceExistenceTestsExecution:
    @pytest.fixture
    def existence_tests(self) -> Any:
        test_class = create_deployed_resource_existence_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        return test_class()

    def test_iam_role_exists_success(self, existence_tests: Any) -> None:
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyFunctionServiceRole"}}
        config = {"func_key": "MyFunction"}
        existence_tests.test_handler_role_exists(mock_client, config)
        assert mock_client.get_role.called

    def test_iam_role_exists_fails_when_not_found(self, existence_tests: Any) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException(
            "Role not found"
        )
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            existence_tests.test_handler_role_exists(mock_client, config)

    def test_lambda_function_exists_success(self, existence_tests: Any) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"FunctionName": "MyFunction"}}
        config = {"func_key": "MyFunction"}
        existence_tests.test_handler_function_exists(mock_client, config)
        assert mock_client.get_function.called

    def test_lambda_function_exists_fails_when_not_found(self, existence_tests: Any) -> None:
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.get_function.side_effect = mock_client.exceptions.ResourceNotFoundException(
            "Function not found"
        )
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            existence_tests.test_handler_function_exists(mock_client, config)
