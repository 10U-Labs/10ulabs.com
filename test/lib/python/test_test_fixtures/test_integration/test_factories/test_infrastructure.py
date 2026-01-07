"""Unit tests for test_fixtures.integration.factories.infrastructure module."""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration.factories.infrastructure import (
    create_ecs_runner_lambda_existence_tests,
    create_ecs_runner_outputs_tests,
    create_kms_policy_test,
    create_lambda_role_existence_test,
    create_log_group_configuration_tests,
    create_security_group_existence_test,
    create_sqs_fifo_queue_tests,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


# === create_ecs_runner_outputs_tests ===


class TestCreateEcsRunnerOutputsTestsReturnsClass:
    """Tests for create_ecs_runner_outputs_tests return type."""

    def test_returns_class(self):
        """create_ecs_runner_outputs_tests returns a class."""
        test_class = create_ecs_runner_outputs_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_ecs_runner_outputs_tests returns class named TestECSRunnerOutputs."""
        test_class = create_ecs_runner_outputs_tests()
        assert test_class.__name__ == "TestECSRunnerOutputs"


class TestCreateEcsRunnerOutputsTestsHasMethods:
    """Tests for create_ecs_runner_outputs_tests class methods."""

    def test_has_test_task_definition_arn_output_exists(self):
        """create_ecs_runner_outputs_tests has test_task_definition_arn_output_exists."""
        test_class = create_ecs_runner_outputs_tests()
        assert hasattr(test_class, "test_task_definition_arn_output_exists")

    def test_has_test_cluster_arn_output_exists(self):
        """create_ecs_runner_outputs_tests has test_cluster_arn_output_exists."""
        test_class = create_ecs_runner_outputs_tests()
        assert hasattr(test_class, "test_cluster_arn_output_exists")

    def test_has_test_cluster_name_output_exists(self):
        """create_ecs_runner_outputs_tests has test_cluster_name_output_exists."""
        test_class = create_ecs_runner_outputs_tests()
        assert hasattr(test_class, "test_cluster_name_output_exists")

    def test_has_test_lambda_function_name_output_exists(self):
        """create_ecs_runner_outputs_tests has test_lambda_function_name_output_exists."""
        test_class = create_ecs_runner_outputs_tests()
        assert hasattr(test_class, "test_lambda_function_name_output_exists")


class TestCreateEcsRunnerOutputsTestsTaskDefinitionArn:
    """Tests for test_task_definition_arn_output_exists method."""

    def test_does_not_raise_when_output_exists(self):
        """test_task_definition_arn_output_exists does not raise when output exists."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {"task_definition_arn": "arn:aws:ecs:us-east-1:123:task-def"}
        result = instance.test_task_definition_arn_output_exists(outputs)
        assert result is None

    def test_fails_when_output_missing(self):
        """test_task_definition_arn_output_exists fails when output missing."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_task_definition_arn_output_exists(outputs)


class TestCreateEcsRunnerOutputsTestsClusterArn:
    """Tests for test_cluster_arn_output_exists method."""

    def test_does_not_raise_when_output_exists(self):
        """test_cluster_arn_output_exists does not raise when output exists."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {"cluster_arn": "arn:aws:ecs:us-east-1:123:cluster/test"}
        result = instance.test_cluster_arn_output_exists(outputs)
        assert result is None

    def test_fails_when_output_missing(self):
        """test_cluster_arn_output_exists fails when output missing."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_cluster_arn_output_exists(outputs)


# === create_ecs_runner_lambda_existence_tests ===


class TestCreateEcsRunnerLambdaExistenceTestsReturnsClass:
    """Tests for create_ecs_runner_lambda_existence_tests return type."""

    def test_returns_class(self):
        """create_ecs_runner_lambda_existence_tests returns a class."""
        test_class = create_ecs_runner_lambda_existence_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_ecs_runner_lambda_existence_tests returns class named TestECSRunnerLambdaExistence."""
        test_class = create_ecs_runner_lambda_existence_tests()
        assert test_class.__name__ == "TestECSRunnerLambdaExistence"


class TestCreateEcsRunnerLambdaExistenceTestsHasMethods:
    """Tests for create_ecs_runner_lambda_existence_tests class methods."""

    def test_has_test_lambda_function_exists(self):
        """create_ecs_runner_lambda_existence_tests has test_lambda_function_exists."""
        test_class = create_ecs_runner_lambda_existence_tests()
        assert hasattr(test_class, "test_lambda_function_exists")

    def test_has_test_lambda_function_is_active(self):
        """create_ecs_runner_lambda_existence_tests has test_lambda_function_is_active."""
        test_class = create_ecs_runner_lambda_existence_tests()
        assert hasattr(test_class, "test_lambda_function_is_active")


# === create_www_common_s3_existence_tests ===


class TestCreateWwwCommonS3ExistenceTestsReturnsClass:
    """Tests for create_www_common_s3_existence_tests return type."""

    def test_returns_class(self):
        """create_www_common_s3_existence_tests returns a class."""
        test_class = create_www_common_s3_existence_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_www_common_s3_existence_tests returns class named TestWWWCommonS3Existence."""
        test_class = create_www_common_s3_existence_tests()
        assert test_class.__name__ == "TestWWWCommonS3Existence"


class TestCreateWwwCommonS3ExistenceTestsHasMethods:
    """Tests for create_www_common_s3_existence_tests class methods."""

    def test_has_test_bucket_name_output_exists(self):
        """create_www_common_s3_existence_tests has test_bucket_name_output_exists."""
        test_class = create_www_common_s3_existence_tests()
        assert hasattr(test_class, "test_bucket_name_output_exists")

    def test_has_test_s3_bucket_exists(self):
        """create_www_common_s3_existence_tests has test_s3_bucket_exists."""
        test_class = create_www_common_s3_existence_tests()
        assert hasattr(test_class, "test_s3_bucket_exists")


class TestCreateWwwCommonS3ExistenceTestsBucketNameOutput:
    """Tests for test_bucket_name_output_exists method."""

    def test_does_not_raise_when_output_exists(self):
        """test_bucket_name_output_exists does not raise when output exists."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        outputs = {"bucket_name": "my-bucket"}
        result = instance.test_bucket_name_output_exists(outputs)
        assert result is None

    def test_fails_when_output_missing(self):
        """test_bucket_name_output_exists fails when output missing."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_bucket_name_output_exists(outputs)


# === create_sqs_fifo_queue_tests ===


class TestCreateSqsFifoQueueTestsReturnsClass:
    """Tests for create_sqs_fifo_queue_tests return type."""

    def test_returns_class(self):
        """create_sqs_fifo_queue_tests returns a class."""
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_sqs_fifo_queue_tests returns class named TestSQSFIFOQueue."""
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert test_class.__name__ == "TestSQSFIFOQueue"


class TestCreateSqsFifoQueueTestsHasMethods:
    """Tests for create_sqs_fifo_queue_tests class methods."""

    def test_has_test_queue_exists(self):
        """create_sqs_fifo_queue_tests has test_queue_exists."""
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_exists")

    def test_has_test_queue_is_fifo(self):
        """create_sqs_fifo_queue_tests has test_queue_is_fifo."""
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_is_fifo")

    def test_has_test_queue_has_deduplication(self):
        """create_sqs_fifo_queue_tests has test_queue_has_deduplication."""
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_has_deduplication")


# === handle_ecr_error ===


class TestHandleEcrErrorRepositoryNotFound:
    """Tests for handle_ecr_error with RepositoryNotFoundException."""

    def test_skips_on_repository_not_found(self):
        """handle_ecr_error skips on RepositoryNotFoundException."""
        error = _create_client_error("RepositoryNotFoundException")
        with pytest.raises(pytest.skip.Exception):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")


class TestHandleEcrErrorAccessDenied:
    """Tests for handle_ecr_error with AccessDeniedException."""

    def test_fails_on_access_denied(self):
        """handle_ecr_error fails on AccessDeniedException."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")

    def test_error_message_contains_operation(self):
        """handle_ecr_error error message contains operation."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="ecr:ListImages"):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")

    def test_error_message_contains_repository_name(self):
        """handle_ecr_error error message contains repository name."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="my-repo"):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")


class TestHandleEcrErrorOtherErrors:
    """Tests for handle_ecr_error with other errors."""

    def test_reraises_other_errors(self):
        """handle_ecr_error reraises other errors."""
        error = _create_client_error("ServiceException")
        with pytest.raises(ClientError, match="ServiceException"):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")


# === create_security_group_existence_test ===


class TestCreateSecurityGroupExistenceTestReturnsFunction:
    """Tests for create_security_group_existence_test return type."""

    def test_returns_callable(self):
        """create_security_group_existence_test returns a callable."""
        test_func = create_security_group_existence_test("outputs_fixture")
        assert callable(test_func)

    def test_returns_function_with_name(self):
        """create_security_group_existence_test returns function with correct name."""
        test_func = create_security_group_existence_test("outputs_fixture")
        assert test_func.__name__ == "test_security_group_exists"


# === create_log_group_configuration_tests ===


class TestCreateLogGroupConfigurationTestsReturnsClass:
    """Tests for create_log_group_configuration_tests return type."""

    def test_returns_class(self):
        """create_log_group_configuration_tests returns a class."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_log_group_configuration_tests returns class named TestCloudWatchLogsConfiguration."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert test_class.__name__ == "TestCloudWatchLogsConfiguration"


class TestCreateLogGroupConfigurationTestsHasMethods:
    """Tests for create_log_group_configuration_tests class methods."""

    def test_has_test_handler_log_group_has_retention_set(self):
        """create_log_group_configuration_tests has test_handler_log_group_has_retention_set."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert hasattr(test_class, "test_handler_log_group_has_retention_set")

    def test_has_test_handler_log_group_retention_is_expected(self):
        """create_log_group_configuration_tests has test_handler_log_group_retention_is_expected."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert hasattr(test_class, "test_handler_log_group_retention_is_expected")


# === create_lambda_role_existence_test ===


class TestCreateLambdaRoleExistenceTestReturnsFunction:
    """Tests for create_lambda_role_existence_test return type."""

    def test_returns_callable(self):
        """create_lambda_role_existence_test returns a callable."""
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        assert callable(test_func)

    def test_returns_function_with_name(self):
        """create_lambda_role_existence_test returns function with correct name."""
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        assert test_func.__name__ == "test_lambda_execution_role_exists"


# === create_kms_policy_test ===


class TestCreateKmsPolicyTestReturnsFunction:
    """Tests for create_kms_policy_test return type."""

    def test_returns_callable(self):
        """create_kms_policy_test returns a callable."""
        test_func = create_kms_policy_test("role_name_fixture")
        assert callable(test_func)

    def test_returns_function_with_name(self):
        """create_kms_policy_test returns function with correct name."""
        test_func = create_kms_policy_test("role_name_fixture")
        assert test_func.__name__ == "test_lambda_role_has_kms_policy"
