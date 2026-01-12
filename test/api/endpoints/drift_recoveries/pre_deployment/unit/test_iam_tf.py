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


class TestLambdaSQSPolicy:
    """Test Lambda SQS access policy."""

    def test_sqs_policy_exists(self, iam_tf_content):
        """Verify SQS access policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"lambda_sqs"'
        assert re.search(pattern, iam_tf_content)

    def test_sqs_policy_has_receive_permission(self, iam_tf_content):
        """Verify SQS policy allows ReceiveMessage."""
        assert '"sqs:ReceiveMessage"' in iam_tf_content

    def test_sqs_policy_has_delete_permission(self, iam_tf_content):
        """Verify SQS policy allows DeleteMessage."""
        assert '"sqs:DeleteMessage"' in iam_tf_content

    def test_sqs_policy_has_get_attributes_permission(self, iam_tf_content):
        """Verify SQS policy allows GetQueueAttributes."""
        assert '"sqs:GetQueueAttributes"' in iam_tf_content


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


class TestConfigRecorderIAMRole:
    """Test Config recorder IAM role configuration."""

    def test_config_recorder_role_exists(self, iam_tf_content):
        """Verify Config recorder IAM role is defined."""
        pattern = r'resource\s+"aws_iam_role"\s+"config_recorder"'
        assert re.search(pattern, iam_tf_content)

    def test_config_recorder_role_allows_config_service(self, iam_tf_content):
        """Verify Config role allows config service to assume it."""
        assert '"config.amazonaws.com"' in iam_tf_content

    def test_config_recorder_has_aws_config_policy(self, iam_tf_content):
        """Verify AWS_ConfigRole managed policy is attached."""
        pattern = r'aws:policy/service-role/AWS_ConfigRole'
        assert re.search(pattern, iam_tf_content)


class TestConfigRecorderS3Policy:
    """Test Config recorder S3 access policy."""

    def test_config_s3_policy_exists(self, iam_tf_content):
        """Verify Config S3 delivery policy is defined."""
        pattern = r'resource\s+"aws_iam_role_policy"\s+"config_recorder_s3"'
        assert re.search(pattern, iam_tf_content)

    def test_config_s3_policy_has_put_object_permission(self, iam_tf_content):
        """Verify Config S3 policy allows PutObject."""
        assert '"s3:PutObject"' in iam_tf_content

    def test_config_s3_policy_has_get_bucket_acl_permission(self, iam_tf_content):
        """Verify Config S3 policy allows GetBucketAcl."""
        assert '"s3:GetBucketAcl"' in iam_tf_content
