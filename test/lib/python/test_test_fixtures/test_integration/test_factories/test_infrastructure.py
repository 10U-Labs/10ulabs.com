from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
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


def _create_nonexistent_queue_mocks():
    mock_client = MagicMock()
    mock_client.get_queue_url.side_effect = create_client_error(
        "AWS.SimpleQueueService.NonExistentQueue"
    )
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-queue.fifo"
    return mock_client, mock_request


def _create_sqs_service_error_mocks():
    mock_client = MagicMock()
    mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
    mock_client.get_queue_attributes.side_effect = create_client_error("ServiceException")
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-queue.fifo"
    return mock_client, mock_request


def _www_common_outputs(monkeypatch, terraform_outputs, **kwargs):
    monkeypatch.setattr(
        "test_fixtures.integration.factories.infrastructure.terraform_output",
        MagicMock(side_effect=terraform_outputs)
    )
    _, outputs_fixture = create_www_common_fixtures(**kwargs)
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = True
    return outputs_fixture.__wrapped__(mock_request)


class TestCreateWwwCommonFixturesReturnsFixtures:
    def test_returns_tuple(self):
        result = create_www_common_fixtures()
        assert isinstance(result, tuple)

    def test_returns_two_fixtures(self):
        result = create_www_common_fixtures()
        assert len(result) == 2

    def test_first_fixture_is_callable(self):
        result = create_www_common_fixtures()
        assert callable(result[0])

    def test_second_fixture_is_callable(self):
        result = create_www_common_fixtures()
        assert callable(result[1])

    def test_first_fixture_has_correct_name(self):
        result = create_www_common_fixtures()
        assert result[0].__name__ == "www_common_terraform_initialized"

    def test_second_fixture_has_correct_name(self):
        result = create_www_common_fixtures()
        assert result[1].__name__ == "www_common_outputs"


class TestCreateWwwCommonFixturesOptions:
    def test_accepts_include_cloudfront(self):
        result = create_www_common_fixtures(include_cloudfront=True)
        assert len(result) == 2

    def test_accepts_include_website_domain(self):
        result = create_www_common_fixtures(include_website_domain=True)
        assert len(result) == 2

    def test_accepts_both_options(self):
        result = create_www_common_fixtures(
            include_cloudfront=True, include_website_domain=True
        )
        assert len(result) == 2


class TestWwwCommonFixturesExecution:
    def test_terraform_initialized_calls_terraform_init(self, monkeypatch):
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

    def test_outputs_returns_bucket_name(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch, ["my-bucket", "arn:aws:s3:::my-bucket"]
        )
        assert "bucket_name" in result

    def test_outputs_returns_bucket_arn(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch, ["my-bucket", "arn:aws:s3:::my-bucket"]
        )
        assert "bucket_arn" in result

    def test_outputs_includes_website_domain_when_requested(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch,
            ["my-bucket", "arn:aws:s3:::my-bucket", "example.com"],
            include_website_domain=True
        )
        assert "website_domain_name" in result

    def test_outputs_includes_cloudfront_when_requested(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch,
            ["my-bucket", "arn:aws:s3:::my-bucket", "E123456789"],
            include_cloudfront=True
        )
        assert "cloudfront_distribution_id" in result

    def test_outputs_includes_website_domain_when_both_requested(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch,
            ["my-bucket", "arn:aws:s3:::my-bucket", "example.com", "E123456789"],
            include_website_domain=True, include_cloudfront=True
        )
        assert "website_domain_name" in result

    def test_outputs_includes_cloudfront_when_both_requested(self, monkeypatch):
        result = _www_common_outputs(
            monkeypatch,
            ["my-bucket", "arn:aws:s3:::my-bucket", "example.com", "E123456789"],
            include_website_domain=True, include_cloudfront=True
        )
        assert "cloudfront_distribution_id" in result


class TestCreateWwwCommonS3ExistenceTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_www_common_s3_existence_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_www_common_s3_existence_tests()
        assert test_class.__name__ == "TestWWWCommonS3Existence"


class TestCreateWwwCommonS3ExistenceTestsHasMethods:
    def test_has_test_bucket_name_output_exists(self):
        test_class = create_www_common_s3_existence_tests()
        assert hasattr(test_class, "test_bucket_name_output_exists")

    def test_has_test_s3_bucket_exists(self):
        test_class = create_www_common_s3_existence_tests()
        assert hasattr(test_class, "test_s3_bucket_exists")


class TestCreateWwwCommonS3ExistenceTestsBucketNameOutput:
    def test_does_not_raise_when_output_exists(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        outputs = {"bucket_name": "my-bucket"}
        assert instance.test_bucket_name_output_exists(outputs) is None

    def test_fails_when_output_missing(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        outputs = {}
        with pytest.raises(AssertionError):
            instance.test_bucket_name_output_exists(outputs)


class TestCreateSqsFifoQueueTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert test_class.__name__ == "TestSQSFIFOQueue"


class TestCreateSqsFifoQueueTestsHasMethods:
    def test_has_test_queue_exists(self):
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_exists")

    def test_has_test_queue_is_fifo(self):
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_is_fifo")

    def test_has_test_queue_has_deduplication(self):
        test_class = create_sqs_fifo_queue_tests("queue_name_fixture")
        assert hasattr(test_class, "test_queue_has_deduplication")


def test_handle_ecr_error_repository_not_found():
    error = create_client_error("RepositoryNotFoundException")
    with pytest.raises(pytest.skip.Exception):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


class TestHandleEcrErrorAccessDenied:
    def test_fails_on_access_denied(self):
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")

    def test_error_message_contains_operation(self):
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="ecr:ListImages"):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")

    def test_error_message_contains_repository_name(self):
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="my-repo"):
            handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_handle_ecr_error_other_errors():
    error = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


class TestCreateSecurityGroupExistenceTestReturnsFunction:
    def test_returns_callable(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        assert callable(test_func)

    def test_returns_function_with_name(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        assert test_func.__name__ == "test_security_group_exists"


class TestCreateLogGroupConfigurationTestsReturnsClass:
    def test_returns_class(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert test_class.__name__ == "TestCloudWatchLogsConfiguration"


class TestCreateLogGroupConfigurationTestsHasMethods:
    def test_has_test_handler_log_group_has_retention_set(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert hasattr(test_class, "test_handler_log_group_has_retention_set")

    def test_has_test_handler_log_group_retention_is_expected(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        assert hasattr(test_class, "test_handler_log_group_retention_is_expected")


class TestCreateLambdaRoleExistenceTestReturnsFunction:
    def test_returns_callable(self):
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        assert callable(test_func)

    def test_returns_function_with_name(self):
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        assert test_func.__name__ == "test_lambda_execution_role_exists"


class TestCreateKmsPolicyTestReturnsFunction:
    def test_returns_callable(self):
        test_func = create_kms_policy_test("role_name_fixture")
        assert callable(test_func)

    def test_returns_function_with_name(self):
        test_func = create_kms_policy_test("role_name_fixture")
        assert test_func.__name__ == "test_lambda_role_has_kms_policy"


class TestWwwCommonS3ExistenceS3BucketExistsExecution:
    def test_s3_bucket_exists_success(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        outputs = {"bucket_name": "my-bucket"}
        assert instance.test_s3_bucket_exists(mock_client, outputs) is None

    def test_s3_bucket_exists_skips_when_no_output(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        outputs = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_s3_bucket_exists(mock_client, outputs)

    def test_s3_bucket_exists_fails_on_404(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("404")
        outputs = {"bucket_name": "my-bucket"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_s3_bucket_exists(mock_client, outputs)

    def test_s3_bucket_exists_reraises_other_errors(self):
        test_class = create_www_common_s3_existence_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("500")
        outputs = {"bucket_name": "my-bucket"}
        with pytest.raises(ClientError):
            instance.test_s3_bucket_exists(mock_client, outputs)


class TestSqsFifoQueueTestsExecution:
    def test_queue_exists_success(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        assert instance.test_queue_exists(mock_client, mock_request) is None

    def test_queue_exists_skips_on_non_existent(self):
        test_class = create_sqs_fifo_queue_tests("queue_name", fail_on_missing=False)
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_exists_fails_on_non_existent_when_fail_on_missing(self):
        test_class = create_sqs_fifo_queue_tests("queue_name", fail_on_missing=True)
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = create_client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(pytest.fail.Exception):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_exists_reraises_other_errors(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.side_effect = create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        with pytest.raises(ClientError):
            instance.test_queue_exists(mock_client, mock_request)

    def test_queue_is_fifo_success(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"FifoQueue": "true"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        assert instance.test_queue_is_fifo(mock_client, mock_request) is None

    def test_queue_is_fifo_fails_when_not_fifo(self):
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
        instance = create_sqs_fifo_queue_tests("queue_name")()
        mock_client, mock_request = _create_nonexistent_queue_mocks()
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_is_fifo(mock_client, mock_request)

    def test_queue_has_deduplication_success(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_queue_url.return_value = {"QueueUrl": "https://..."}
        mock_client.get_queue_attributes.return_value = {
            "Attributes": {"ContentBasedDeduplication": "true"}
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-queue.fifo"
        assert instance.test_queue_has_deduplication(mock_client, mock_request) is None

    def test_queue_has_deduplication_fails_when_disabled(self):
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
        instance = create_sqs_fifo_queue_tests("queue_name")()
        mock_client, mock_request = _create_nonexistent_queue_mocks()
        with pytest.raises(pytest.skip.Exception):
            instance.test_queue_has_deduplication(mock_client, mock_request)


class TestSecurityGroupExistenceExecution:
    def test_security_group_exists_success(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.return_value = {"SecurityGroups": [{}]}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
        assert test_func(None, mock_client, mock_request) is None

    def test_security_group_exists_skips_when_no_output(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {}
        with pytest.raises(pytest.skip.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_fails_on_not_found(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = create_client_error(
            "InvalidGroup.NotFound"
        )
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
        with pytest.raises(pytest.fail.Exception):
            test_func(None, mock_client, mock_request)

    def test_security_group_exists_reraises_other_errors(self):
        test_func = create_security_group_existence_test(
            "outputs_fixture", "security_group_id", "src/api/common/routing"
        )
        mock_client = MagicMock()
        mock_client.describe_security_groups.side_effect = create_client_error("ServiceException")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"security_group_id": "sg-123"}
        with pytest.raises(ClientError):
            test_func(None, mock_client, mock_request)


class TestLogGroupConfigurationExecution:
    def test_log_group_has_retention_set_success(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
        assert instance.test_handler_log_group_has_retention_set(mock_request) is None

    def test_log_group_has_retention_set_fails_when_none(self):
        test_class = create_log_group_configuration_tests("log_group_fixture")
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {
            "name": "/aws/lambda/my-func", "retention": None
        }
        with pytest.raises(AssertionError):
            instance.test_handler_log_group_has_retention_set(mock_request)

    def test_log_group_retention_is_expected_success(self):
        test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
        assert instance.test_handler_log_group_retention_is_expected(mock_request) is None

    def test_log_group_retention_is_expected_fails_when_different(self):
        test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
        instance = test_class()
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 30}
        with pytest.raises(AssertionError):
            instance.test_handler_log_group_retention_is_expected(mock_request)


class TestSqsFifoQueueTestsErrorReRaise:
    def test_queue_is_fifo_reraises_other_errors(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client, mock_request = _create_sqs_service_error_mocks()
        with pytest.raises(ClientError):
            instance.test_queue_is_fifo(mock_client, mock_request)

    def test_queue_has_deduplication_reraises_other_errors(self):
        test_class = create_sqs_fifo_queue_tests("queue_name")
        instance = test_class()
        mock_client, mock_request = _create_sqs_service_error_mocks()
        with pytest.raises(ClientError):
            instance.test_queue_has_deduplication(mock_client, mock_request)


class TestLambdaRoleExistenceExecution:
    def test_lambda_execution_role_exists_calls_helper(self):
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        assert test_func(None, mock_client, mock_request) is None
        mock_client.get_role.assert_called_once_with(RoleName="my-role")

    def test_lambda_execution_role_exists_fails_when_role_missing(self):
        test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        with pytest.raises(pytest.fail.Exception):
            test_func(None, mock_client, mock_request)


class TestKmsPolicyExecution:
    def test_lambda_role_has_kms_policy_calls_helper(self):
        test_func = create_kms_policy_test("role_name_fixture")
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["KMSDecrypt"]
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        assert test_func(None, mock_client, mock_request) is None

    def test_lambda_role_has_kms_policy_fails_when_policy_missing(self):
        test_func = create_kms_policy_test("role_name_fixture")
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["OtherPolicy"]
        }
        mock_request = MagicMock()
        mock_request.getfixturevalue.return_value = "my-role"
        with pytest.raises(AssertionError):
            test_func(None, mock_client, mock_request)
