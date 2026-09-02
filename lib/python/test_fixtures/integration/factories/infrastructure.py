from typing import Any, Callable, Dict, Tuple

from botocore.exceptions import ClientError
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.integration.helpers import check_iam_role_exists, check_lambda_role_has_policy
from test_fixtures.terraform import terraform_init, terraform_output


def create_www_common_fixtures(
    include_cloudfront: bool = False,
    include_website_domain: bool = False,
) -> Tuple[Any, Any]:
    www_common_dir = REPO_ROOT / "src" / "www" / "common"

    @pytest.fixture(scope="session")
    def www_common_terraform_initialized() -> bool:
        return terraform_init(www_common_dir)

    @pytest.fixture(scope="session")
    def www_common_outputs(request: pytest.FixtureRequest) -> Dict[str, str]:
        if not request.getfixturevalue("www_common_terraform_initialized"):
            pytest.skip("Terraform init failed for www_common")
        outputs = {
            "bucket_name": terraform_output(www_common_dir, "bucket_name"),
            "bucket_arn": terraform_output(www_common_dir, "bucket_arn"),
        }
        if include_website_domain:
            outputs["website_domain_name"] = terraform_output(
                www_common_dir, "website_domain_name"
            )
        if include_cloudfront:
            outputs["cloudfront_distribution_id"] = terraform_output(
                www_common_dir, "cloudfront_distribution_id"
            )
        return outputs

    return www_common_terraform_initialized, www_common_outputs


def create_www_common_s3_existence_tests() -> type:
    class TestWWWCommonS3Existence:
        def test_bucket_name_output_exists(self, www_common_outputs: Dict[str, str]) -> None:
            assert www_common_outputs.get("bucket_name"), (
                "bucket_name output not found in www_common. "
                "Run terraform apply in src/www/common/"
            )

        def test_s3_bucket_exists(self, s3_client: Any, www_common_outputs: Dict[str, str]) -> None:
            bucket_name = www_common_outputs.get("bucket_name")
            if not bucket_name:
                pytest.skip("bucket_name output not available")
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    pytest.fail(
                        f"S3 bucket '{bucket_name}' does not exist. "
                        "Run terraform apply in src/www/common/"
                    )
                raise

    return TestWWWCommonS3Existence


def _queue_attribute(
    sqs_client: Any,
    queue_name: str,
    attribute: str,
    description: str
) -> Any:
    try:
        queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
        attrs = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=[attribute]
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
            pytest.skip(f"{description} {queue_name} not deployed yet")
        raise
    return attrs.get("Attributes", {}).get(attribute)


def create_sqs_fifo_queue_tests(
    queue_name_fixture: str,
    queue_description: str = "queue",
    fail_on_missing: bool = False,
) -> type:
    class TestSQSFIFOQueue:
        def test_queue_exists(self, sqs_client: Any, request: pytest.FixtureRequest) -> None:
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                response = sqs_client.get_queue_url(QueueName=queue_name)
                assert response.get("QueueUrl"), (
                    f"{queue_description} {queue_name} URL not returned"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    if fail_on_missing:
                        pytest.fail(
                            f"{queue_description} {queue_name} does not exist. "
                            "Deploy the endpoint first."
                        )
                    else:
                        pytest.skip(
                            f"{queue_description} {queue_name} not deployed yet. "
                            "Run terraform apply first."
                        )
                raise

        def test_queue_is_fifo(self, sqs_client: Any, request: pytest.FixtureRequest) -> None:
            queue_name = request.getfixturevalue(queue_name_fixture)
            fifo_attr = _queue_attribute(
                sqs_client, queue_name, "FifoQueue", queue_description
            )
            assert fifo_attr == "true", (
                f"{queue_description} {queue_name} FifoQueue attribute is "
                f"'{fifo_attr}', expected 'true'"
            )

        def test_queue_has_deduplication(
            self,
            sqs_client: Any,
            request: pytest.FixtureRequest
        ) -> None:
            queue_name = request.getfixturevalue(queue_name_fixture)
            dedup_attr = _queue_attribute(
                sqs_client, queue_name, "ContentBasedDeduplication", queue_description
            )
            assert dedup_attr == "true", (
                f"{queue_description} {queue_name} ContentBasedDeduplication is "
                f"'{dedup_attr}', expected 'true'"
            )

    return TestSQSFIFOQueue


def handle_ecr_error(error: ClientError, operation: str, repository_name: str) -> None:
    error_code = error.response["Error"]["Code"]
    if error_code == "RepositoryNotFoundException":
        pytest.skip("Repository does not exist")
    if error_code == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "This is required to manage Docker images."
        )
    raise error


def create_security_group_existence_test(
    outputs_fixture: str,
    sg_id_key: str,
    terraform_path: str,
) -> Callable[..., None]:
    def test_security_group_exists(
        _self: Any,
        ec2_client: Any,
        request: pytest.FixtureRequest
    ) -> None:
        outputs = request.getfixturevalue(outputs_fixture)
        sg_id = outputs.get(sg_id_key)
        if not sg_id:
            pytest.skip(f"{sg_id_key} output not available")
        try:
            response = ec2_client.describe_security_groups(GroupIds=[sg_id])
            assert len(response["SecurityGroups"]) == 1, (
                f"Security group {sg_id} not found."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.fail(
                    f"Security group {sg_id} does not exist. "
                    f"Run: cd {terraform_path} && terraform apply"
                )
            raise
    return test_security_group_exists


def create_log_group_configuration_tests(
    log_group_fixture: str,
    expected_retention: int = 7,
) -> type:
    class TestCloudWatchLogsConfiguration:
        def test_handler_log_group_has_retention_set(self, request: pytest.FixtureRequest) -> None:
            log_group = request.getfixturevalue(log_group_fixture)
            assert log_group["retention"] is not None, (
                f"Log group '{log_group['name']}' should have retention set"
            )

        def test_handler_log_group_retention_is_expected(
            self,
            request: pytest.FixtureRequest
        ) -> None:
            log_group = request.getfixturevalue(log_group_fixture)
            retention = log_group["retention"]
            assert retention == expected_retention, (
                f"Log group retention should be {expected_retention} days, got: {retention}"
            )

    return TestCloudWatchLogsConfiguration


def create_lambda_role_existence_test(
    role_name_fixture: str,
    terraform_path: str
) -> Callable[..., None]:
    def test_lambda_execution_role_exists(
        _self: Any,
        iam_client: Any,
        request: pytest.FixtureRequest
    ) -> None:
        role_name = request.getfixturevalue(role_name_fixture)
        check_iam_role_exists(iam_client, role_name, terraform_path)
    return test_lambda_execution_role_exists


def create_kms_policy_test(role_name_fixture: str) -> Callable[..., None]:
    def test_lambda_role_has_kms_policy(
        _self: Any,
        iam_client: Any,
        request: pytest.FixtureRequest
    ) -> None:
        role_name = request.getfixturevalue(role_name_fixture)
        check_lambda_role_has_policy(iam_client, role_name, "KMSDecrypt")
    return test_lambda_role_has_kms_policy
