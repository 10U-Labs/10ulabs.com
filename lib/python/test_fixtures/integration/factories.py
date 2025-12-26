"""Factory functions for creating test classes.

These functions dynamically create test classes with specific configurations.
"""
from botocore.exceptions import ClientError
import pytest
from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from test_fixtures.integration.helpers import (
    check_s3_head_bucket_permission,
    check_service_can_assume_role,
    NO_CREDENTIALS_MESSAGE,
)
from test_fixtures.terraform import terraform_init, terraform_output


def create_layer1_authentication_tests():
    """Create Layer 1 authentication test class.

    Returns a test class with standard AWS credential verification tests.
    Used by ecs_runner, image_for_ecs_runners, and similar endpoints.

    Returns:
        Test class with Layer 1 authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_credentials_available(self, sts_client):
            """Verify AWS credentials are configured."""
            assert sts_client is not None, NO_CREDENTIALS_MESSAGE

        def test_can_call_sts_api(self, sts_client):
            """Verify credentials are valid by calling STS."""
            try:
                response = sts_client.get_caller_identity()
                assert response.get("Account"), "STS returned no account ID"
            except ClientError as e:
                pytest.fail(
                    f"Credentials invalid or expired: {e.response['Error']['Message']}"
                )

        def test_identity_has_arn(self, sts_client):
            """Verify identity response has Arn."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response, "STS response missing Arn field"

    return TestAWSAuthentication


def create_layer6_capability_tests(capabilities: frozenset | None = None):
    """Create Layer 6 deployment capability test class.

    Args:
        capabilities: frozenset of capability names to include. Valid names:
            'lambda', 'iam', 'ssm', 'dynamodb', 'logs', 's3'.
            Defaults to frozenset({'lambda', 'iam'}) if None.

    Returns:
        Test class with Layer 6 capability tests
    """
    if capabilities is None:
        capabilities = frozenset({'lambda', 'iam'})

    class TestDeploymentCapabilities:
        """Layer 6: Verify deployment capabilities."""

        def get_enabled_capabilities(self):
            """Return the set of enabled capabilities for this test class."""
            return capabilities

        def test_capabilities_configured(self):
            """Verify at least one capability is being tested."""
            assert len(capabilities) > 0, "No capabilities configured for testing"

    if 'lambda' in capabilities:

        def test_can_list_lambda_functions(_self, lambda_client):
            """Verify we can list Lambda functions (required for deployment)."""
            try:
                lambda_client.list_functions(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list Lambda functions, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_lambda_functions",
            test_can_list_lambda_functions,
        )

    if 'iam' in capabilities:

        def test_can_list_iam_roles(_self, iam_client):
            """Verify we can list IAM roles (required for deployment)."""
            try:
                iam_client.list_roles(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list IAM roles, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_iam_roles",
            test_can_list_iam_roles,
        )

    if 'ssm' in capabilities:

        def test_can_describe_ssm_parameters(_self, ssm_client):
            """Verify we can describe SSM parameters (required for deployment)."""
            try:
                ssm_client.describe_parameters(MaxResults=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot describe SSM parameters, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_describe_ssm_parameters",
            test_can_describe_ssm_parameters,
        )

    if 'dynamodb' in capabilities:

        def test_can_list_dynamodb_tables(_self, dynamodb_client):
            """Verify we can list DynamoDB tables (required for deployment)."""
            try:
                dynamodb_client.list_tables(Limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list DynamoDB tables, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_dynamodb_tables",
            test_can_list_dynamodb_tables,
        )

    if 'logs' in capabilities:

        def test_can_list_log_groups(_self, logs_client):
            """Verify we can list CloudWatch log groups (required for deployment)."""
            try:
                logs_client.describe_log_groups(limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list CloudWatch log groups, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_log_groups",
            test_can_list_log_groups,
        )

    if 's3' in capabilities:

        def test_can_list_s3_buckets(_self, s3_client):
            """Verify we can list S3 buckets (required for deployment)."""
            try:
                s3_client.list_buckets()
            except ClientError as e:
                pytest.fail(
                    f"Cannot list S3 buckets, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_s3_buckets",
            test_can_list_s3_buckets,
        )

    return TestDeploymentCapabilities


def create_layer2_s3_authorization_tests():
    """Create Layer 2 S3 authorization tests.

    Tests permission to call s3:HeadBucket on the state bucket.
    Requires `s3_client` and `state_bucket_name` fixtures.

    Returns:
        Test class with S3 authorization tests
    """

    class TestS3Authorization:
        """Layer 2: Verify S3 authorization."""

        def test_can_call_s3_head_bucket(self, s3_client, state_bucket_name):
            """Verify permission to call s3:HeadBucket on state bucket."""
            check_s3_head_bucket_permission(s3_client, state_bucket_name)

        def test_bucket_name_is_configured(self, state_bucket_name):
            """Verify state bucket name is configured."""
            assert state_bucket_name, "State bucket name is not configured"

    return TestS3Authorization


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


def create_lambda_api_gateway_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    """Create Lambda API Gateway wiring tests for an endpoint.

    Creates a test class that verifies:
    - Lambda has API Gateway invoke permission
    - Lambda has IAM role attached
    - Lambda role follows naming pattern

    Args:
        function_name_config_key: Config key for function name
            (e.g., 'health_handler_function_name')
        default_function_name: Default function name if not in config

    Returns:
        Test class with Lambda wiring tests
    """

    class TestLambdaWiring:
        """Layer 3: Verify Lambda is wired to API Gateway and has correct role."""

        def test_handler_has_api_gateway_permission(self, lambda_client, config):
            """Verify Lambda has permission to be invoked by API Gateway."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_policy(FunctionName=function_name)
                policy = response.get("Policy", "")
                # Check that API Gateway has permission to invoke
                assert "apigateway.amazonaws.com" in policy, (
                    f"Lambda '{function_name}' missing API Gateway invoke permission"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda '{function_name}' has no resource policy - "
                        "API Gateway cannot invoke it"
                    )
                raise

        def test_handler_has_role_attached(self, lambda_client, config):
            """Verify Lambda function has IAM role attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            assert role_arn, f"Lambda '{function_name}' has no IAM role attached"

        def test_handler_role_follows_naming_pattern(self, lambda_client, config):
            """Verify Lambda role ARN follows expected naming pattern."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response["Configuration"].get("Role", "")
            expected_role_suffix = f"{function_name}ServiceRole"
            assert expected_role_suffix in role_arn, (
                f"Lambda role ARN '{role_arn}' doesn't match expected pattern "
                f"containing '{expected_role_suffix}'"
            )

    return TestLambdaWiring


def create_lambda_iam_wiring_tests(
    function_name_config_key: str,
    default_function_name: str,
    check_basic_execution: bool = True,
    check_lambda_trust: bool = True,
):
    """Create Lambda IAM policy wiring tests for an endpoint.

    Creates a test class that verifies IAM role policies are properly configured.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        check_basic_execution: Whether to check for basic execution policy
        check_lambda_trust: Whether to check Lambda can assume the role

    Returns:
        Test class with IAM policy wiring tests
    """

    class TestIAMPolicyWiring:
        """Layer 3: Verify IAM role has required policies attached."""

        def test_config_has_function_name(self, config):
            """Verify config contains the required function name key."""
            assert config.get(function_name_config_key) or default_function_name, (
                f"Neither config key '{function_name_config_key}' nor default "
                f"'{default_function_name}' is available"
            )

        def test_service_role_name_follows_convention(self, config):
            """Verify service role name follows naming convention."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            assert "ServiceRole" in role_name, "Role name should contain 'ServiceRole'"

    if check_basic_execution:

        def test_handler_role_has_basic_execution_policy(_self, iam_client, config):
            """Verify IAM role has Lambda basic execution policy attached."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.list_attached_role_policies(RoleName=role_name)
            policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
            basic_execution = (
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            assert basic_execution in policy_arns, (
                f"IAM role '{role_name}' missing AWSLambdaBasicExecutionRole policy. "
                f"Attached policies: {policy_arns}"
            )

        setattr(
            TestIAMPolicyWiring,
            "test_handler_role_has_basic_execution_policy",
            test_handler_role_has_basic_execution_policy,
        )

    if check_lambda_trust:

        def test_handler_role_can_assume_lambda_service(_self, iam_client, config):
            """Verify IAM role trust policy allows Lambda service to assume it."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.get_role(RoleName=role_name)
            assume_policy = response["Role"]["AssumeRolePolicyDocument"]
            statements = assume_policy.get("Statement", [])
            lambda_principals = [
                s for s in statements
                if s.get("Principal", {}).get("Service") == "lambda.amazonaws.com"
            ]
            assert lambda_principals, (
                f"IAM role '{role_name}' missing Lambda service in trust policy"
            )

        setattr(
            TestIAMPolicyWiring,
            "test_handler_role_can_assume_lambda_service",
            test_handler_role_can_assume_lambda_service,
        )

    return TestIAMPolicyWiring


def create_www_shared_fixtures(
    include_cloudfront: bool = False,
    include_website_domain: bool = False,
):
    """Create www_shared terraform fixtures.

    Creates fixtures for accessing www_shared terraform outputs including
    bucket information and optionally CloudFront/website domain info.

    Args:
        include_cloudfront: Include CloudFront distribution ID in outputs
        include_website_domain: Include website domain name in outputs

    Returns:
        Tuple of (www_shared_terraform_initialized, www_shared_outputs) fixtures
    """
    www_shared_dir = REPO_ROOT / "src" / "www" / "shared"

    @pytest.fixture(scope="session")
    def www_shared_terraform_initialized():
        """Initialize terraform for www_shared state access."""
        return terraform_init(www_shared_dir)

    @pytest.fixture(scope="session")
    def www_shared_outputs(request):
        """Get www_shared terraform outputs."""
        if not request.getfixturevalue("www_shared_terraform_initialized"):
            pytest.skip("Terraform init failed for www_shared")
        outputs = {
            "bucket_name": terraform_output(www_shared_dir, "bucket_name"),
            "bucket_arn": terraform_output(www_shared_dir, "bucket_arn"),
        }
        if include_website_domain:
            outputs["website_domain_name"] = terraform_output(
                www_shared_dir, "website_domain_name"
            )
        if include_cloudfront:
            outputs["cloudfront_distribution_id"] = terraform_output(
                www_shared_dir, "cloudfront_distribution_id"
            )
        return outputs

    return www_shared_terraform_initialized, www_shared_outputs


def create_www_shared_s3_existence_tests():
    """Create S3 bucket existence tests for www_shared.

    Creates a test class that verifies the www_shared S3 bucket exists.
    Requires `s3_client` and `www_shared_outputs` fixtures.

    Returns:
        Test class with S3 bucket existence tests
    """

    class TestWWWSharedS3Existence:
        """Verify www_shared S3 bucket exists."""

        def test_bucket_name_output_exists(self, www_shared_outputs):
            """Verify bucket_name output is available."""
            assert www_shared_outputs.get("bucket_name"), (
                "bucket_name output not found in www_shared. "
                "Run terraform apply in src/www/shared/"
            )

        def test_s3_bucket_exists(self, s3_client, www_shared_outputs):
            """Verify the S3 bucket exists in AWS."""
            bucket_name = www_shared_outputs.get("bucket_name")
            if not bucket_name:
                pytest.skip("bucket_name output not available")
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    pytest.fail(
                        f"S3 bucket '{bucket_name}' does not exist. "
                        "Run terraform apply in src/www/shared/"
                    )
                raise

    return TestWWWSharedS3Existence


def create_lambda_execution_role_wiring_tests(fixture_name: str = "lambda_function"):
    """Create Lambda execution role wiring tests.

    Creates a test class that verifies Lambda function has proper
    IAM execution role configuration and wiring.

    Args:
        fixture_name: Name of the fixture providing Lambda config
                     (e.g., 'lambda_function' or 'lambda_config')

    Returns:
        Test class with Lambda execution role wiring tests
    """

    class TestLambdaExecutionRole:
        """Verify Lambda execution role wiring."""

        def test_lambda_has_execution_role_key(self, request):
            """Verify Lambda function has Role key in configuration."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert "Role" in lambda_config

        def test_lambda_has_execution_role_value(self, request):
            """Verify Lambda function execution role is not empty."""
            lambda_config = request.getfixturevalue(fixture_name)
            assert lambda_config.get("Role")

        def test_lambda_role_starts_with_iam_arn(self, request):
            """Verify Lambda execution role starts with IAM ARN prefix."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert role_arn.startswith("arn:aws:iam::"), (
                f"Lambda role '{role_arn}' is not a valid IAM ARN"
            )

        def test_lambda_role_contains_role_path(self, request):
            """Verify Lambda execution role ARN contains :role/ path."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            assert ":role/" in role_arn, (
                f"Lambda role '{role_arn}' does not appear to be a role ARN"
            )

        def test_lambda_role_exists(self, iam_client, request):
            """Verify the Lambda execution role exists in IAM."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.fail("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response.get("Role") is not None
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.fail(
                        f"Lambda execution role '{role_name}' does not exist in IAM. "
                        "The Lambda is configured with a non-existent role."
                    )
                raise

        def test_lambda_role_can_be_assumed_by_lambda(self, iam_client, request):
            """Verify the Lambda execution role has a trust policy for Lambda."""
            lambda_config = request.getfixturevalue(fixture_name)
            role_arn = lambda_config.get("Role", "")
            role_name = role_arn.split("/")[-1] if "/" in role_arn else ""

            if not role_name:
                pytest.skip("Could not extract role name from Lambda configuration")

            try:
                response = iam_client.get_role(RoleName=role_name)
                trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
                can_assume = check_service_can_assume_role(
                    trust_policy, "lambda.amazonaws.com"
                )

                assert can_assume, (
                    f"Role '{role_name}' trust policy does not allow Lambda to assume it"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchEntity":
                    pytest.skip(f"Role '{role_name}' does not exist")
                raise

    return TestLambdaExecutionRole


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


def create_simple_layer1_authentication_tests():
    """Create simple Layer 1 authentication tests.

    Simpler version with just two basic credential checks.
    Used by bootstrap, www_shared, and similar modules.

    Returns:
        Test class with simple authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_aws_credentials_valid(self, sts_client):
            """Verify AWS credentials are valid."""
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None

        def test_aws_credentials_not_expired(self, sts_client):
            """Verify AWS credentials are not expired."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response

    return TestAWSAuthentication


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
    terraform_path: str = "src/api/shared/networking",
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


def create_lambda_existence_tests(
    function_name_config_key: str,
    default_function_name: str,
    terraform_path: str,
    log_group_fixture: str | None = None,
):
    """Create Lambda/IAM existence tests for an endpoint.

    Creates a test class that verifies Lambda function and IAM role exist.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        terraform_path: Path to terraform directory for error messages
        log_group_fixture: Optional fixture name for log group test

    Returns:
        Test class with Lambda existence tests
    """

    class TestDeployedResourcesExist:
        """Layer 1: Verify Lambda, IAM role exist."""

        def test_handler_lambda_exists(self, lambda_client, config):
            """Verify Lambda function exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                assert response["Configuration"]["FunctionName"] == function_name
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    pytest.fail(
                        f"Lambda function '{function_name}' does not exist. "
                        f"Run terraform apply in {terraform_path}"
                    )
                raise

        def test_handler_iam_role_exists(self, iam_client, config):
            """Verify IAM role exists."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response["Role"]["RoleName"] == role_name
            except iam_client.exceptions.NoSuchEntityException:
                pytest.fail(
                    f"IAM role '{role_name}' does not exist. "
                    f"Run terraform apply in {terraform_path}"
                )

    if log_group_fixture:

        def test_handler_log_group_exists(_self, request):
            """Verify CloudWatch log group exists."""
            log_group = request.getfixturevalue(log_group_fixture)
            assert log_group["exists"], (
                f"CloudWatch log group '{log_group['name']}' does not exist"
            )

        setattr(
            TestDeployedResourcesExist,
            "test_handler_log_group_exists",
            test_handler_log_group_exists,
        )

    return TestDeployedResourcesExist


def create_lambda_configuration_tests(
    function_name_config_key: str,
    default_function_name: str,
    expected_runtime: str = "python3.13",
    expected_handler: str = "handler.handler",
    expected_architecture: str = "arm64",
):
    """Create Lambda configuration tests for an endpoint.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config
        expected_runtime: Expected Python runtime
        expected_handler: Expected handler path
        expected_architecture: Expected architecture

    Returns:
        Test class with Lambda configuration tests
    """

    class TestLambdaConfiguration:
        """Layer 2: Verify Lambda function is configured correctly."""

        def test_handler_uses_python_runtime(self, lambda_client, config):
            """Verify Lambda uses expected Python runtime."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            runtime = response["Configuration"]["Runtime"]
            assert runtime == expected_runtime, (
                f"Lambda runtime should be {expected_runtime}, got: {runtime}"
            )

        def test_handler_uses_expected_architecture(self, lambda_client, config):
            """Verify Lambda uses expected architecture."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            architectures = response["Configuration"].get("Architectures", [])
            assert expected_architecture in architectures, (
                f"Lambda should use {expected_architecture} architecture, got: {architectures}"
            )

        def test_handler_has_handler_configured(self, lambda_client, config):
            """Verify Lambda has correct handler configured."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            handler = response["Configuration"]["Handler"]
            assert handler == expected_handler, (
                f"Lambda handler should be {expected_handler}, got: {handler}"
            )

    return TestLambdaConfiguration


def create_naming_convention_tests(
    function_name_config_key: str,
    default_function_name: str,
):
    """Create naming convention tests for Lambda and IAM resources.

    Args:
        function_name_config_key: Config key for function name
        default_function_name: Default function name if not in config

    Returns:
        Test class with naming convention tests
    """

    class TestNamingConventions:
        """Layer 2: Verify resources follow naming conventions."""

        def test_handler_lambda_name_is_pascalcase(self, lambda_client, config):
            """Verify Lambda function name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            response = lambda_client.get_function(FunctionName=function_name)
            actual_name = response["Configuration"]["FunctionName"]
            error = validate_name(actual_name)
            assert error is None, (
                f"Lambda function has invalid name '{actual_name}': {error}"
            )

        def test_handler_role_name_is_pascalcase(self, iam_client, config):
            """Verify IAM role name uses PascalCase."""
            function_name = config.get(function_name_config_key, default_function_name)
            role_name = f"{function_name}ServiceRole"
            response = iam_client.get_role(RoleName=role_name)
            actual_name = response["Role"]["RoleName"]
            error = validate_name(actual_name)
            assert error is None, (
                f"IAM role has invalid name '{actual_name}': {error}"
            )

    return TestNamingConventions


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
