"""Terraform unit tests for iam.tf.

These tests verify the structure and configuration of IAM resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestLambdaIAMRole:
    """Test Lambda IAM role configuration."""

    def test_lambda_role_exists(self, iam_tf_content):
        """Verify Lambda IAM role is defined."""
        pattern = r'resource\s+"aws_iam_role"\s+"lambda"'
        assert re.search(pattern, iam_tf_content)

    def test_lambda_role_uses_local_name(self, iam_tf_content):
        """Verify Lambda role uses local variable for name."""
        pattern = r'name\s*=\s*local\.lambda_role_name'
        assert re.search(pattern, iam_tf_content)

    def test_lambda_role_allows_lambda_service(self, iam_tf_content):
        """Verify Lambda role allows Lambda service to assume it."""
        assert '"lambda.amazonaws.com"' in iam_tf_content

    def test_basic_execution_policy_attached(self, iam_tf_content):
        """Verify AWSLambdaBasicExecutionRole is attached."""
        pattern = r'aws:policy/service-role/AWSLambdaBasicExecutionRole'
        assert re.search(pattern, iam_tf_content)


class TestLambdaSSMPolicy:
    """Test Lambda SSM access policy."""

    def test_ssm_policy_exists(self, iam_tf_content):
        """Verify SSM access policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"lambda_ssm"'
        assert re.search(pattern, iam_tf_content)

    def test_ssm_policy_has_get_parameter_permission(self, iam_tf_content):
        """Verify SSM policy allows GetParameter."""
        assert '"ssm:GetParameter"' in iam_tf_content


class TestLambdaKMSPolicy:
    """Test Lambda KMS access policy."""

    def test_kms_policy_exists(self, iam_tf_content):
        """Verify KMS access policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"lambda_kms"'
        assert re.search(pattern, iam_tf_content)

    def test_kms_policy_has_decrypt_permission(self, iam_tf_content):
        """Verify KMS policy allows Decrypt."""
        assert '"kms:Decrypt"' in iam_tf_content


class TestLambdaSNSPolicy:
    """Test Lambda SNS access policy."""

    def test_sns_policy_exists(self, iam_tf_content):
        """Verify SNS access policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"lambda_sns"'
        assert re.search(pattern, iam_tf_content)

    def test_sns_policy_has_publish_permission(self, iam_tf_content):
        """Verify SNS policy allows Publish."""
        assert '"sns:Publish"' in iam_tf_content


class TestLambdaEC2Policy:
    """Test Lambda EC2 access policy."""

    def test_ec2_policy_exists(self, iam_tf_content):
        """Verify EC2 access policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"lambda_ec2"'
        assert re.search(pattern, iam_tf_content)

    def test_ec2_policy_has_describe_subnets_permission(self, iam_tf_content):
        """Verify EC2 policy allows DescribeSubnets."""
        assert '"ec2:DescribeSubnets"' in iam_tf_content

    def test_ec2_policy_has_describe_security_groups_permission(self, iam_tf_content):
        """Verify EC2 policy allows DescribeSecurityGroups."""
        assert '"ec2:DescribeSecurityGroups"' in iam_tf_content

    def test_ec2_policy_has_describe_vpcs_permission(self, iam_tf_content):
        """Verify EC2 policy allows DescribeVpcs."""
        assert '"ec2:DescribeVpcs"' in iam_tf_content
