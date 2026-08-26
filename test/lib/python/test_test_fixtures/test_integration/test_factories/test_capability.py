from unittest.mock import MagicMock

import pytest

from boto_mocks import create_client_error
from test_fixtures.integration.factories.capability import (
    create_layer6_capability_tests,
)


class TestCreateLayer6CapabilityTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_layer6_capability_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_layer6_capability_tests()
        assert test_class.__name__ == "TestDeploymentCapabilities"


class TestCreateLayer6CapabilityTestsDefaultCapabilities:
    def test_has_lambda_capability_by_default(self):
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert "lambda" in capabilities

    def test_has_iam_capability_by_default(self):
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert "iam" in capabilities

    def test_has_two_default_capabilities(self):
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert len(capabilities) == 2


class TestCreateLayer6CapabilityTestsDefaultMethods:
    def test_has_test_capabilities_configured_method(self):
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_capabilities_configured")

    def test_has_test_can_list_lambda_functions_method(self):
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_can_list_lambda_functions")

    def test_has_test_can_list_iam_roles_method(self):
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_can_list_iam_roles")


def test_create_layer6_capability_tests_lambda_capability():
    test_class = create_layer6_capability_tests(frozenset({"lambda"}))
    assert hasattr(test_class, "test_can_list_lambda_functions")


class TestCreateLayer6CapabilityTestsLambdaTestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        assert getattr(instance, "test_can_list_lambda_functions")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_list_lambda_functions")(mock_client)


def test_create_layer6_capability_tests_iam_capability():
    test_class = create_layer6_capability_tests(frozenset({"iam"}))
    assert hasattr(test_class, "test_can_list_iam_roles")


class TestCreateLayer6CapabilityTestsIAMTestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"iam"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert getattr(instance, "test_can_list_iam_roles")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"iam"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_list_iam_roles")(mock_client)


class TestCreateLayer6CapabilityTestsSSMCapability:
    def test_has_ssm_test_when_ssm_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        assert hasattr(test_class, "test_can_describe_ssm_parameters")

    def test_does_not_have_ssm_test_when_ssm_not_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_describe_ssm_parameters")


class TestCreateLayer6CapabilityTestsSSMTestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_parameters.return_value = {"Parameters": []}
        assert getattr(instance, "test_can_describe_ssm_parameters")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_parameters.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_describe_ssm_parameters")(mock_client)


class TestCreateLayer6CapabilityTestsDynamoDBCapability:
    def test_has_dynamodb_test_when_dynamodb_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        assert hasattr(test_class, "test_can_list_dynamodb_tables")

    def test_does_not_have_dynamodb_test_when_dynamodb_not_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_dynamodb_tables")


class TestCreateLayer6CapabilityTestsDynamoDBTestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_tables.return_value = {"TableNames": []}
        assert getattr(instance, "test_can_list_dynamodb_tables")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_tables.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_list_dynamodb_tables")(mock_client)


class TestCreateLayer6CapabilityTestsLogsCapability:
    def test_has_logs_test_when_logs_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        assert hasattr(test_class, "test_can_list_log_groups")

    def test_does_not_have_logs_test_when_logs_not_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_log_groups")


class TestCreateLayer6CapabilityTestsLogsTestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        assert getattr(instance, "test_can_list_log_groups")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_list_log_groups")(mock_client)


class TestCreateLayer6CapabilityTestsS3Capability:
    def test_has_s3_test_when_s3_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        assert hasattr(test_class, "test_can_list_s3_buckets")

    def test_does_not_have_s3_test_when_s3_not_in_capabilities(self):
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_s3_buckets")


class TestCreateLayer6CapabilityTestsS3TestBehavior:
    def test_does_not_raise_on_success(self):
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        assert getattr(instance, "test_can_list_s3_buckets")(mock_client) is None

    def test_fails_on_create_client_error(self):
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            getattr(instance, "test_can_list_s3_buckets")(mock_client)


class TestCreateLayer6CapabilityTestsMultipleCapabilities:
    def _get_all_capabilities(self):
        test_class = create_layer6_capability_tests(
            frozenset({"lambda", "iam", "ssm", "dynamodb", "logs", "s3"})
        )
        instance = test_class()
        return instance.get_enabled_capabilities()

    def test_has_lambda_when_all_specified(self):
        assert "lambda" in self._get_all_capabilities()

    def test_has_iam_when_all_specified(self):
        assert "iam" in self._get_all_capabilities()

    def test_has_ssm_when_all_specified(self):
        assert "ssm" in self._get_all_capabilities()

    def test_has_dynamodb_when_all_specified(self):
        assert "dynamodb" in self._get_all_capabilities()

    def test_has_logs_when_all_specified(self):
        assert "logs" in self._get_all_capabilities()

    def test_has_s3_when_all_specified(self):
        assert "s3" in self._get_all_capabilities()


def test_create_layer6_capability_tests_empty_capabilities():
    test_class = create_layer6_capability_tests(frozenset())
    instance = test_class()
    with pytest.raises(AssertionError):
        instance.test_capabilities_configured()
