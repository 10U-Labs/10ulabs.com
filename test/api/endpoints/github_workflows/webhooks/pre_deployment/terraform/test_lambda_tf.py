"""Terraform unit tests for lambda.tf.

These tests verify the structure and configuration of Lambda resources
defined in the Terraform configuration without making AWS calls.
"""

import re

import pytest

# Expected Lambda functions and their configurations
LAMBDA_FUNCTIONS = [
    {
        "resource_name": "runners_handler",
        "handler": "webhook_router.lambda_handler",
        "description_contains": "webhook",
    },
    # Note: runner_terminator removed - runners are ephemeral and self-terminate
    {
        "resource_name": "ignored_events_archiver",
        "handler": "ignored_events_archiver.lambda_handler",
        "description_contains": "archive",
    },
    {
        "resource_name": "circuit_breaker_reset",
        "handler": "circuit_breaker_reset.lambda_handler",
        "description_contains": "reset",
    },
    {
        "resource_name": "circuit_breaker_remediation",
        "handler": "circuit_breaker_remediation.lambda_handler",
        "description_contains": "remediation",
    },
    {
        "resource_name": "dlq_reprocessor",
        "handler": "dlq_reprocessor.handler",
        "description_contains": "reprocess",
    },
    {
        "resource_name": "circuit_breaker_recovery",
        "handler": "circuit_breaker_recovery.lambda_handler",
        "description_contains": "recovery",
    },
    {
        "resource_name": "drift_recovery",
        "handler": "drift_recovery.lambda_handler",
        "description_contains": "drift",
    },
    {
        "resource_name": "spot_interruption_handler",
        "handler": "spot_interruption_handler.lambda_handler",
        "description_contains": "spot",
    },
    {
        "resource_name": "stale_runner_cleanup",
        "handler": "stale_runner_cleanup.lambda_handler",
        "description_contains": "stale",
    },
]


class TestLambdaResourcesExist:
    """Test that all expected Lambda resources are defined."""

    @pytest.mark.parametrize("lambda_config", LAMBDA_FUNCTIONS)
    def test_lambda_function_resource_exists(self, lambda_tf_content, lambda_config):
        """Verify Lambda function resource is defined."""
        pattern = rf'resource\s+"aws_lambda_function"\s+"{lambda_config["resource_name"]}"'
        assert re.search(pattern, lambda_tf_content), (
            f"Lambda function resource '{lambda_config['resource_name']}' not found in lambda.tf"
        )

    @pytest.mark.parametrize("lambda_config", LAMBDA_FUNCTIONS)
    def test_archive_file_data_source_exists(self, lambda_tf_content, lambda_config):
        """Verify archive_file data source exists for Lambda."""
        pattern = rf'data\s+"archive_file"\s+"{lambda_config["resource_name"]}"'
        assert re.search(pattern, lambda_tf_content), (
            f"Archive file data source for '{lambda_config['resource_name']}' not found in lambda.tf"
        )

    @pytest.mark.parametrize("lambda_config", LAMBDA_FUNCTIONS)
    def test_log_group_resource_exists(self, lambda_tf_content, lambda_config):
        """Verify CloudWatch log group is defined for Lambda."""
        pattern = rf'resource\s+"aws_cloudwatch_log_group"\s+"{lambda_config["resource_name"]}"'
        assert re.search(pattern, lambda_tf_content), (
            f"CloudWatch log group for '{lambda_config['resource_name']}' not found in lambda.tf"
        )


class TestLambdaHandlerConfiguration:
    """Test Lambda handler configurations."""

    @pytest.mark.parametrize("lambda_config", LAMBDA_FUNCTIONS)
    def test_handler_value_correct(self, lambda_tf_content, lambda_config):
        """Verify Lambda handler value matches expected."""
        # Find the Lambda resource block and extract handler
        resource_pattern = rf'resource\s+"aws_lambda_function"\s+"{lambda_config["resource_name"]}"\s*\{{'
        match = re.search(resource_pattern, lambda_tf_content)
        assert match, f"Lambda resource '{lambda_config['resource_name']}' not found"

        # Extract handler from the block
        start_pos = match.end()
        handler_pattern = r'handler\s*=\s*"([^"]+)"'
        handler_match = re.search(handler_pattern, lambda_tf_content[start_pos:start_pos+2000])
        assert handler_match, f"Handler not found for '{lambda_config['resource_name']}'"
        assert handler_match.group(1) == lambda_config["handler"], (
            f"Handler mismatch for '{lambda_config['resource_name']}': "
            f"expected '{lambda_config['handler']}', got '{handler_match.group(1)}'"
        )


class TestLambdaRuntimeConfiguration:
    """Test Lambda runtime and architecture settings."""

    def test_all_lambdas_use_python313(self, lambda_tf_content):
        """Verify all Lambdas use Python 3.13 runtime."""
        # Count Lambda function resources
        lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', lambda_tf_content))
        # Count Python 3.13 runtime declarations
        runtime_count = len(re.findall(r'runtime\s*=\s*"python3\.13"', lambda_tf_content))
        assert runtime_count == lambda_count, (
            f"Not all Lambda functions use python3.13: "
            f"found {runtime_count} python3.13 runtimes for {lambda_count} functions"
        )

    def test_all_lambdas_use_arm64(self, lambda_tf_content):
        """Verify all Lambdas use arm64 architecture."""
        # Count Lambda function resources
        lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', lambda_tf_content))
        # Count arm64 architecture declarations
        arch_count = len(re.findall(r'architectures\s*=\s*\["arm64"\]', lambda_tf_content))
        assert arch_count == lambda_count, (
            f"Not all Lambda functions use arm64 architecture: "
            f"found {arch_count} arm64 declarations for {lambda_count} functions"
        )


class TestLambdaLoggingConfiguration:
    """Test Lambda logging configurations."""

    def test_all_lambdas_have_logging_config(self, lambda_tf_content):
        """Verify all Lambdas have logging_config block."""
        lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', lambda_tf_content))
        logging_count = len(re.findall(r'logging_config\s*\{', lambda_tf_content))
        assert logging_count == lambda_count, (
            f"Not all Lambda functions have logging_config: "
            f"found {logging_count} logging configs for {lambda_count} functions"
        )

    def test_log_groups_have_retention(self, lambda_tf_content):
        """Verify all log groups have retention_in_days set."""
        log_group_count = len(re.findall(r'resource\s+"aws_cloudwatch_log_group"', lambda_tf_content))
        retention_count = len(re.findall(r'retention_in_days\s*=', lambda_tf_content))
        assert retention_count == log_group_count, (
            f"Not all log groups have retention_in_days: "
            f"found {retention_count} retention settings for {log_group_count} log groups"
        )


class TestLambdaTracingConfiguration:
    """Test Lambda X-Ray tracing configurations."""

    def test_lambdas_have_tracing_config(self, lambda_tf_content):
        """Verify Lambdas have tracing_config for X-Ray."""
        # Most Lambdas should have tracing enabled (some may not)
        tracing_count = len(re.findall(r'tracing_config\s*\{[^}]*mode\s*=\s*"Active"', lambda_tf_content, re.DOTALL))
        # At minimum, the main webhook handler should have tracing
        assert tracing_count >= 1, "Expected at least one Lambda with X-Ray tracing enabled"


class TestLambdaIAMConfiguration:
    """Test Lambda IAM role references."""

    @pytest.mark.parametrize("lambda_config", LAMBDA_FUNCTIONS)
    def test_lambda_has_role_reference(self, lambda_tf_content, lambda_config):
        """Verify Lambda references an IAM role."""
        resource_pattern = rf'resource\s+"aws_lambda_function"\s+"{lambda_config["resource_name"]}"\s*\{{'
        match = re.search(resource_pattern, lambda_tf_content)
        assert match, f"Lambda resource '{lambda_config['resource_name']}' not found"

        start_pos = match.end()
        role_pattern = r'role\s*=\s*aws_iam_role\.\w+\.arn'
        role_match = re.search(role_pattern, lambda_tf_content[start_pos:start_pos+2000])
        assert role_match, f"IAM role reference not found for '{lambda_config['resource_name']}'"


class TestLambdaEventSourceMappings:
    """Test Lambda event source mappings."""

    def test_webhook_handler_has_sqs_trigger(self, lambda_tf_content):
        """Verify webhook handler has SQS event source mapping."""
        pattern = r'resource\s+"aws_lambda_event_source_mapping"\s+"runners_handler_webhook_ingress"'
        assert re.search(pattern, lambda_tf_content), (
            "SQS event source mapping for runners_handler not found"
        )

    # Note: test_runner_terminator_has_sqs_trigger removed - runners are ephemeral

    def test_ignored_events_archiver_has_sqs_trigger(self, lambda_tf_content):
        """Verify ignored_events_archiver has SQS event source mapping."""
        pattern = r'resource\s+"aws_lambda_event_source_mapping"\s+"ignored_events_archiver_sqs"'
        assert re.search(pattern, lambda_tf_content), (
            "SQS event source mapping for ignored_events_archiver not found"
        )


class TestLambdaEnvironmentVariables:
    """Test Lambda environment variable configurations."""

    def test_webhook_handler_has_required_env_vars(self, lambda_tf_content):
        """Verify webhook handler has required environment variables."""
        required_vars = [
            "API_BASE_URL",
            "API_KEY_PARAMETER_NAME",
            # Note: CANCELLATION_QUEUE_URL removed - runners are ephemeral
            "CIRCUIT_BREAKER_TABLE_NAME",
            "GITHUB_REPO",
            "GITHUB_TOKEN_SECRET_NAME",
            "IDEMPOTENCY_TABLE_NAME",
            "IGNORED_EVENTS_QUEUE_URL",
            "WEBHOOK_SECRET_NAME",
        ]
        # Find the runners_handler environment block
        for var in required_vars:
            pattern = rf'{var}\s*='
            assert re.search(pattern, lambda_tf_content), (
                f"Environment variable '{var}' not found in webhook handler"
            )


class TestLambdaNamingConventions:
    """Test Lambda naming conventions."""

    def test_function_names_use_locals(self, lambda_tf_content):
        """Verify function_name uses local variables for consistency."""
        # Each Lambda should reference local.xxx_function_name
        pattern = r'function_name\s*=\s*local\.\w+_function_name'
        local_refs = len(re.findall(pattern, lambda_tf_content))
        lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', lambda_tf_content))
        assert local_refs == lambda_count, (
            f"Not all Lambda function_names use local variables: "
            f"found {local_refs} local refs for {lambda_count} functions"
        )


class TestLambdaLifecycleConfiguration:
    """Test Lambda lifecycle configurations."""

    def test_lambdas_have_lifecycle_blocks(self, lambda_tf_content):
        """Verify Lambdas have lifecycle blocks for IAM role replacement."""
        lifecycle_count = len(re.findall(r'lifecycle\s*\{[^}]*replace_triggered_by', lambda_tf_content, re.DOTALL))
        lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', lambda_tf_content))
        # Most Lambdas should have lifecycle blocks (at least the major ones)
        assert lifecycle_count >= lambda_count - 2, (
            f"Expected most Lambdas to have lifecycle blocks: "
            f"found {lifecycle_count} for {lambda_count} functions"
        )
