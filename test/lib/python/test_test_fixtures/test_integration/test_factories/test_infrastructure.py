"""Unit tests for test_fixtures.integration.factories.infrastructure module."""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration.factories.infrastructure import (
    create_kms_policy_test,
    create_lambda_role_existence_test,
    create_log_group_configuration_tests,
    create_security_group_existence_test,
    create_sqs_fifo_queue_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


def _create_nonexistent_queue_mocks():
    """Create mocks for a non-existent SQS queue scenario."""
    mock_client = MagicMock()
    mock_client.get_queue_url.side_effect = _create_client_error(
        "AWS.SimpleQueueService.NonExistentQueue"
    )
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-queue.fifo"
    return mock_client, mock_request


def _create_sqs_service_error_mocks():
    """Create mocks for SQS queue service error re-raise scenario."""
    mock_client = MagicMock()
    mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
    mock_client.get_queue_attributes.side_effect = _create_client_error("ServiceException")
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-queue.fifo"
    return mock_client, mock_request


# === create_www_common_fixtures ===


class TestCreateWwwCommonFixturesReturnsFixtures:
    """Tests for create_www_common_fixtures return type."""

    def test_returns_tuple(self):
        """create_www_common_fixtures returns a tuple."""
        result = create_www_common_fixtures()
        assert isinstance(result, tuple)

    def test_returns_two_fixtures(self):
        """create_www_common_fixtures returns two fixtures."""
        result = create_www_common_fixtures()
        assert len(result) == 2

    def test_first_fixture_is_callable(self):
        """create_www_common_fixtures first fixture is callable."""
        result = create_www_common_fixtures()
        assert callable(result[0])

    def test_second_fixture_is_callable(self):
        """create_www_common_fixtures second fixture is callable."""
        result = create_www_common_fixtures()
        assert callable(result[1])

    def test_first_fixture_has_correct_name(self):
        """create_www_common_fixtures first fixture is www_common_terraform_initialized."""
        result = create_www_common_fixtures()
        assert result[0].__name__ == "www_common_terraform_initialized"

    def test_second_fixture_has_correct_name(self):
        """create_www_common_fixtures second fixture is www_common_outputs."""
        result = create_www_common_fixtures()
        assert result[1].__name__ == "www_common_outputs"


class TestCreateWwwCommonFixturesOptions:
    """Tests for create_www_common_fixtures option handling."""

    def test_accepts_include_cloudfront(self):
        """create_www_common_fixtures accepts include_cloudfront parameter."""
        result = create_www_common_fixtures(include_cloudfront=True)
        assert len(result) == 2

    def test_accepts_include_website_domain(self):
        """create_www_common_fixtures accepts include_website_domain parameter."""
        result = create_www_common_fixtures(include_website_domain=True)
        assert len(result) == 2

    def test_accepts_both_options(self):
        """create_www_common_fixtures accepts both options."""
        result = create_www_common_fixtures(
            include_cloudfront=True, include_website_domain=True
        )
        assert len(result) == 2


class TestWwwCommonFixturesExecution:
    """Tests that execute www_common fixtures via __wrapped__."""

    def test_terraform_initialized_calls_terraform_init(self, monkeypatch):
        """www_common_terraform_initialized fixture calls terraform_init."""
        mock_init = MagicMock(return_value=True)
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_init",
            mock_init
        )
        tf_init, _ = create_www_common_fixtures()
        result = tf_init.__wrapped__()
        assert result is True
        mock_init.assert_called_once()

    def test_outputs_skips_when_init_fails(self, monkeypatch):
        """www_common_outputs fixture skips when terraform init fails."""
        mock_init = MagicMock(return_value=False)
        mock_output = MagicMock(return_value="value")
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_init",
            mock_init
        )
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_output",
            mock_output
        )
        _, outputs_fixture = create_www_common_fixtures()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = False
        with pytest.raises(pytest.skip.Exception):
            outputs_fixture.__wrapped__(mock_request)

    def test_outputs_returns_bucket_info(self, monkeypatch):
        """www_common_outputs fixture returns bucket info."""
        mock_output = MagicMock(side_effect=["my-bucket", "arn:aws:s3:::my-bucket"])
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_output",
            mock_output
        )
        _, outputs_fixture = create_www_common_fixtures()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = True
        result = outputs_fixture.__wrapped__(mock_request)
        assert "bucket_name" in result and "bucket_arn" in result

    def test_outputs_includes_website_domain_when_requested(self, monkeypatch):
        """www_common_outputs includes website_domain_name when requested."""
        mock_output = MagicMock(side_effect=[
            "my-bucket", "arn:aws:s3:::my-bucket", "example.com"
        ])
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_output",
            mock_output
        )
        _, outputs_fixture = create_www_common_fixtures(include_website_domain=True)
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = True
        result = outputs_fixture.__wrapped__(mock_request)
        assert "website_domain_name" in result

    def test_outputs_includes_cloudfront_when_requested(self, monkeypatch):
        """www_common_outputs includes cloudfront_distribution_id when requested."""
        mock_output = MagicMock(side_effect=[
            "my-bucket", "arn:aws:s3:::my-bucket", "E123456789"
        ])
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_output",
            mock_output
        )
        _, outputs_fixture = create_www_common_fixtures(include_cloudfront=True)
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = True
        result = outputs_fixture.__wrapped__(mock_request)
        assert "cloudfront_distribution_id" in result

    def test_outputs_includes_both_when_requested(self, monkeypatch):
        """www_common_outputs includes both optional fields when requested."""
        mock_output = MagicMock(side_effect=[
            "my-bucket", "arn:aws:s3:::my-bucket", "example.com", "E123456789"
        ])
        monkeypatch.setattr(
            "test_fixtures.integration.factories.infrastructure.terraform_output",
            mock_output
        )
        _, outputs_fixture = create_www_common_fixtures(
            include_website_domain=True, include_cloudfront=True
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = True
        result = outputs_fixture.__wrapped__(mock_request)
        assert "website_domain_name" in result and "cloudfront_distribution_id" in result


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
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        assert callable(test_func)

    def test_returns_function_with_name(self):
        """create_security_group_existence_test returns function with correct name."""
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
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
        instance = create_sqs_fifo_queue_tests("queue_name")()
        mock_client, mock_request = _create_nonexistent_queue_mocks()
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
        instance = create_sqs_fifo_queue_tests("queue_name")()
        mock_client, mock_request = _create_nonexistent_queue_mocks()
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_has_deduplication(mock_client, mock_request)


class TestSecurityGroupExistenceExecution:
    """Tests that execute security group existence test."""

    def test_security_group_exists_success(self):
        """test_security_group_exists passes when SG exists."""
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.return_value = {"SecurityGroups": [{}]}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
        result = test_func(None, mock_client, mock_request)
        assert result is None

    def test_security_group_exists_skips_when_no_output(self):
        """test_security_group_exists skips when output missing."""
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {}
        with pytest.raises(pytest.skip.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_fails_on_not_found(self):
        """test_security_group_exists fails when SG not found."""
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = _create_client_error(
            "InvalidGroup.NotFound"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
        with pytest.raises(pytest.fail.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_reraises_other_errors(self):
        """test_security_group_exists reraises other errors."""
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = _create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
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


class TestSqsFifoQueueTestsErrorReRaise:
    """Tests that verify error re-raise behavior in SQS FIFO queue tests."""

    def test_queue_is_fifo_reraises_other_errors(self):
        """test_queue_is_fifo reraises non-queue errors."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client, mock_request = _create_sqs_service_error_mocks()
        with pytest.raises(ClientError):
            instance.test_queue_is_fifo(mock_client, mock_request)

    def test_queue_has_deduplication_reraises_other_errors(self):
        """test_queue_has_deduplication reraises non-queue errors."""
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client, mock_request = _create_sqs_service_error_mocks()
        with pytest.raises(ClientError):
            instance.test_queue_has_deduplication(mock_client, mock_request)


class TestLambdaRoleExistenceExecution:
    """Tests that execute Lambda role existence test."""

    def test_lambda_execution_role_exists_calls_helper(self):
        """test_lambda_execution_role_exists calls check_iam_role_exists."""
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        result = test_func(None, mock_client, mock_request)
        assert result is None
        mock_client.get_role.assert_called_once_with(RoleName="my-role")

    def test_lambda_execution_role_exists_fails_when_role_missing(self):
        """test_lambda_execution_role_exists fails when role doesn't exist."""
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        mock_client = MagicMock()
        mock_client.get_role.side_effect = _create_client_error("NoSuchEntity")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        with pytest.raises(pytest.fail.Exception):
            test_func(None, mock_client, mock_request)


class TestKmsPolicyExecution:
    """Tests that execute KMS policy test."""

    def test_lambda_role_has_kms_policy_calls_helper(self):
        """test_lambda_role_has_kms_policy calls check_lambda_role_has_policy."""
        test_func = create_kms_policy_test("role_name_fixture")
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["KMSDecrypt"]
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        result = test_func(None, mock_client, mock_request)
        assert result is None

    def test_lambda_role_has_kms_policy_fails_when_policy_missing(self):
        """test_lambda_role_has_kms_policy fails when policy not attached."""
        test_func = create_kms_policy_test("role_name_fixture")
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["OtherPolicy"]
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        with pytest.raises(AssertionError):
            test_func(None, mock_client, mock_request)
