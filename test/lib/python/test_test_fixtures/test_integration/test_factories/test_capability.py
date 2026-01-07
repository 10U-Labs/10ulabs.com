"""Unit tests for test_fixtures.integration.factories.capability module."""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration.factories.capability import (
    create_layer6_capability_tests,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


# === create_layer6_capability_tests default capabilities ===


class TestCreateLayer6CapabilityTestsReturnsClass:
    """Tests for create_layer6_capability_tests return type."""

    def test_returns_class(self):
        """create_layer6_capability_tests returns a class."""
        test_class = create_layer6_capability_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_layer6_capability_tests returns class named TestDeploymentCapabilities."""
        test_class = create_layer6_capability_tests()
        assert test_class.__name__ == "TestDeploymentCapabilities"


class TestCreateLayer6CapabilityTestsDefaultCapabilities:
    """Tests for create_layer6_capability_tests with default capabilities."""

    def test_has_lambda_capability_by_default(self):
        """create_layer6_capability_tests includes lambda by default."""
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert "lambda" in capabilities

    def test_has_iam_capability_by_default(self):
        """create_layer6_capability_tests includes iam by default."""
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert "iam" in capabilities

    def test_has_two_default_capabilities(self):
        """create_layer6_capability_tests has two capabilities by default."""
        test_class = create_layer6_capability_tests()
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert len(capabilities) == 2


class TestCreateLayer6CapabilityTestsDefaultMethods:
    """Tests for create_layer6_capability_tests default methods."""

    def test_has_test_capabilities_configured_method(self):
        """create_layer6_capability_tests has test_capabilities_configured."""
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_capabilities_configured")

    def test_has_test_can_list_lambda_functions_method(self):
        """create_layer6_capability_tests has test_can_list_lambda_functions."""
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_can_list_lambda_functions")

    def test_has_test_can_list_iam_roles_method(self):
        """create_layer6_capability_tests has test_can_list_iam_roles."""
        test_class = create_layer6_capability_tests()
        assert hasattr(test_class, "test_can_list_iam_roles")


# === create_layer6_capability_tests with lambda capability ===


class TestCreateLayer6CapabilityTestsLambdaCapability:
    """Tests for create_layer6_capability_tests lambda capability."""

    def test_has_lambda_test_when_lambda_in_capabilities(self):
        """create_layer6_capability_tests has lambda test when lambda specified."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert hasattr(test_class, "test_can_list_lambda_functions")


class TestCreateLayer6CapabilityTestsLambdaTestBehavior:
    """Tests for test_can_list_lambda_functions behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_list_lambda_functions does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        instance.test_can_list_lambda_functions(mock_client)

    def test_fails_on_client_error(self):
        """test_can_list_lambda_functions fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_lambda_functions(mock_client)


# === create_layer6_capability_tests with iam capability ===


class TestCreateLayer6CapabilityTestsIAMCapability:
    """Tests for create_layer6_capability_tests IAM capability."""

    def test_has_iam_test_when_iam_in_capabilities(self):
        """create_layer6_capability_tests has IAM test when iam specified."""
        test_class = create_layer6_capability_tests(frozenset({"iam"}))
        assert hasattr(test_class, "test_can_list_iam_roles")


class TestCreateLayer6CapabilityTestsIAMTestBehavior:
    """Tests for test_can_list_iam_roles behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_list_iam_roles does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"iam"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        instance.test_can_list_iam_roles(mock_client)

    def test_fails_on_client_error(self):
        """test_can_list_iam_roles fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"iam"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_iam_roles(mock_client)


# === create_layer6_capability_tests with ssm capability ===


class TestCreateLayer6CapabilityTestsSSMCapability:
    """Tests for create_layer6_capability_tests SSM capability."""

    def test_has_ssm_test_when_ssm_in_capabilities(self):
        """create_layer6_capability_tests has SSM test when ssm specified."""
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        assert hasattr(test_class, "test_can_describe_ssm_parameters")

    def test_does_not_have_ssm_test_when_ssm_not_in_capabilities(self):
        """create_layer6_capability_tests has no SSM test when ssm not specified."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_describe_ssm_parameters")


class TestCreateLayer6CapabilityTestsSSMTestBehavior:
    """Tests for test_can_describe_ssm_parameters behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_describe_ssm_parameters does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_parameters.return_value = {"Parameters": []}
        instance.test_can_describe_ssm_parameters(mock_client)

    def test_fails_on_client_error(self):
        """test_can_describe_ssm_parameters fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"ssm"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_parameters.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_describe_ssm_parameters(mock_client)


# === create_layer6_capability_tests with dynamodb capability ===


class TestCreateLayer6CapabilityTestsDynamoDBCapability:
    """Tests for create_layer6_capability_tests DynamoDB capability."""

    def test_has_dynamodb_test_when_dynamodb_in_capabilities(self):
        """create_layer6_capability_tests has DynamoDB test when dynamodb specified."""
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        assert hasattr(test_class, "test_can_list_dynamodb_tables")

    def test_does_not_have_dynamodb_test_when_dynamodb_not_in_capabilities(self):
        """create_layer6_capability_tests has no DynamoDB test when dynamodb not specified."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_dynamodb_tables")


class TestCreateLayer6CapabilityTestsDynamoDBTestBehavior:
    """Tests for test_can_list_dynamodb_tables behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_list_dynamodb_tables does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_tables.return_value = {"TableNames": []}
        instance.test_can_list_dynamodb_tables(mock_client)

    def test_fails_on_client_error(self):
        """test_can_list_dynamodb_tables fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"dynamodb"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_tables.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_dynamodb_tables(mock_client)


# === create_layer6_capability_tests with logs capability ===


class TestCreateLayer6CapabilityTestsLogsCapability:
    """Tests for create_layer6_capability_tests logs capability."""

    def test_has_logs_test_when_logs_in_capabilities(self):
        """create_layer6_capability_tests has logs test when logs specified."""
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        assert hasattr(test_class, "test_can_list_log_groups")

    def test_does_not_have_logs_test_when_logs_not_in_capabilities(self):
        """create_layer6_capability_tests has no logs test when logs not specified."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_log_groups")


class TestCreateLayer6CapabilityTestsLogsTestBehavior:
    """Tests for test_can_list_log_groups behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_list_log_groups does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        instance.test_can_list_log_groups(mock_client)

    def test_fails_on_client_error(self):
        """test_can_list_log_groups fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"logs"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_log_groups(mock_client)


# === create_layer6_capability_tests with s3 capability ===


class TestCreateLayer6CapabilityTestsS3Capability:
    """Tests for create_layer6_capability_tests S3 capability."""

    def test_has_s3_test_when_s3_in_capabilities(self):
        """create_layer6_capability_tests has S3 test when s3 specified."""
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        assert hasattr(test_class, "test_can_list_s3_buckets")

    def test_does_not_have_s3_test_when_s3_not_in_capabilities(self):
        """create_layer6_capability_tests has no S3 test when s3 not specified."""
        test_class = create_layer6_capability_tests(frozenset({"lambda"}))
        assert not hasattr(test_class, "test_can_list_s3_buckets")


class TestCreateLayer6CapabilityTestsS3TestBehavior:
    """Tests for test_can_list_s3_buckets behavior."""

    def test_does_not_raise_on_success(self):
        """test_can_list_s3_buckets does not raise on success."""
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        instance.test_can_list_s3_buckets(mock_client)

    def test_fails_on_client_error(self):
        """test_can_list_s3_buckets fails on ClientError."""
        test_class = create_layer6_capability_tests(frozenset({"s3"}))
        instance = test_class()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_s3_buckets(mock_client)


# === create_layer6_capability_tests with multiple capabilities ===


class TestCreateLayer6CapabilityTestsMultipleCapabilities:
    """Tests for create_layer6_capability_tests with multiple capabilities."""

    def test_has_all_specified_capabilities(self):
        """create_layer6_capability_tests includes all specified capabilities."""
        test_class = create_layer6_capability_tests(
            frozenset({"lambda", "iam", "ssm", "dynamodb", "logs", "s3"})
        )
        instance = test_class()
        capabilities = instance.get_enabled_capabilities()
        assert "lambda" in capabilities
        assert "iam" in capabilities
        assert "ssm" in capabilities
        assert "dynamodb" in capabilities
        assert "logs" in capabilities
        assert "s3" in capabilities


class TestCreateLayer6CapabilityTestsEmptyCapabilities:
    """Tests for create_layer6_capability_tests with empty capabilities."""

    def test_test_capabilities_configured_fails_with_empty_set(self):
        """test_capabilities_configured fails with empty capabilities set."""
        test_class = create_layer6_capability_tests(frozenset())
        instance = test_class()
        with pytest.raises(AssertionError):
            instance.test_capabilities_configured()
