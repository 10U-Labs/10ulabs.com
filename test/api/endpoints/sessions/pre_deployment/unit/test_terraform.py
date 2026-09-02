import re
from typing import Any

import hcl2
from repo_utils import REPO_ROOT
from test_fixtures.hcl import V7_COMPATIBLE
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests
from test_fixtures.terraform_tests import create_remote_state_config_tests

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


def _load_events_table() -> Any:
    dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
    with open(dynamodb_tf, encoding='utf-8') as f:
        tf_config = hcl2.load(f, serialization_options=V7_COMPATIBLE)
    return next(
        r['aws_dynamodb_table']['events']
        for r in tf_config['resource']
        if 'events' in r.get('aws_dynamodb_table', {})
    )


TestLambdaLifecycle = create_lambda_lifecycle_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_files=["lambda.tf", "analytics.tf"]
)

TestRemoteStateConfig = create_remote_state_config_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    endpoint_name="sessions"
)


class TestLambdaConfiguration:
    def test_handler_lambda_uses_arm64_architecture(self) -> None:
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'arm64' in content

    def test_handler_lambda_uses_python313_runtime(self) -> None:
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'python3.13' in content

    def test_export_lambda_uses_arm64_architecture(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'arm64' in content

    def test_export_lambda_uses_python313_runtime(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'python3.13' in content


def test_analytics_bucket_configuration() -> None:
    analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
    with open(analytics_tf, encoding='utf-8') as f:
        tf_config = hcl2.load(f, serialization_options=V7_COMPATIBLE)
    versioning = next(
        r['aws_s3_bucket_versioning']['analytics']
        for r in tf_config['resource']
        if 'analytics' in r.get('aws_s3_bucket_versioning', {})
    )
    assert versioning['versioning_configuration'][0]['status'] == 'Disabled'


class TestBackendConfiguration:
    def test_backend_uses_s3(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'backend "s3"' in content

    def test_backend_encryption_enabled(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert re.search(r'encrypt\s+= true', content)

    def test_backend_uses_lockfile(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'use_lockfile' in content

    def test_backend_state_key_uses_sessions(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'sessions/' in content

    def test_required_terraform_version_specified(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'required_version' in content

    def test_aws_provider_version_specified(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'hashicorp/aws' in content

    def test_archive_provider_version_specified(self) -> None:
        backend_tf = SESSIONS_SRC_PATH / "backend.tf"
        content = backend_tf.read_text()
        assert 'hashicorp/archive' in content


class TestProviderConfiguration:
    def test_provider_uses_local_aws_region(self) -> None:
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert 'local.aws_region' in content

    def test_provider_has_default_tags(self) -> None:
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert 'default_tags' in content

    def test_provider_default_tags_set_managed_by_to_terraform(self) -> None:
        providers_tf = SESSIONS_SRC_PATH / "providers.tf"
        content = providers_tf.read_text()
        assert re.search(r'ManagedBy\s+= "terraform"', content)


class TestSharedModuleConfiguration:
    def test_shared_module_sources_common(self) -> None:
        shared_tf = SESSIONS_SRC_PATH / "shared.tf"
        content = shared_tf.read_text()
        assert 'module "common"' in content

    def test_shared_module_uses_correct_path(self) -> None:
        shared_tf = SESSIONS_SRC_PATH / "shared.tf"
        content = shared_tf.read_text()
        assert 'lib/terraform/common' in content


class TestDynamoDbConfiguration:
    def test_dynamodb_table_uses_pay_per_request(self) -> None:
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'PAY_PER_REQUEST' in content

    def test_dynamodb_table_hash_key_is_session_id(self) -> None:
        assert _load_events_table()['hash_key'] == 'session_id'

    def test_dynamodb_table_range_key_is_timestamp(self) -> None:
        assert _load_events_table()['range_key'] == 'timestamp'

    def test_dynamodb_table_has_event_type_gsi(self) -> None:
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'event_type-index' in content

    def test_dynamodb_table_has_device_id_gsi(self) -> None:
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'device_id-index' in content

    def test_dynamodb_table_point_in_time_recovery_enabled(self) -> None:
        assert _load_events_table()['point_in_time_recovery'][0]['enabled'] is True

    def test_dynamodb_table_has_event_type_attribute(self) -> None:
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'name = "event_type"' in content

    def test_dynamodb_table_has_device_id_attribute(self) -> None:
        dynamodb_tf = SESSIONS_SRC_PATH / "dynamodb.tf"
        content = dynamodb_tf.read_text()
        assert 'name = "device_id"' in content


class TestBackupConfiguration:
    def test_backup_vault_defined(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_vault' in content

    def test_backup_plan_defined(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_plan' in content

    def test_backup_plan_has_daily_schedule(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'cron(0 5' in content

    def test_backup_plan_has_30_day_retention(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'delete_after = 30' in content

    def test_backup_role_defined(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'resource "aws_iam_role" "backup"' in content

    def test_backup_selection_defined(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_backup_selection' in content

    def test_backup_selection_includes_dynamodb_table(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_dynamodb_table.events.arn' in content

    def test_backup_role_has_policy_attachment(self) -> None:
        backup_tf = SESSIONS_SRC_PATH / "backup.tf"
        content = backup_tf.read_text()
        assert 'aws_iam_role_policy_attachment' in content


class TestOutputConfiguration:
    def test_lambda_function_name_output_defined(self) -> None:
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "lambda_function_name"' in content

    def test_lambda_function_arn_output_defined(self) -> None:
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "lambda_function_arn"' in content

    def test_dynamodb_table_name_output_defined(self) -> None:
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "dynamodb_table_name"' in content

    def test_dynamodb_table_arn_output_defined(self) -> None:
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "dynamodb_table_arn"' in content

    def test_outputs_have_descriptions(self) -> None:
        outputs_tf = SESSIONS_SRC_PATH / "outputs.tf"
        content = outputs_tf.read_text()
        description_count = content.count('description')
        output_count = content.count('output "')
        assert description_count == output_count


class TestLocalsConfiguration:
    def test_locals_defines_aws_region(self) -> None:
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'module.common.aws_region' in content

    def test_locals_defines_resource_prefix(self) -> None:
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'module.common.resource_prefix' in content

    def test_locals_defines_common_tags(self) -> None:
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'common_tags' in content

    def test_locals_common_tags_purpose_is_sessions(self) -> None:
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert re.search(r'Purpose\s+= "sessions"', content)
