"""Terraform unit tests for locals.tf.

These tests verify local variables are correctly defined
and follow consistent naming conventions.
"""

import re


class TestLocalsBlockExists:
    """Test that locals block is properly defined."""

    def test_locals_block_exists(self, locals_tf_content):
        """Verify locals block is defined."""
        pattern = r'locals\s*\{'
        assert re.search(pattern, locals_tf_content), (
            "locals block not found in locals.tf"
        )

    def test_locals_block_has_content(self, locals_tf_content):
        """Verify locals block contains at least one assignment."""
        pattern = r'locals\s*\{[^}]+='
        assert re.search(pattern, locals_tf_content, re.DOTALL), (
            "locals block should contain at least one assignment"
        )


class TestCommonLocals:
    """Test common local variables."""

    def test_aws_account_id_defined(self, locals_tf_content):
        """Verify aws_account_id is defined."""
        assert 'aws_account_id' in locals_tf_content, (
            "aws_account_id local not found"
        )

    def test_aws_region_defined(self, locals_tf_content):
        """Verify aws_region is defined."""
        assert 'aws_region' in locals_tf_content, (
            "aws_region local not found"
        )

    def test_resource_prefix_defined(self, locals_tf_content):
        """Verify resource_prefix is defined."""
        assert 'resource_prefix' in locals_tf_content, (
            "resource_prefix local not found"
        )

    def test_github_org_defined(self, locals_tf_content):
        """Verify github_org is defined."""
        assert 'github_org' in locals_tf_content, (
            "github_org local not found"
        )

    def test_github_repo_defined(self, locals_tf_content):
        """Verify github_repo is defined."""
        assert 'github_repo' in locals_tf_content, (
            "github_repo local not found"
        )


class TestLambdaConfiguration:
    """Test Lambda configuration locals."""

    def test_lambda_memory_defined(self, locals_tf_content):
        """Verify lambda_memory_mb is defined."""
        assert 'lambda_memory_mb' in locals_tf_content, (
            "lambda_memory_mb local not found"
        )

    def test_lambda_timeout_defined(self, locals_tf_content):
        """Verify lambda_timeout_seconds is defined."""
        assert 'lambda_timeout_seconds' in locals_tf_content, (
            "lambda_timeout_seconds local not found"
        )

    def test_webhook_handler_function_name_defined(self, locals_tf_content):
        """Verify webhook_handler_function_name is defined."""
        assert 'webhook_handler_function_name' in locals_tf_content, (
            "webhook_handler_function_name local not found"
        )


class TestQueueNameLocals:
    """Test SQS queue name locals."""

    def test_webhook_ingress_queue_name_defined(self, locals_tf_content):
        """Verify webhook_ingress_queue_name is defined."""
        assert 'webhook_ingress_queue_name' in locals_tf_content, (
            "webhook_ingress_queue_name local not found"
        )

    def test_webhook_ingress_dlq_name_defined(self, locals_tf_content):
        """Verify webhook_ingress_dlq_name is defined."""
        assert 'webhook_ingress_dlq_name' in locals_tf_content, (
            "webhook_ingress_dlq_name local not found"
        )

    def test_ignored_events_queue_name_defined(self, locals_tf_content):
        """Verify ignored_events_queue_name is defined."""
        assert 'ignored_events_queue_name' in locals_tf_content, (
            "ignored_events_queue_name local not found"
        )

    def test_webhook_dlq_name_defined(self, locals_tf_content):
        """Verify webhook_dlq_name is defined."""
        assert 'webhook_dlq_name' in locals_tf_content, (
            "webhook_dlq_name local not found"
        )


class TestTableNameLocals:
    """Test DynamoDB table name locals."""

    def test_idempotency_table_name_defined(self, locals_tf_content):
        """Verify idempotency_table_name is defined."""
        assert 'idempotency_table_name' in locals_tf_content, (
            "idempotency_table_name local not found"
        )

    def test_circuit_open_table_name_defined(self, locals_tf_content):
        """Verify circuit_open_state_table_name is defined."""
        assert 'circuit_open' in locals_tf_content, (
            "circuit_open table name local not found"
        )


class TestFunctionNameLocals:
    """Test Lambda function name locals."""

    def test_circuit_opens_function_name_defined(self, locals_tf_content):
        """Verify circuit_opens_function_name is defined."""
        assert 'circuit_opens_function_name' in locals_tf_content, (
            "circuit_opens_function_name local not found"
        )

    def test_circuit_open_remediations_function_name_defined(self, locals_tf_content):
        """Verify circuit_open_remediations_function_name is defined."""
        assert 'circuit_open_remediations_function_name' in locals_tf_content, (
            "circuit_open_remediations_function_name local not found"
        )

    def test_dlq_reprocessor_function_name_defined(self, locals_tf_content):
        """Verify dlq_reprocessor_function_name is defined."""
        assert 'dlq_reprocessor_function_name' in locals_tf_content, (
            "dlq_reprocessor_function_name local not found"
        )

    def test_circuit_open_recoveries_function_name_defined(self, locals_tf_content):
        """Verify circuit_open_recoveries_function_name is defined."""
        assert 'circuit_open_recoveries_function_name' in locals_tf_content, (
            "circuit_open_recoveries_function_name local not found"
        )

    def test_drift_recovery_function_name_defined(self, locals_tf_content):
        """Verify drift_recovery_function_name is defined."""
        assert 'drift_recovery_function_name' in locals_tf_content, (
            "drift_recovery_function_name local not found"
        )

    def test_spot_interruption_handler_function_name_defined(self, locals_tf_content):
        """Verify spot_interruption_handler_function_name is defined."""
        assert 'spot_interruption_handler_function_name' in locals_tf_content, (
            "spot_interruption_handler_function_name local not found"
        )

    def test_stale_runner_cleanup_function_name_defined(self, locals_tf_content):
        """Verify stale_runner_cleanup_function_name is defined."""
        assert 'stale_runner_cleanup_function_name' in locals_tf_content, (
            "stale_runner_cleanup_function_name local not found"
        )

    def test_ignored_events_archiver_function_name_defined(self, locals_tf_content):
        """Verify ignored_events_archiver_function_name is defined."""
        assert 'ignored_events_archiver_function_name' in locals_tf_content, (
            "ignored_events_archiver_function_name local not found"
        )


class TestRoleNameLocals:
    """Test IAM role name locals."""

    def test_lambda_runners_handler_role_name_defined(self, locals_tf_content):
        """Verify lambda_runners_handler_role_name is defined."""
        assert 'lambda_runners_handler_role_name' in locals_tf_content, (
            "lambda_runners_handler_role_name local not found"
        )

    def test_circuit_opens_role_name_defined(self, locals_tf_content):
        """Verify circuit_opens_role_name is defined."""
        assert 'circuit_opens_role_name' in locals_tf_content, (
            "circuit_opens_role_name local not found"
        )


class TestCommonTagsLocals:
    """Test common tags local variable."""

    def test_common_tags_defined(self, locals_tf_content):
        """Verify common_tags is defined."""
        assert 'common_tags' in locals_tf_content, (
            "common_tags local not found"
        )

    def test_common_tags_has_managed_by(self, locals_tf_content):
        """Verify common_tags includes ManagedBy tag."""
        assert 'ManagedBy' in locals_tf_content, (
            "ManagedBy tag not found in common_tags"
        )

    def test_common_tags_has_purpose(self, locals_tf_content):
        """Verify common_tags includes Purpose tag."""
        assert 'Purpose' in locals_tf_content, (
            "Purpose tag not found in common_tags"
        )


class TestModuleReferences:
    """Test that locals properly reference module outputs."""

    def test_uses_module_common(self, locals_tf_content):
        """Verify locals reference module.common."""
        assert 'module.common' in locals_tf_content, (
            "locals should reference module.common for shared configuration"
        )

    def test_resource_prefix_from_module(self, locals_tf_content):
        """Verify resource_prefix comes from module.common."""
        pattern = r'resource_prefix\s*=\s*module\.common\.resource_prefix'
        assert re.search(pattern, locals_tf_content), (
            "resource_prefix should reference module.common.resource_prefix"
        )


class TestSSMParameterLocals:
    """Test SSM parameter name locals."""

    def test_webhook_secret_parameter_name_defined(self, locals_tf_content):
        """Verify SSM parameter name for webhook secret is defined."""
        assert 'ssm_parameter_name_for_webhook_secret' in locals_tf_content, (
            "ssm_parameter_name_for_webhook_secret local not found"
        )

    def test_github_token_parameter_referenced(self, locals_tf_content):
        """Verify GitHub token parameter name is referenced."""
        assert 'github_token' in locals_tf_content.lower(), (
            "GitHub token parameter reference not found"
        )


class TestAlertingLocals:
    """Test alerting configuration locals."""

    def test_circuit_open_alert_email_defined(self, locals_tf_content):
        """Verify circuit_open_alert_email is defined."""
        assert 'circuit_open_alert_email' in locals_tf_content, (
            "circuit_open_alert_email local not found"
        )

    def test_alert_email_uses_variable_or_local(self, locals_tf_content):
        """Verify alert email is configurable via variable or local."""
        has_var = 'var.' in locals_tf_content
        has_local_email = 'alert_email' in locals_tf_content
        assert has_var or has_local_email, (
            "Alert email should be configurable"
        )
