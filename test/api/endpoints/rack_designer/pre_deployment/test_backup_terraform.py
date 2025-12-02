def test_backup_terraform_file_exists(backup_tf_path):
    assert backup_tf_path.exists()


def test_backup_vault_exists(backup_tf_content):
    assert 'resource "aws_backup_vault" "rack_designer"' in backup_tf_content


def test_backup_plan_exists(backup_tf_content):
    assert 'resource "aws_backup_plan" "rack_designer"' in backup_tf_content


def test_backup_plan_has_daily_schedule(backup_tf_content):
    assert 'cron(0 5 * * ? *)' in backup_tf_content


def test_backup_plan_has_30_day_retention(backup_tf_content):
    assert 'delete_after = 30' in backup_tf_content


def test_backup_iam_role_exists(backup_tf_content):
    assert 'resource "aws_iam_role" "backup"' in backup_tf_content


def test_backup_iam_role_has_backup_service_principal(backup_tf_content):
    assert 'backup.amazonaws.com' in backup_tf_content


def test_backup_policy_attachment_exists(backup_tf_content):
    assert 'resource "aws_iam_role_policy_attachment" "backup"' in backup_tf_content


def test_backup_policy_uses_aws_managed_policy(backup_tf_content):
    assert 'AWSBackupServiceRolePolicyForBackup' in backup_tf_content


def test_restore_policy_attachment_exists(backup_tf_content):
    assert 'resource "aws_iam_role_policy_attachment" "backup_restores"' in backup_tf_content


def test_restore_policy_uses_aws_managed_policy(backup_tf_content):
    assert 'AWSBackupServiceRolePolicyForRestores' in backup_tf_content


def test_backup_selection_exists(backup_tf_content):
    assert 'resource "aws_backup_selection" "rack_designer"' in backup_tf_content


def test_backup_selection_includes_configurations_table(backup_tf_content):
    assert 'aws_dynamodb_table.configurations.arn' in backup_tf_content


def test_backup_selection_includes_events_table(backup_tf_content):
    assert 'aws_dynamodb_table.events.arn' in backup_tf_content
