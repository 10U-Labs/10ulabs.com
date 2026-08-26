import inspect
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.factories.lambda_factories import (
    create_deployed_naming_convention_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
    create_naming_convention_tests,
)


class TestCreateLambdaApiGatewayWiringTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestLambdaWiring"


class TestCreateLambdaApiGatewayWiringTestsHasMethods:
    def test_has_test_handler_has_api_gateway_permission(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_api_gateway_permission")

    def test_has_test_handler_has_role_attached(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_has_role_attached")

    def test_has_test_handler_role_follows_naming_pattern(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_role_follows_naming_pattern")


class TestCreateLambdaApiGatewayWiringTestsExecution:
    def test_handler_has_api_gateway_permission_success(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_has_api_gateway_permission(mock_client, config) is None

    def test_handler_has_api_gateway_permission_uses_default(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {
            "Policy": '{"Statement":[{"Principal":{"Service":"apigateway.amazonaws.com"}}]}'
        }
        config = {}
        instance.test_handler_has_api_gateway_permission(mock_client, config)
        assert mock_client.get_policy.call_args[1]["FunctionName"] == "DefaultFunc"

    def test_handler_has_api_gateway_permission_fails_when_no_permission(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.return_value = {"Policy": '{"Statement":[]}'}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_fails_on_resource_not_found(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = create_client_error("ResourceNotFoundException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_api_gateway_permission_reraises_other_errors(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_policy.side_effect = create_client_error("ServiceException")
        config = {"func_key": "MyFunction"}
        with pytest.raises(ClientError):
            instance.test_handler_has_api_gateway_permission(mock_client, config)

    def test_handler_has_role_attached_success(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_has_role_attached(mock_client, config) is None

    def test_handler_has_role_attached_fails_when_no_role(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"Role": ""}}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            instance.test_handler_has_role_attached(mock_client, config)

    def test_handler_role_follows_naming_pattern_success(self):
        test_class = create_lambda_api_gateway_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Role": "arn:aws:iam::123:role/MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_role_follows_naming_pattern(mock_client, config) is None

    def test_handler_role_follows_naming_pattern_fails_when_pattern_mismatch(self):
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
    def test_returns_class(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestIAMPolicyWiring"


class TestCreateLambdaIamWiringTestsHasMethods:
    def test_has_test_config_has_function_name(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_config_has_function_name")

    def test_has_test_service_role_name_follows_convention(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_service_role_name_follows_convention")

    def test_has_basic_execution_policy_test_when_enabled(self):
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        assert hasattr(test_class, "test_handler_role_has_basic_execution_policy")

    def test_has_lambda_trust_test_when_enabled(self):
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=True
        )
        assert hasattr(test_class, "test_handler_role_can_assume_lambda_service")

    def test_no_basic_execution_test_when_disabled(self):
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=False
        )
        assert not hasattr(test_class, "test_handler_role_has_basic_execution_policy")

    def test_no_lambda_trust_test_when_disabled(self):
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_lambda_trust=False
        )
        assert not hasattr(test_class, "test_handler_role_can_assume_lambda_service")


class TestCreateLambdaIamWiringTestsExecution:
    def test_config_has_function_name_success(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        assert instance.test_config_has_function_name(config) is None

    def test_config_has_function_name_uses_default(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {}
        assert instance.test_config_has_function_name(config) is None

    def test_service_role_name_follows_convention_success(self):
        test_class = create_lambda_iam_wiring_tests("func_key", "DefaultFunc")
        instance = test_class()
        config = {"func_key": "MyFunction"}
        assert instance.test_service_role_name_follows_convention(config) is None

    def test_handler_role_has_basic_execution_policy_success(self):
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

    def test_handler_role_has_basic_execution_policy_fails_when_missing(self):
        test_class = create_lambda_iam_wiring_tests(
            "func_key", "DefaultFunc", check_basic_execution=True
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        config = {"func_key": "MyFunction"}
        with pytest.raises(AssertionError):
            getattr(instance, "test_handler_role_has_basic_execution_policy")(mock_client, config)

    def test_handler_role_can_assume_lambda_service_success(self):
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

    def test_handler_role_can_assume_lambda_service_fails_when_no_trust(self):
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
    def test_returns_class(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert test_class.__name__ == "TestLambdaExecutionRole"


class TestCreateLambdaExecutionRoleWiringTestsHasMethods:
    def test_has_test_lambda_has_execution_role_key(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_key")

    def test_has_test_lambda_has_execution_role_value(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_has_execution_role_value")

    def test_has_test_lambda_role_starts_with_iam_arn(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_starts_with_iam_arn")

    def test_has_test_lambda_role_contains_role_path(self):
        test_class = create_lambda_execution_role_wiring_tests()
        assert hasattr(test_class, "test_lambda_role_contains_role_path")


class TestCreateLambdaExecutionRoleWiringTestsExecution:
    def test_lambda_has_execution_role_key_success(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_lambda_has_execution_role_key(mock_request) is None

    def test_lambda_has_execution_role_value_success(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_lambda_has_execution_role_value(mock_request) is None

    def test_lambda_has_execution_role_value_fails_when_empty(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": ""}
        with pytest.raises(AssertionError):
            instance.test_lambda_has_execution_role_value(mock_request)

    def test_lambda_role_starts_with_iam_arn_success(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_lambda_role_starts_with_iam_arn(mock_request) is None

    def test_lambda_role_starts_with_iam_arn_fails_when_invalid(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-role"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_starts_with_iam_arn(mock_request)

    def test_lambda_role_contains_role_path_success(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_lambda_role_contains_role_path(mock_request) is None

    def test_lambda_role_contains_role_path_fails_when_missing(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:user/MyUser"}
        with pytest.raises(AssertionError):
            instance.test_lambda_role_contains_role_path(mock_request)

    def test_lambda_role_exists_success(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_lambda_role_exists(mock_client, mock_request) is None

    def test_lambda_role_exists_fails_when_no_role_name_extracted(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-no-slash"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_lambda_role_exists(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_success(self):
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
        assert instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request) is None

    def test_lambda_role_can_be_assumed_by_lambda_skips_when_no_role_name(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "invalid-no-slash"}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_fails_when_no_trust(self):
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

    def test_lambda_role_can_be_assumed_by_lambda_skips_on_no_such_entity(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)

    def test_lambda_role_can_be_assumed_by_lambda_reraises_other_errors(self):
        test_class = create_lambda_execution_role_wiring_tests("lambda_config")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"Role": "arn:aws:iam::123:role/MyRole"}
        with pytest.raises(ClientError):
            instance.test_lambda_role_can_be_assumed_by_lambda(mock_client, mock_request)


class TestCreateLambdaExistenceTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert test_class.__name__ == "TestDeployedResourcesExist"


class TestCreateLambdaExistenceTestsHasMethods:
    def test_has_test_handler_lambda_exists(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_lambda_exists")

    def test_has_test_handler_iam_role_exists(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        assert hasattr(test_class, "test_handler_iam_role_exists")

    def test_has_log_group_test_when_fixture_provided(self):
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        assert hasattr(test_class, "test_handler_log_group_exists")


class TestCreateLambdaExistenceTestsExecution:
    def test_handler_iam_role_exists_success(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyFunctionServiceRole"}}
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_iam_role_exists(mock_client, config) is None

    def test_handler_log_group_exists_success(self):
        test_class = create_lambda_existence_tests(
            "func_key", "DefaultFunc", "tf/path", log_group_fixture="log_group"
        )
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "exists": True, "name": "/aws/lambda/MyFunction"
        }
        assert getattr(instance, "test_handler_log_group_exists")(mock_request) is None

    def test_handler_log_group_exists_fails_when_not_exists(self):
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

    def test_handler_lambda_exists_success(self):
        test_class = create_lambda_existence_tests("func_key", "DefaultFunc", "tf/path")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"FunctionName": "MyFunction"}}
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_lambda_exists(mock_client, config) is None

    def test_handler_iam_role_exists_fails_when_no_such_entity(self):
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
    def test_expected_handler_has_no_default(self):
        parameters = inspect.signature(create_lambda_configuration_tests).parameters
        assert parameters["expected_handler"].default is inspect.Parameter.empty

    def test_other_configuration_arguments_keep_their_defaults(self):
        parameters = inspect.signature(create_lambda_configuration_tests).parameters
        assert all(
            parameters[name].default is not inspect.Parameter.empty
            for name in ("expected_runtime", "expected_architecture")
        )


class TestCreateLambdaConfigurationTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert test_class.__name__ == "TestLambdaConfiguration"


class TestCreateLambdaConfigurationTestsHasMethods:
    def test_has_test_handler_uses_python_runtime(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_uses_python_runtime")

    def test_has_test_handler_uses_expected_architecture(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_uses_expected_architecture")

    def test_has_test_handler_has_handler_configured(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        assert hasattr(test_class, "test_handler_has_handler_configured")


class TestCreateLambdaConfigurationTestsExecution:
    def test_handler_uses_python_runtime_success(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_runtime="python3.13"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Runtime": "python3.13"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_uses_python_runtime(mock_client, config) is None

    def test_handler_uses_python_runtime_fails_when_different(self):
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

    def test_handler_uses_expected_architecture_success(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", "handler.lambda_handler", expected_architecture="arm64"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Architectures": ["arm64"]}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_uses_expected_architecture(mock_client, config) is None

    def test_handler_uses_expected_architecture_fails_when_different(self):
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

    def test_handler_has_handler_configured_success(self):
        test_class = create_lambda_configuration_tests(
            "func_key", "DefaultFunc", expected_handler="handler.lambda_handler"
        )
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"Handler": "handler.lambda_handler"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_has_handler_configured(mock_client, config) is None

    def test_handler_has_handler_configured_fails_when_different(self):
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


class TestCreateNamingConventionTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert test_class.__name__ == "TestNamingConventions"


class TestCreateNamingConventionTestsHasMethods:
    def test_has_test_handler_lambda_name_is_pascalcase(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_lambda_name_is_pascalcase")

    def test_has_test_handler_role_name_is_pascalcase(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        assert hasattr(test_class, "test_handler_role_name_is_pascalcase")


class TestCreateNamingConventionTestsExecution:
    def test_handler_lambda_name_is_pascalcase_success(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyPascalCaseFunction"}
        }
        config = {"func_key": "MyPascalCaseFunction"}
        assert instance.test_handler_lambda_name_is_pascalcase(mock_client, config) is None

    def test_handler_lambda_name_is_pascalcase_fails_when_invalid(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "my_snake_case_function"}
        }
        config = {"func_key": "my_snake_case_function"}
        with pytest.raises(AssertionError):
            instance.test_handler_lambda_name_is_pascalcase(mock_client, config)

    def test_handler_role_name_is_pascalcase_success(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"RoleName": "MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_role_name_is_pascalcase(mock_client, config) is None

    def test_handler_role_name_is_pascalcase_fails_when_invalid(self):
        test_class = create_naming_convention_tests("func_key", "DefaultFunc")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"RoleName": "my_function_service_role"}
        }
        config = {"func_key": "my_function"}
        with pytest.raises(AssertionError):
            instance.test_handler_role_name_is_pascalcase(mock_client, config)


class TestCreateDeployedNamingConventionTestsReturnsTuple:
    def test_returns_tuple(self):
        result = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert isinstance(result, tuple)

    def test_returns_tuple_of_two(self):
        result = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert len(result) == 2

    def test_first_is_iam_class(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert iam_class.__name__ == "TestDeployedIAMRoleNamingConventions"

    def test_second_is_lambda_class(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert lambda_class.__name__ == "TestDeployedLambdaFunctionNamingConventions"


class TestCreateDeployedNamingConventionTestsHasMethods:
    def test_iam_class_has_test_handler_role_exists(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(iam_class, "test_handler_role_exists")

    def test_iam_class_has_test_handler_role_name_is_pascalcase(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(iam_class, "test_handler_role_name_is_pascalcase")

    def test_lambda_class_has_test_handler_function_exists(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(lambda_class, "test_handler_function_exists")

    def test_lambda_class_has_test_handler_function_name_is_pascalcase(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        assert hasattr(lambda_class, "test_handler_function_name_is_pascalcase")


class TestCreateDeployedNamingConventionTestsExecution:
    def test_iam_role_exists_success(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = iam_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyFunctionServiceRole"}}
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_role_exists(mock_client, config) is None

    def test_iam_role_exists_fails_when_not_found(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = iam_class()
        mock_client = MagicMock()
        mock_client.exceptions.NoSuchEntityException = type(
            "NoSuchEntityException", (Exception,), {}
        )
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException(
            "Role not found"
        )
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_role_exists(mock_client, config)

    def test_iam_role_name_is_pascalcase_success(self):
        iam_class, _ = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = iam_class()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {
            "Role": {"RoleName": "MyFunctionServiceRole"}
        }
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_role_name_is_pascalcase(mock_client, config) is None

    def test_lambda_function_exists_success(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = lambda_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"FunctionName": "MyFunction"}}
        config = {"func_key": "MyFunction"}
        assert instance.test_handler_function_exists(mock_client, config) is None

    def test_lambda_function_exists_fails_when_not_found(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = lambda_class()
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_client.get_function.side_effect = mock_client.exceptions.ResourceNotFoundException(
            "Function not found"
        )
        config = {"func_key": "MyFunction"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_handler_function_exists(mock_client, config)

    def test_lambda_function_name_is_pascalcase_success(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = lambda_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyPascalCaseFunction"}
        }
        config = {"func_key": "MyPascalCaseFunction"}
        assert instance.test_handler_function_name_is_pascalcase(mock_client, config) is None

    def test_lambda_function_name_is_pascalcase_fails_when_invalid(self):
        _, lambda_class = create_deployed_naming_convention_tests(
            "func_key", "DefaultFunc", "TestHandler"
        )
        instance = lambda_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "my_snake_case_function"}
        }
        config = {"func_key": "my_snake_case_function"}
        with pytest.raises(AssertionError):
            instance.test_handler_function_name_is_pascalcase(mock_client, config)
