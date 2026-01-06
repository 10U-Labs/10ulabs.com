"""Terraform configuration tests for sessions endpoint.

Tests verify Terraform configuration correctness without deploying:
- Lambda lifecycle rules for environment variable handling
- IAM role naming conventions (PascalCase)
- Lambda function naming conventions (PascalCase)
- Remote state configuration (no hardcoded values)
- Backend configuration (S3 state, encryption)
- Provider configuration (default tags)
- DynamoDB table configuration (billing, keys, indexes, PITR)
- Backup configuration (vault, plan, retention, selection)
- Output definitions (function name/arn, table name/arn)
"""
from repo_utils import REPO_ROOT
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests
from test_fixtures.terraform_tests import create_remote_state_config_tests

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


# Generate Lambda lifecycle tests for all Terraform files with Lambda definitions
TestLambdaLifecycle = create_lambda_lifecycle_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_files=["lambda.tf", "analytics.tf"]
)

# Generate remote state configuration tests to prevent hardcoded values
TestRemoteStateConfig = create_remote_state_config_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    endpoint_name="sessions"
)


class TestIamRoleNamingConventions:
    """Tests for IAM role naming conventions."""

    def test_sessions_handler_role_name_is_pascalcase(self):
        """Verify SessionsHandlerRole follows PascalCase naming."""
        iam_tf = SESSIONS_SRC_PATH / "iam.tf"
        content = iam_tf.read_text()
        assert 'SessionsHandlerRole' in content

    def test_sessions_export_role_name_is_pascalcase(self):
        """Verify SessionsExportRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsExportRole' in content

    def test_sessions_crawler_trigger_role_name_is_pascalcase(self):
        """Verify SessionsCrawlerTriggerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsCrawlerTriggerRole' in content

    def test_sessions_glue_crawler_role_name_is_pascalcase(self):
        """Verify SessionsGlueCrawlerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsGlueCrawlerRole' in content

    def test_sessions_scheduler_role_name_is_pascalcase(self):
        """Verify SessionsSchedulerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsSchedulerRole' in content


class TestLambdaFunctionNamingConventions:
    """Tests for Lambda function naming conventions."""

    def test_export_function_name_is_pascalcase(self):
        """Verify SessionsExport function name follows PascalCase."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsExport' in content

    def test_crawler_trigger_function_name_is_pascalcase(self):
        """Verify SessionsCrawlerTrigger function name follows PascalCase."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsCrawlerTrigger' in content


class TestLambdaConfiguration:
    """Tests for Lambda configuration in Terraform."""

    def test_handler_lambda_uses_arm64_architecture(self):
        """Verify handler Lambda uses arm64 architecture."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'arm64' in content

    def test_handler_lambda_uses_python313_runtime(self):
        """Verify handler Lambda uses Python 3.13 runtime."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'python3.13' in content

    def test_export_lambda_uses_arm64_architecture(self):
        """Verify export Lambda uses arm64 architecture."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'arm64' in content

    def test_export_lambda_uses_python313_runtime(self):
        """Verify export Lambda uses Python 3.13 runtime."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'python3.13' in content


class TestBackendConfiguration:
    """Tests for Terraform backend configuration."""

    def test_backend_uses_s3(self):
        """Verify backend uses S3 for state storage."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'backend "s3"' in content

    def test_backend_encryption_enabled(self):
        """Verify S3 backend has encryption enabled."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'encrypt' in content
        assert 'true' in content

    def test_backend_uses_lockfile(self):
        """Verify S3 backend uses lockfile for state locking."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'use_lockfile' in content

    def test_backend_state_key_uses_sessions(self):
        """Verify backend state key is in sessions namespace."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'sessions/' in content

    def test_required_terraform_version_specified(self):
        """Verify required Terraform version is specified."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'required_version' in content

    def test_aws_provider_version_specified(self):
        """Verify AWS provider version is specified."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'hashicorp/aws' in content

    def test_archive_provider_version_specified(self):
        """Verify archive provider version is specified."""
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'hashicorp/archive' in content


class TestProviderConfiguration:
    """Tests for AWS provider configuration."""

    def test_provider_uses_local_aws_region(self):
        """Verify provider uses local.aws_region for region."""
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert 'local.aws_region' in content

    def test_provider_has_default_tags(self):
        """Verify provider has default_tags block."""
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert 'default_tags' in content

    def test_provider_default_tags_include_managed_by(self):
        """Verify default tags include ManagedBy = terraform."""
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert 'ManagedBy' in content
        assert 'terraform' in content


class TestSharedModuleConfiguration:
    """Tests for shared module configuration."""

    def test_shared_module_sources_common(self):
        """Verify shared.tf sources the common module."""
        shared_tf = SESSIONS_SRC_PATH / "shared.tf"
        content = shared_tf.read_text()
        assert 'module "common"' in content

    def test_shared_module_uses_correct_path(self):
        """Verify common module uses correct relative path."""
        shared_tf = SESSIONS_SRC_PATH / "shared.tf"
        content = shared_tf.read_text()
        assert 'lib/terraform/common' in content


class TestDynamoDbConfiguration:
    """Tests for DynamoDB table configuration in Terraform."""

    def test_dynamodb_table_uses_pay_per_request(self):
        """Verify DynamoDB table uses PAY_PER_REQUEST billing mode."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'PAY_PER_REQUEST' in content

    def test_dynamodb_table_has_session_id_hash_key(self):
        """Verify DynamoDB table uses session_id as hash key."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'hash_key' in content
        assert 'session_id' in content

    def test_dynamodb_table_has_timestamp_range_key(self):
        """Verify DynamoDB table uses timestamp as range key."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'range_key' in content
        assert 'timestamp' in content

    def test_dynamodb_table_has_event_type_gsi(self):
        """Verify DynamoDB table has event_type-index GSI."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'event_type-index' in content

    def test_dynamodb_table_has_device_id_gsi(self):
        """Verify DynamoDB table has device_id-index GSI."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'device_id-index' in content

    def test_dynamodb_table_has_pitr_enabled(self):
        """Verify DynamoDB table has point-in-time recovery enabled."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'point_in_time_recovery' in content
        assert 'enabled = true' in content

    def test_dynamodb_table_has_event_type_attribute(self):
        """Verify DynamoDB table defines event_type attribute."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'name = "event_type"' in content

    def test_dynamodb_table_has_device_id_attribute(self):
        """Verify DynamoDB table defines device_id attribute."""
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'name = "device_id"' in content


class TestBackupConfiguration:
    """Tests for AWS Backup configuration in Terraform."""

    def test_backup_vault_defined(self):
        """Verify backup vault resource is defined."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_vault' in content

    def test_backup_plan_defined(self):
        """Verify backup plan resource is defined."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_plan' in content

    def test_backup_plan_has_daily_schedule(self):
        """Verify backup plan runs daily at 5 AM UTC."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'cron(0 5' in content

    def test_backup_plan_has_30_day_retention(self):
        """Verify backup plan has 30-day retention."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'delete_after = 30' in content

    def test_backup_role_defined(self):
        """Verify backup IAM role is defined."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_iam_role' in content
        assert 'backup' in content.lower()

    def test_backup_selection_defined(self):
        """Verify backup selection resource is defined."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_selection' in content

    def test_backup_selection_includes_dynamodb_table(self):
        """Verify backup selection includes DynamoDB events table."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_dynamodb_table.events.arn' in content

    def test_backup_role_has_policy_attachment(self):
        """Verify backup role has required policy attachments."""
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_iam_role_policy_attachment' in content


class TestOutputConfiguration:
    """Tests for Terraform output configuration."""

    def test_lambda_function_name_output_defined(self):
        """Verify lambda_function_name output is defined."""
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "lambda_function_name"' in content

    def test_lambda_function_arn_output_defined(self):
        """Verify lambda_function_arn output is defined."""
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "lambda_function_arn"' in content

    def test_dynamodb_table_name_output_defined(self):
        """Verify dynamodb_table_name output is defined."""
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "dynamodb_table_name"' in content

    def test_dynamodb_table_arn_output_defined(self):
        """Verify dynamodb_table_arn output is defined."""
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "dynamodb_table_arn"' in content

    def test_outputs_have_descriptions(self):
        """Verify all outputs have descriptions."""
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        description_count = content.count('description')
        output_count = content.count('output "')
        assert description_count == output_count


class TestLocalsConfiguration:
    """Tests for locals block configuration."""

    def test_locals_defines_aws_region(self):
        """Verify locals defines aws_region from common module."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'aws_region' in content
        assert 'module.common.aws_region' in content

    def test_locals_defines_resource_prefix(self):
        """Verify locals defines resource_prefix from common module."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'resource_prefix' in content
        assert 'module.common.resource_prefix' in content

    def test_locals_defines_common_tags(self):
        """Verify locals defines common_tags block."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'common_tags' in content

    def test_locals_common_tags_include_purpose(self):
        """Verify common_tags include Purpose = sessions."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'Purpose' in content
        assert 'sessions' in content
