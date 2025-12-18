"""Layer 3: Existence - Do the required resources exist?

These tests verify that all required infrastructure resources exist before
checking their configuration. Organized by resource type for clarity.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist? (THIS FILE)
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""
from pathlib import Path

from botocore.exceptions import ClientError
import pytest

from terraform_config import extract_sqs_queue_names


RUNNERS_SRC = Path(__file__).parents[6] / "src" / "api" / "endpoints" / "runners"
SQS_TF_FILE = RUNNERS_SRC / "sqs.tf"


# =============================================================================
# Terraform Outputs Existence
# =============================================================================


class TestApiSharedRunnersOutputs:
    """Layer 3: Verify api_shared_runners terraform outputs are accessible."""

    def test_01_vpc_id_output_exists(self, api_shared_runners_outputs):
        """Verify vpc_id output exists."""
        assert api_shared_runners_outputs.get("vpc_id"), (
            "vpc_id output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )

    def test_02_subnet_ids_output_exists(self, api_shared_runners_outputs):
        """Verify vpc_public_subnet_ids output exists."""
        assert api_shared_runners_outputs.get("vpc_public_subnet_ids"), (
            "vpc_public_subnet_ids output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )

    def test_03_security_group_id_output_exists(self, api_shared_runners_outputs):
        """Verify runner_security_group_id output exists."""
        assert api_shared_runners_outputs.get("runner_security_group_id"), (
            "runner_security_group_id output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )


class TestApiSharedEcsRunnerOutputs:
    """Layer 3: Verify api_shared_ecs_runner terraform outputs are accessible."""

    def test_01_ecr_repository_arn_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_arn output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_arn"), (
            "ecr_repository_arn output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )

    def test_02_ecr_repository_name_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_name output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_name"), (
            "ecr_repository_name output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )

    def test_03_ecr_repository_url_output_exists(self, api_shared_ecs_runner_outputs):
        """Verify ecr_repository_url output exists."""
        assert api_shared_ecs_runner_outputs.get("ecr_repository_url"), (
            "ecr_repository_url output not found in api_shared_ecs_runner. "
            "Run: cd src/api/shared/ecs_runner && terraform apply"
        )


class TestEC2RunnerOutputs:
    """Layer 3: Verify ec2_runner terraform outputs are accessible."""

    def test_01_lambda_function_arn_output_exists(self, ec2_runner_outputs):
        """Verify ec2_runner has lambda_function_arn output."""
        assert ec2_runner_outputs.get("lambda_function_arn"), \
            "lambda_function_arn output not found in ec2_runner"

    def test_02_lambda_function_name_output_exists(self, ec2_runner_outputs):
        """Verify ec2_runner has lambda_function_name output."""
        assert ec2_runner_outputs.get("lambda_function_name"), \
            "lambda_function_name output not found in ec2_runner"

    def test_03_lambda_invoke_arn_output_exists(self, ec2_runner_outputs):
        """Verify ec2_runner has lambda_invoke_arn output."""
        assert ec2_runner_outputs.get("lambda_invoke_arn"), \
            "lambda_invoke_arn output not found in ec2_runner"


class TestECSRunnerOutputs:
    """Layer 3: Verify ecs_runner terraform outputs are accessible."""

    def test_01_lambda_function_arn_output_exists(self, ecs_runner_outputs):
        """Verify ecs_runner has lambda_function_arn output."""
        assert ecs_runner_outputs.get("lambda_function_arn"), \
            "lambda_function_arn output not found in ecs_runner"

    def test_02_lambda_function_name_output_exists(self, ecs_runner_outputs):
        """Verify ecs_runner has lambda_function_name output."""
        assert ecs_runner_outputs.get("lambda_function_name"), \
            "lambda_function_name output not found in ecs_runner"

    def test_03_cluster_arn_output_exists(self, ecs_runner_outputs):
        """Verify ecs_runner has cluster_arn output."""
        assert ecs_runner_outputs.get("cluster_arn"), \
            "cluster_arn output not found in ecs_runner"

    def test_04_cluster_name_output_exists(self, ecs_runner_outputs):
        """Verify ecs_runner has cluster_name output."""
        assert ecs_runner_outputs.get("cluster_name"), \
            "cluster_name output not found in ecs_runner"


# =============================================================================
# AWS Resource Existence
# =============================================================================


class TestVPCResourceExistence:
    """Layer 3: Verify VPC resources exist in AWS."""

    def test_01_vpc_exists(self, vpc_info, api_shared_runners_outputs):
        """Verify the VPC exists."""
        vpc_id = api_shared_runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        assert vpc_info is not None, (
            f"VPC {vpc_id} not found. "
            "Run: cd src/api/shared/runners && terraform apply"
        )

    def test_02_subnets_exist(self, subnets_info, api_shared_runners_outputs):
        """Verify all subnets exist."""
        subnet_ids_str = api_shared_runners_outputs.get("vpc_public_subnet_ids")
        if not subnet_ids_str:
            pytest.skip("vpc_public_subnet_ids output not available")
        subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
        assert len(subnets_info) == len(subnet_ids), (
            f"Expected {len(subnet_ids)} subnets, found {len(subnets_info)}. "
            "Some subnets may have been deleted."
        )

    def test_03_security_group_exists(self, ec2_client, api_shared_runners_outputs):
        """Verify the security group exists."""
        sg_id = api_shared_runners_outputs.get("runner_security_group_id")
        if not sg_id:
            pytest.skip("runner_security_group_id output not available")
        try:
            response = ec2_client.describe_security_groups(GroupIds=[sg_id])
            assert len(response["SecurityGroups"]) == 1, (
                f"Security group {sg_id} not found."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.fail(
                    f"Security group {sg_id} does not exist. "
                    "Run: cd src/api/shared/runners && terraform apply"
                )
            raise


def test_ecr_repository_exists(ecr_repository_info, api_shared_ecs_runner_outputs):
    """Verify the ECR repository exists."""
    repo_name = api_shared_ecs_runner_outputs.get("ecr_repository_name")
    if not repo_name:
        pytest.skip("ecr_repository_name output not available")
    assert ecr_repository_info is not None, (
        f"ECR repository '{repo_name}' not found. "
        "Run: cd src/api/shared/ecs_runner && terraform apply"
    )


class TestLambdaResourceExistence:
    """Layer 3: Verify Lambda functions exist in AWS."""

    def test_01_ec2_runner_lambda_exists(self, lambda_client, ec2_runner_outputs):
        """Verify the EC2 runner Lambda function exists."""
        function_name = ec2_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        response = lambda_client.get_function(FunctionName=function_name)
        assert response["Configuration"]["FunctionName"] == function_name

    def test_02_ecs_runner_lambda_exists(self, lambda_client, ecs_runner_outputs):
        """Verify the ECS runner Lambda function exists."""
        function_name = ecs_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        response = lambda_client.get_function(FunctionName=function_name)
        assert response["Configuration"]["FunctionName"] == function_name


class TestSSMResourceExistence:
    """Layer 3: Verify SSM parameters exist in AWS."""

    def test_01_github_pat_parameter_exists(self, ssm_client, ssm_github_pat_name):
        """Verify the GitHub PAT SSM parameter exists."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=False
            )
            assert response.get("Parameter") is not None, (
                f"SSM parameter '{ssm_github_pat_name}' returned empty response."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{ssm_github_pat_name}' does not exist. "
                    "This parameter must be created manually with a valid GitHub PAT."
                )
            raise

    def test_02_github_pat_parameter_has_value(self, ssm_client, ssm_github_pat_name):
        """Verify the GitHub PAT SSM parameter has a non-empty value."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=True
            )
            value = response.get("Parameter", {}).get("Value", "")
            assert value, (
                f"SSM parameter '{ssm_github_pat_name}' exists but has empty value. "
                "Update the parameter with a valid GitHub PAT."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            if code == "AccessDeniedException":
                pytest.skip("No permission to decrypt - checking existence only")
            raise


# =============================================================================
# Terraform Configuration Existence (pre-deployment validation)
# =============================================================================


class TestSQSTerraformConfigExistence:
    """Layer 3: Verify SQS queue definitions exist in Terraform config."""

    def test_01_sqs_tf_file_exists(self):
        """Verify sqs.tf file exists in runners endpoint."""
        assert SQS_TF_FILE.exists(), (
            f"sqs.tf not found at {SQS_TF_FILE}. "
            "The runners endpoint requires SQS queue definitions."
        )

    def test_02_sqs_queues_extractable(self):
        """Verify SQS queue names can be extracted from sqs.tf."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        assert len(queues) > 0, (
            "No SQS queue definitions found in sqs.tf. "
            "Expected at least one aws_sqs_queue resource."
        )

    def test_03_webhook_ingress_queue_defined(self):
        """Verify webhook_ingress queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "webhook_ingress" in queue_resources, (
            "webhook_ingress queue not found in sqs.tf. "
            "Required for API Gateway -> SQS direct integration."
        )

    def test_04_webhook_ingress_dlq_defined(self):
        """Verify webhook_ingress_dlq is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "webhook_ingress_dlq" in queue_resources, (
            "webhook_ingress_dlq not found in sqs.tf. "
            "Required for failed webhook ingress message handling."
        )

    def test_05_ignored_events_queue_defined(self):
        """Verify ignored_events queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "ignored_events" in queue_resources, (
            "ignored_events queue not found in sqs.tf. "
            "Required for storing unhandled webhook events."
        )

    def test_06_job_queue_defined(self):
        """Verify job_queue is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "job_queue" in queue_resources, (
            "job_queue not found in sqs.tf. "
            "Required for workflow_job queued event handling."
        )
