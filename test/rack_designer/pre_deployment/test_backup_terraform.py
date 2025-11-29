from pathlib import Path


def test_backup_terraform_file_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    assert backup_file.exists()


def test_backup_vault_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_backup_vault" "rack_designer"' in content


def test_backup_plan_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_backup_plan" "rack_designer"' in content


def test_backup_plan_has_daily_schedule():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cron(0 5 * * ? *)' in content


def test_backup_plan_has_30_day_retention():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'delete_after = 30' in content


def test_backup_iam_role_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "backup"' in content


def test_backup_iam_role_has_backup_service_principal():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'backup.amazonaws.com' in content


def test_backup_policy_attachment_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "backup"' in content


def test_backup_policy_uses_aws_managed_policy():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSBackupServiceRolePolicyForBackup' in content


def test_restore_policy_attachment_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "backup_restores"' in content


def test_restore_policy_uses_aws_managed_policy():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSBackupServiceRolePolicyForRestores' in content


def test_backup_selection_exists():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_backup_selection" "rack_designer"' in content


def test_backup_selection_includes_configurations_table():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_dynamodb_table.configurations.arn' in content


def test_backup_selection_includes_events_table():
    backup_file = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "backup.tf"
    with open(backup_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_dynamodb_table.events.arn' in content
