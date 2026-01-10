"""Terraform unit tests for iam.tf.

These tests verify IAM roles, policies, and permissions
are correctly configured for the Lambda functions.
"""

import re

import pytest

# Expected IAM roles for Lambda functions
LAMBDA_IAM_ROLES = [
    "lambda_runners_handler",
    # Note: runner_terminator removed - runners are ephemeral and self-terminate
    "ignored_events_archiver",
    "circuit_breaker_reset",
    "circuit_breaker_remediation",
    "dlq_reprocessor",
    "circuit_breaker_recovery",
    "drift_recovery",
    "spot_interruption_handler",
    "stale_runner_cleanup",
]


class TestIAMRolesExist:
    """Test that all expected IAM roles are defined."""

    @pytest.mark.parametrize("role_name", LAMBDA_IAM_ROLES)
    def test_iam_role_exists(self, iam_tf_content, role_name):
        """Verify IAM role resource is defined."""
        pattern = rf'resource\s+"aws_iam_role"\s+"{role_name}"'
        assert re.search(pattern, iam_tf_content), (
            f"IAM role '{role_name}' not found in iam.tf"
        )


class TestIAMAssumeRolePolicy:
    """Test IAM assume role policy configurations."""

    @pytest.mark.parametrize("role_name", LAMBDA_IAM_ROLES)
    def test_role_allows_lambda_assume(self, iam_tf_content, role_name):
        """Verify IAM role allows Lambda service to assume it."""
        # All Lambda roles should allow lambda.amazonaws.com to assume
        assert '"lambda.amazonaws.com"' in iam_tf_content, (
            "Lambda service principal not found in assume role policy"
        )
        assert '"sts:AssumeRole"' in iam_tf_content, (
            "sts:AssumeRole action not found in assume role policy"
        )


class TestIAMBasicExecutionPolicy:
    """Test IAM basic execution policy attachments."""

    def test_basic_execution_role_attached(self, iam_tf_content):
        """Verify AWSLambdaBasicExecutionRole is attached to Lambda roles."""
        pattern = r'policy_arn\s*=\s*"arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"'
        attachments = len(re.findall(pattern, iam_tf_content))
        # Should have at least as many attachments as roles
        assert attachments >= len(LAMBDA_IAM_ROLES), (
            f"Expected at least {len(LAMBDA_IAM_ROLES)} basic execution policy attachments, "
            f"found {attachments}"
        )


class TestIAMXRayPolicy:
    """Test IAM X-Ray policy attachments."""

    def test_xray_policy_attached(self, iam_tf_content):
        """Verify AWSXRayDaemonWriteAccess is attached for tracing."""
        pattern = r'policy_arn\s*=\s*"arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"'
        assert re.search(pattern, iam_tf_content), (
            "X-Ray daemon write access policy not found in IAM configuration"
        )


class TestIAMSSMPermissions:
    """Test IAM SSM parameter permissions."""

    def test_ssm_get_parameter_permission_exists(self, iam_tf_content):
        """Verify ssm:GetParameter permission is granted."""
        assert '"ssm:GetParameter"' in iam_tf_content, (
            "SSM GetParameter permission not found"
        )


class TestIAMSQSPermissions:
    """Test IAM SQS permissions."""

    def test_sqs_send_message_permission_exists(self, iam_tf_content):
        """Verify sqs:SendMessage permission is granted."""
        assert '"sqs:SendMessage"' in iam_tf_content, (
            "SQS SendMessage permission not found"
        )

    def test_sqs_receive_message_permission_exists(self, iam_tf_content):
        """Verify sqs:ReceiveMessage permission is granted."""
        assert '"sqs:ReceiveMessage"' in iam_tf_content, (
            "SQS ReceiveMessage permission not found"
        )

    def test_sqs_delete_message_permission_exists(self, iam_tf_content):
        """Verify sqs:DeleteMessage permission is granted."""
        assert '"sqs:DeleteMessage"' in iam_tf_content, (
            "SQS DeleteMessage permission not found"
        )


class TestIAMDynamoDBPermissions:
    """Test IAM DynamoDB permissions."""

    def test_dynamodb_read_permissions_exist(self, iam_tf_content):
        """Verify DynamoDB read permissions are granted."""
        assert '"dynamodb:GetItem"' in iam_tf_content, (
            "DynamoDB GetItem permission not found"
        )
        assert '"dynamodb:Query"' in iam_tf_content, (
            "DynamoDB Query permission not found"
        )

    def test_dynamodb_write_permissions_exist(self, iam_tf_content):
        """Verify DynamoDB write permissions are granted."""
        assert '"dynamodb:PutItem"' in iam_tf_content, (
            "DynamoDB PutItem permission not found"
        )
        assert '"dynamodb:UpdateItem"' in iam_tf_content, (
            "DynamoDB UpdateItem permission not found"
        )


class TestIAMCloudWatchPermissions:
    """Test IAM CloudWatch permissions."""

    def test_cloudwatch_put_metric_data_permission_exists(self, iam_tf_content):
        """Verify cloudwatch:PutMetricData permission is granted."""
        assert '"cloudwatch:PutMetricData"' in iam_tf_content, (
            "CloudWatch PutMetricData permission not found"
        )


class TestIAMKMSPermissions:
    """Test IAM KMS permissions."""

    def test_kms_decrypt_permission_exists(self, iam_tf_content):
        """Verify kms:Decrypt permission is granted for env var decryption."""
        assert '"kms:Decrypt"' in iam_tf_content, (
            "KMS Decrypt permission not found"
        )


class TestIAMEC2Permissions:
    """Test IAM EC2 permissions for runner management."""

    def test_ec2_terminate_instances_permission_exists(self, iam_tf_content):
        """Verify ec2:TerminateInstances permission is granted."""
        assert '"ec2:TerminateInstances"' in iam_tf_content, (
            "EC2 TerminateInstances permission not found"
        )

    def test_ec2_describe_instances_permission_exists(self, iam_tf_content):
        """Verify ec2:DescribeInstances permission is granted."""
        assert '"ec2:DescribeInstances"' in iam_tf_content, (
            "EC2 DescribeInstances permission not found"
        )


class TestIAMECSPermissions:
    """Test IAM ECS permissions for runner management."""

    def test_ecs_stop_task_permission_exists(self, iam_tf_content):
        """Verify ecs:StopTask permission is granted."""
        assert '"ecs:StopTask"' in iam_tf_content, (
            "ECS StopTask permission not found"
        )

    def test_ecs_list_tasks_permission_exists(self, iam_tf_content):
        """Verify ecs:ListTasks permission is granted."""
        assert '"ecs:ListTasks"' in iam_tf_content, (
            "ECS ListTasks permission not found"
        )


class TestIAMNamingConventions:
    """Test IAM naming conventions."""

    @pytest.mark.parametrize("role_name", LAMBDA_IAM_ROLES)
    def test_role_names_use_locals(self, iam_tf_content, role_name):
        """Verify IAM role names use local variables."""
        # Look for local variable reference in name
        pattern = rf'resource\s+"aws_iam_role"\s+"{role_name}"[^}}]*?name\s*=\s*local\.'
        assert re.search(pattern, iam_tf_content, re.DOTALL), (
            f"IAM role '{role_name}' should use local variable for name"
        )


class TestIAMPolicyStructure:
    """Test IAM policy structure and formatting."""

    def test_policies_use_jsonencode(self, iam_tf_content):
        """Verify policies use jsonencode for proper formatting."""
        # Count inline policies
        inline_policies = len(re.findall(r'resource\s+"aws_iam_role_policy"', iam_tf_content))
        # Count jsonencode usages
        jsonencode_count = len(re.findall(r'jsonencode\s*\(', iam_tf_content))
        # Each role's assume_role_policy + inline policies should use jsonencode
        assert jsonencode_count >= inline_policies, (
            f"Not all policies use jsonencode: found {jsonencode_count} for {inline_policies} inline policies"
        )

    def test_policy_version_is_2012(self, iam_tf_content):
        """Verify IAM policies use 2012-10-17 version."""
        assert '"2012-10-17"' in iam_tf_content, (
            "Policy version 2012-10-17 not found"
        )
