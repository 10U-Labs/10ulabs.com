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


# === Method Execution Tests ===


class TestEcsRunnerOutputsClusterNameExecution:
    """Tests that execute test_cluster_name_output_exists."""

    def test_passes_when_output_exists(self):
        """test_cluster_name_output_exists passes when output exists."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {"cluster_name": "my-cluster"}
        result = instance.test_cluster_name_output_exists(outputs)
        assert result is None

    def test_fails_when_output_missing(self):
        """test_cluster_name_output_exists fails when output missing."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_cluster_name_output_exists(outputs)


class TestEcsRunnerOutputsLambdaFunctionNameExecution:
    """Tests that execute test_lambda_function_name_output_exists."""

    def test_passes_when_output_exists(self):
        """test_lambda_function_name_output_exists passes when output exists."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {"lambda_function_name": "my-function"}
        result = instance.test_lambda_function_name_output_exists(outputs)
        assert result is None

    def test_fails_when_output_missing(self):
        """test_lambda_function_name_output_exists fails when output missing."""
        test_class = create_ecs_runner_outputs_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_lambda_function_name_output_exists(outputs)


class TestEcsRunnerLambdaExistenceExecution:
    """Tests that execute ECS runner Lambda existence test methods."""

    def test_lambda_function_exists_success(self):
        """test_lambda_function_exists passes when Lambda exists."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"FunctionName": "my-func"}}
        outputs = {"lambda_function_name": "my-func"}
        result = instance.test_lambda_function_exists(mock_client, outputs)
        assert result is None

    def test_lambda_function_exists_skips_when_no_output(self):
        """test_lambda_function_exists skips when output missing."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        outputs = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_function_exists(mock_client, outputs)

    def test_lambda_function_exists_fails_on_not_found(self):
        """test_lambda_function_exists fails when Lambda not found."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error("ResourceNotFoundException")
        outputs = {"lambda_function_name": "my-func"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_lambda_function_exists(mock_client, outputs)

    def test_lambda_function_exists_reraises_other_errors(self):
        """test_lambda_function_exists reraises other errors."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error("ServiceException")
        outputs = {"lambda_function_name": "my-func"}
        with pytest.raises(ClientError):
            instance.test_lambda_function_exists(mock_client, outputs)

    def test_lambda_function_is_active_success(self):
        """test_lambda_function_is_active passes when Lambda is active."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"State": "Active"}}
        outputs = {"lambda_function_name": "my-func"}
        result = instance.test_lambda_function_is_active(mock_client, outputs)
        assert result is None

    def test_lambda_function_is_active_skips_when_no_output(self):
        """test_lambda_function_is_active skips when output missing."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        outputs = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_function_is_active(mock_client, outputs)

    def test_lambda_function_is_active_fails_when_not_active(self):
        """test_lambda_function_is_active fails when Lambda not active."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.return_value = {"Configuration": {"State": "Pending"}}
        outputs = {"lambda_function_name": "my-func"}
        with pytest.raises(AssertionError):
            instance.test_lambda_function_is_active(mock_client, outputs)

    def test_lambda_function_is_active_skips_on_not_found(self):
        """test_lambda_function_is_active skips when Lambda not found."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error("ResourceNotFoundException")
        outputs = {"lambda_function_name": "my-func"}
        with pytest.raises(pytest.skip.Exception):
            instance.test_lambda_function_is_active(mock_client, outputs)

    def test_lambda_function_is_active_reraises_other_errors(self):
        """test_lambda_function_is_active reraises other errors."""
        test_class = create_ecs_runner_lambda_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error("ServiceException")
        outputs = {"lambda_function_name": "my-func"}
        with pytest.raises(ClientError):
            instance.test_lambda_function_is_active(mock_client, outputs)


class TestWwwCommonS3ExistenceS3BucketExistsExecution:
    """Tests that execute test_s3_bucket_exists method."""

    def test_s3_bucket_exists_success(self):
        """test_s3_bucket_exists passes when bucket exists."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        outputs = {"bucket_name": "my-bucket"}
        result = instance.test_s3_bucket_exists(mock_client, outputs)
        assert result is None

    def test_s3_bucket_exists_skips_when_no_output(self):
        """test_s3_bucket_exists skips when output missing."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        outputs = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_s3_bucket_exists(mock_client, outputs)

    def test_s3_bucket_exists_fails_on_404(self):
        """test_s3_bucket_exists fails when bucket not found."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("404")
        outputs = {"bucket_name": "my-bucket"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_s3_bucket_exists(mock_client, outputs)

    def test_s3_bucket_exists_reraises_other_errors(self):
        """test_s3_bucket_exists reraises other errors."""
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("500")
        outputs = {"bucket_name": "my-bucket"}
        with pytest.raises(ClientError):
            instance.test_s3_bucket_exists(mock_client, outputs)


class TestSqsFifoQueueTestsExecution:
    """Tests that execute SQS FIFO queue test methods."""

    def test_queue_exists_success(self):
        """test_queue_exists passes when queue exists."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        result = instance.test_queue_exists(mock_client, mock_request)
        assert result is None

    def test_queue_exists_skips_on_non_existent(self):
        """test_queue_exists skips when queue doesn't exist (fail_on_missing=False)."""
        test_class = create_sqs_fifo_queue_tests("queue_name", fail_on_missing=False)
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = _create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_exists_fails_on_non_existent_when_fail_on_missing(self):
        """test_queue_exists fails when queue doesn't exist (fail_on_missing=True)."""
        test_class = create_sqs_fifo_queue_tests("queue_name", fail_on_missing=True)
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = _create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.fail.Exception):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_exists_reraises_other_errors(self):
        """test_queue_exists reraises other errors."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = _create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(ClientError):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_is_fifo_success(self):
        """test_queue_is_fifo passes when queue is FIFO."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"FifoQueue": "true"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        result = instance.test_queue_is_fifo(mock_client, mock_request)
        assert result is None

    def test_queue_is_fifo_fails_when_not_fifo(self):
        """test_queue_is_fifo fails when queue is not FIFO."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"FifoQueue": "false"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(AssertionError):
            instance.test_queue_is_fifo(mock_client, mock_request)

    def test_queue_is_fifo_skips_on_non_existent(self):
        """test_queue_is_fifo skips when queue doesn't exist."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = _create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_is_fifo(mock_client, mock_request)

    def test_queue_has_deduplication_success(self):
        """test_queue_has_deduplication passes when deduplication enabled."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"ContentBasedDeduplication": "true"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        result = instance.test_queue_has_deduplication(mock_client, mock_request)
        assert result is None

    def test_queue_has_deduplication_fails_when_disabled(self):
        """test_queue_has_deduplication fails when deduplication disabled."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"ContentBasedDeduplication": "false"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(AssertionError):
            instance.test_queue_has_deduplication(mock_client, mock_request)

    def test_queue_has_deduplication_skips_on_non_existent(self):
        """test_queue_has_deduplication skips when queue doesn't exist."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = _create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_has_deduplication(mock_client, mock_request)


class TestSecurityGroupExistenceExecution:
    """Tests that execute security group existence test."""

    def test_security_group_exists_success(self):
        """test_security_group_exists passes when SG exists."""
        test_func = create_security_group_existence_test("outputs_fixture")
        mock_client = MagicMock()
        mock_client.describe_security_groups.return_value = {"SecurityGroups": [{}]}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"runner_security_group_id": "sg-123"}
        result = test_func(None, mock_client, mock_request)
        assert result is None

    def test_security_group_exists_skips_when_no_output(self):
        """test_security_group_exists skips when output missing."""
        test_func = create_security_group_existence_test("outputs_fixture")
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {}
        with pytest.raises(pytest.skip.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_fails_on_not_found(self):
        """test_security_group_exists fails when SG not found."""
        test_func = create_security_group_existence_test("outputs_fixture")
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = _create_client_error(
            "InvalidGroup.NotFound"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"runner_security_group_id": "sg-123"}
        with pytest.raises(pytest.fail.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_reraises_other_errors(self):
        """test_security_group_exists reraises other errors."""
        test_func = create_security_group_existence_test("outputs_fixture")
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = _create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"runner_security_group_id": "sg-123"}
        with pytest.raises(ClientError):
            test_func(None, mock_client, mock_request)


class TestLogGroupConfigurationExecution:
    """Tests that execute log group configuration test methods."""

    def test_log_group_has_retention_set_success(self):
        """test_handler_log_group_has_retention_set passes when retention set."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
        result = instance.test_handler_log_group_has_retention_set(mock_request)
        assert result is None

    def test_log_group_has_retention_set_fails_when_none(self):
        """test_handler_log_group_has_retention_set fails when retention is None."""
        test_class = create_log_group_configuration_tests("log_group_fixture")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": None}
        with pytest.raises(AssertionError):
            instance.test_handler_log_group_has_retention_set(mock_request)

    def test_log_group_retention_is_expected_success(self):
        """test_handler_log_group_retention_is_expected passes when retention matches."""
        test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
        result = instance.test_handler_log_group_retention_is_expected(mock_request)
        assert result is None

    def test_log_group_retention_is_expected_fails_when_different(self):
        """test_handler_log_group_retention_is_expected fails when retention differs."""
        test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 30}
        with pytest.raises(AssertionError):
            instance.test_handler_log_group_retention_is_expected(mock_request)
