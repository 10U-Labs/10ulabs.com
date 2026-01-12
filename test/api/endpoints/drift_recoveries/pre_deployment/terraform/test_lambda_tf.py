"""Terraform unit tests for lambda.tf.

These tests verify the structure and configuration of Lambda resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestLambdaResourcesExist:
    """Test that all expected Lambda resources are defined."""

    def test_lambda_function_resource_exists(self, lambda_tf_content):
        """Verify Lambda function resource is defined."""
        pattern = r'resource\s+"aws_lambda_function"\s+"handler"'
        assert re.search(pattern, lambda_tf_content)

    def test_archive_file_data_source_exists(self, lambda_tf_content):
        """Verify archive_file data source exists for Lambda."""
        pattern = r'data\s+"archive_file"\s+"handler"'
        assert re.search(pattern, lambda_tf_content)

    def test_log_group_resource_exists(self, lambda_tf_content):
        """Verify CloudWatch log group is defined for Lambda."""
        pattern = r'resource\s+"aws_cloudwatch_log_group"\s+"handler"'
        assert re.search(pattern, lambda_tf_content)

    def test_event_source_mapping_exists(self, lambda_tf_content):
        """Verify SQS event source mapping is defined."""
        pattern = r'resource\s+"aws_lambda_event_source_mapping"\s+"sqs"'
        assert re.search(pattern, lambda_tf_content)


class TestLambdaHandlerConfiguration:
    """Test Lambda handler configurations."""

    def test_handler_value_correct(self, lambda_tf_content):
        """Verify Lambda handler value is handler.lambda_handler."""
        pattern = r'handler\s*=\s*"handler\.lambda_handler"'
        assert re.search(pattern, lambda_tf_content)

    def test_runtime_is_python313(self, lambda_tf_content):
        """Verify Lambda uses Python 3.13 runtime."""
        pattern = r'runtime\s*=\s*"python3\.13"'
        assert re.search(pattern, lambda_tf_content)

    def test_architecture_is_arm64(self, lambda_tf_content):
        """Verify Lambda uses arm64 architecture."""
        pattern = r'architectures\s*=\s*\["arm64"\]'
        assert re.search(pattern, lambda_tf_content)

    def test_timeout_is_120_seconds(self, lambda_tf_content):
        """Verify Lambda timeout is 120 seconds."""
        pattern = r'timeout\s*=\s*120'
        assert re.search(pattern, lambda_tf_content)

    def test_memory_size_is_256(self, lambda_tf_content):
        """Verify Lambda memory size is 256 MB."""
        pattern = r'memory_size\s*=\s*256'
        assert re.search(pattern, lambda_tf_content)


class TestLambdaEnvironmentVariables:
    """Test Lambda environment variable configurations."""

    def test_has_github_repo_env_var(self, lambda_tf_content):
        """Verify GITHUB_REPO environment variable is set."""
        pattern = r'GITHUB_REPO\s*='
        assert re.search(pattern, lambda_tf_content)

    def test_has_github_token_parameter_name_env_var(self, lambda_tf_content):
        """Verify GITHUB_TOKEN_PARAMETER_NAME environment variable is set."""
        pattern = r'GITHUB_TOKEN_PARAMETER_NAME\s*='
        assert re.search(pattern, lambda_tf_content)

    def test_has_sns_topic_arn_env_var(self, lambda_tf_content):
        """Verify SNS_TOPIC_ARN environment variable is set."""
        pattern = r'SNS_TOPIC_ARN\s*='
        assert re.search(pattern, lambda_tf_content)

    def test_has_managed_vpc_id_env_var(self, lambda_tf_content):
        """Verify MANAGED_VPC_ID environment variable is set."""
        pattern = r'MANAGED_VPC_ID\s*='
        assert re.search(pattern, lambda_tf_content)


class TestLambdaNamingConventions:
    """Test Lambda naming conventions."""

    def test_function_name_uses_local(self, lambda_tf_content):
        """Verify function_name uses local variable."""
        pattern = r'function_name\s*=\s*local\.function_name'
        assert re.search(pattern, lambda_tf_content)

    def test_role_references_iam_role(self, lambda_tf_content):
        """Verify Lambda references IAM role."""
        pattern = r'role\s*=\s*aws_iam_role\.lambda\.arn'
        assert re.search(pattern, lambda_tf_content)


class TestLambdaEventSourceMapping:
    """Test Lambda SQS event source mapping configuration."""

    def test_event_source_references_sqs_queue(self, lambda_tf_content):
        """Verify event source mapping references SQS queue."""
        pattern = r'event_source_arn\s*=\s*aws_sqs_queue\.handler\.arn'
        assert re.search(pattern, lambda_tf_content)

    def test_batch_size_is_one(self, lambda_tf_content):
        """Verify batch size is 1 for serial processing."""
        pattern = r'batch_size\s*=\s*1'
        assert re.search(pattern, lambda_tf_content)

    def test_mapping_is_enabled(self, lambda_tf_content):
        """Verify event source mapping is enabled."""
        pattern = r'enabled\s*=\s*true'
        assert re.search(pattern, lambda_tf_content)


class TestCloudWatchLogGroup:
    """Test CloudWatch log group configuration."""

    def test_log_group_name_format(self, lambda_tf_content):
        """Verify log group name follows /aws/lambda/ format."""
        pattern = r'name\s*=\s*"/aws/lambda/\$\{local\.function_name\}"'
        assert re.search(pattern, lambda_tf_content)

    def test_log_group_has_retention(self, lambda_tf_content):
        """Verify log group has retention configured."""
        pattern = r'retention_in_days\s*=\s*30'
        assert re.search(pattern, lambda_tf_content)
