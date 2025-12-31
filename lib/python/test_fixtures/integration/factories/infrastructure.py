"""Infrastructure test factory functions for ECS, SQS, WWW, EC2, CloudWatch."""
from botocore.exceptions import ClientError
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output


def create_ecs_runner_outputs_tests():
    """Create tests for ECS runner terraform outputs existence.

    Tests that ecs_runner terraform outputs are accessible.
    Requires `ecs_runner_outputs` fixture.

    Returns:
        Test class with ECS runner output tests
    """

    class TestECSRunnerOutputs:
        """Verify ecs_runner terraform outputs are accessible."""

        def test_task_definition_arn_output_exists(self, ecs_runner_outputs):
            """Verify task_definition_arn output is available."""
            assert ecs_runner_outputs.get("task_definition_arn"), (
                "task_definition_arn output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

        def test_cluster_arn_output_exists(self, ecs_runner_outputs):
            """Verify cluster_arn output is available."""
            assert ecs_runner_outputs.get("cluster_arn"), (
                "cluster_arn output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

        def test_cluster_name_output_exists(self, ecs_runner_outputs):
            """Verify cluster_name output is available."""
            assert ecs_runner_outputs.get("cluster_name"), (
                "cluster_name output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

        def test_lambda_function_name_output_exists(self, ecs_runner_outputs):
            """Verify lambda_function_name output is available."""
            assert ecs_runner_outputs.get("lambda_function_name"), (
                "lambda_function_name output not found in ecs_runner. "
                "Run terraform apply in src/api/endpoints/ecs_runner/"
            )

    return TestECSRunnerOutputs


def create_ecs_runner_lambda_existence_tests():
    """Create tests for ECS runner Lambda function existence.

    Used by endpoints that depend on the ECS runner Lambda function.
    Requires `lambda_client` and `ecs_runner_outputs` fixtures.

    Returns:
        Test class with ECS runner Lambda existence tests
    """

    class TestECSRunnerLambdaExistence:
        """Verify the ECS runner Lambda function exists in AWS."""

        def test_lambda_function_exists(self, lambda_client, ecs_runner_outputs):
            """Verify the ECS runner Lambda function exists."""
            function_name = ecs_runner_outputs.get("lambda_function_name")
            if not function_name:
                pytest.skip("lambda_function_name output not available")
            try:
                lambda_client.get_function(FunctionName=function_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda function '{function_name}' does not exist. "
                        "Run terraform apply in src/api/endpoints/ecs_runner/"
                    )
                raise

        def test_lambda_function_is_active(self, lambda_client, ecs_runner_outputs):
            """Verify the ECS runner Lambda function is active."""
            function_name = ecs_runner_outputs.get("lambda_function_name")
            if not function_name:
                pytest.skip("lambda_function_name output not available")
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                state = response["Configuration"]["State"]
                assert state == "Active", (
                    f"Lambda function '{function_name}' is not active (state: {state}). "
                    "Check Lambda function configuration."
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.skip("Lambda function does not exist")
                raise

    return TestECSRunnerLambdaExistence


def create_www_common_fixtures(
    include_cloudfront: bool = False,
    include_website_domain: bool = False,
):
    """Create www_common terraform fixtures.

    Creates fixtures for accessing www_common terraform outputs including
    bucket information and optionally CloudFront/website domain info.

    Args:
        include_cloudfront: Include CloudFront distribution ID in outputs
        include_website_domain: Include website domain name in outputs

    Returns:
        Tuple of (www_common_terraform_initialized, www_common_outputs) fixtures
    """
    www_common_dir = REPO_ROOT / "src" / "www" / "common"

    @pytest.fixture(scope="session")
    def www_common_terraform_initialized():
        """Initialize terraform for www_common state access."""
        return terraform_init(www_common_dir)

    @pytest.fixture(scope="session")
    def www_common_outputs(request):
        """Get www_common terraform outputs."""
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


def create_www_common_s3_existence_tests():
    """Create S3 bucket existence tests for www_common.

    Creates a test class that verifies the www_common S3 bucket exists.
    Requires `s3_client` and `www_common_outputs` fixtures.

    Returns:
        Test class with S3 bucket existence tests
    """

    class TestWWWCommonS3Existence:
        """Verify www_common S3 bucket exists."""

        def test_bucket_name_output_exists(self, www_common_outputs):
            """Verify bucket_name output is available."""
            assert www_common_outputs.get("bucket_name"), (
                "bucket_name output not found in www_common. "
                "Run terraform apply in src/www/common/"
            )

        def test_s3_bucket_exists(self, s3_client, www_common_outputs):
            """Verify the S3 bucket exists in AWS."""
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


def create_sqs_fifo_queue_tests(
    queue_name_fixture: str,
    queue_description: str = "queue",
    fail_on_missing: bool = False,
):
    """Create SQS FIFO queue configuration tests.

    Creates a test class that verifies an SQS queue is properly
    configured as a FIFO queue with content-based deduplication.

    Args:
        queue_name_fixture: Name of the fixture providing the queue name
        queue_description: Human-readable description (e.g., "webhook queue", "DLQ")
        fail_on_missing: If True, fail when queue doesn't exist; if False, skip

    Returns:
        Test class with SQS FIFO queue tests
    """

    class TestSQSFIFOQueue:
        """Verify SQS queue is configured as FIFO with deduplication."""

        def test_queue_exists(self, sqs_client, request):
            """Verify the FIFO queue exists."""
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

        def test_queue_is_fifo(self, sqs_client, request):
            """Verify the queue is configured as FIFO."""
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
                attrs = sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=["FifoQueue"]
                )

                fifo_attr = attrs.get("Attributes", {}).get("FifoQueue")
                assert fifo_attr == "true", (
                    f"{queue_description} {queue_name} FifoQueue attribute is "
                    f"'{fifo_attr}', expected 'true'"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    pytest.skip(f"{queue_description} {queue_name} not deployed yet")
                raise

        def test_queue_has_deduplication(self, sqs_client, request):
            """Verify the queue has content-based deduplication enabled."""
            queue_name = request.getfixturevalue(queue_name_fixture)
            try:
                queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
                attrs = sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=["ContentBasedDeduplication"]
                )

                dedup_attr = attrs.get("Attributes", {}).get("ContentBasedDeduplication")
                assert dedup_attr == "true", (
                    f"{queue_description} {queue_name} ContentBasedDeduplication is "
                    f"'{dedup_attr}', expected 'true'"
                )
            except ClientError as err:
                if err.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    pytest.skip(f"{queue_description} {queue_name} not deployed yet")
                raise

    return TestSQSFIFOQueue


def handle_ecr_error(error: ClientError, operation: str, repository_name: str) -> None:
    """Handle common ECR ClientError patterns.

    Args:
        error: The ClientError that was raised
        operation: ECR operation name (e.g., "ecr:ListImages")
        repository_name: Name of the ECR repository

    Raises:
        pytest.skip: If repository doesn't exist
        pytest.fail: If access is denied
        ClientError: Re-raises for other error codes
    """
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
    sg_id_key: str = "runner_security_group_id",
    terraform_path: str = "src/api/common/networking",
):
    """Create a security group existence test method.

    Args:
        outputs_fixture: Name of the fixture providing terraform outputs
        sg_id_key: Key in outputs containing the security group ID
        terraform_path: Path to show in error message for terraform apply

    Returns:
        Test method that checks security group exists
    """
    def test_security_group_exists(_self, ec2_client, request):
        """Verify the security group exists."""
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
):
    """Create CloudWatch log group configuration tests.

    Args:
        log_group_fixture: Name of the log group fixture
        expected_retention: Expected retention period in days

    Returns:
        Test class with log group configuration tests
    """

    class TestCloudWatchLogsConfiguration:
        """Layer 2: Verify CloudWatch log group is configured correctly."""

        def test_handler_log_group_has_retention_set(self, request):
            """Verify log group has retention period set."""
            log_group = request.getfixturevalue(log_group_fixture)
            assert log_group["retention"] is not None, (
                f"Log group '{log_group['name']}' should have retention set"
            )

        def test_handler_log_group_retention_is_expected(self, request):
            """Verify log group retention is expected value."""
            log_group = request.getfixturevalue(log_group_fixture)
            retention = log_group["retention"]
            assert retention == expected_retention, (
                f"Log group retention should be {expected_retention} days, got: {retention}"
            )

    return TestCloudWatchLogsConfiguration
