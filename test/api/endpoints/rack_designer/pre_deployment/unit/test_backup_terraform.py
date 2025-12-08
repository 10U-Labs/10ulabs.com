"""Unit tests for backup Terraform configuration."""


def test_backup_terraform_file_exists(backup_tf_path):
    """Test backup.tf file exists."""
    assert backup_tf_path.exists()


def test_backup_vault_exists(backup_tf_content):
    """Test backup vault resource exists."""
    assert 'resource "aws_backup_vault" "rack_designer"' in backup_tf_content


def test_backup_plan_exists(backup_tf_content):
    """Test backup plan resource exists."""
    assert 'resource "aws_backup_plan" "rack_designer"' in backup_tf_content


def test_backup_plan_has_daily_schedule(backup_tf_content):
    """Test backup plan has daily schedule."""
    assert 'cron(0 5 * * ? *)' in backup_tf_content


def test_backup_plan_has_30_day_retention(backup_tf_content):
    """Test backup plan has 30 day retention."""
    assert 'delete_after = 30' in backup_tf_content


def test_backup_iam_role_exists(backup_tf_content):
    """Test backup IAM role exists."""
    assert 'resource "aws_iam_role" "backup"' in backup_tf_content


def test_backup_iam_role_has_backup_service_principal(backup_tf_content):
    """Test backup role has backup service principal."""
    assert 'backup.amazonaws.com' in backup_tf_content


def test_backup_policy_attachment_exists(backup_tf_content):
    """Test backup policy attachment exists."""
    assert 'resource "aws_iam_role_policy_attachment" "backup"' in backup_tf_content


def test_backup_policy_uses_aws_managed_policy(backup_tf_content):
    """Test backup uses AWS managed policy."""
    assert 'AWSBackupServiceRolePolicyForBackup' in backup_tf_content


def test_restore_policy_attachment_exists(backup_tf_content):
    """Test restore policy attachment exists."""
    assert 'resource "aws_iam_role_policy_attachment" "backup_restores"' in backup_tf_content


def test_restore_policy_uses_aws_managed_policy(backup_tf_content):
    """Test restore uses AWS managed policy."""
    assert 'AWSBackupServiceRolePolicyForRestores' in backup_tf_content


def test_backup_selection_exists(backup_tf_content):
    """Test backup selection resource exists."""
    assert 'resource "aws_backup_selection" "rack_designer"' in backup_tf_content


def test_backup_selection_includes_configurations_table(backup_tf_content):
    """Test backup includes configurations table."""
    assert 'aws_dynamodb_table.configurations.arn' in backup_tf_content


def test_backup_selection_includes_events_table(backup_tf_content):
    """Test backup includes events table."""
    assert 'aws_dynamodb_table.events.arn' in backup_tf_content
