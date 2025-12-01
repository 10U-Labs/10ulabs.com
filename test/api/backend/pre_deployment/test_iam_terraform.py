from pathlib import Path


def test_iam_terraform_file_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    assert iam_file.exists()


def test_ecs_task_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "ecs_task_role"' in content


def test_ecs_execution_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "ecs_execution_role"' in content


def test_ecs_execution_role_policy_attachment_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy"' in content


def test_ecs_execution_ssm_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "ecs_execution_ssm_access"' in content


def test_ecs_execution_kms_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "ecs_execution_kms_access"' in content


def test_lambda_catchall_handler_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_catchall_handler"' in content


def test_lambda_runners_handler_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_runners_handler"' in content


def test_lambda_runners_handler_has_xray_policy():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_runners_handler_xray"' in content


def test_lambda_runners_handler_has_ssm_policy():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_runners_handler_ssm"' in content


def test_lambda_runners_handler_has_cloudwatch_policy():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_runners_handler_cloudwatch"' in content


def test_lambda_runners_handler_has_sqs_policy():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_runners_handler_sqs"' in content


def test_lambda_runners_handler_has_dynamodb_policy():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_runners_handler_dynamodb"' in content


def test_circuit_breaker_remediation_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "circuit_breaker_remediation"' in content


def test_circuit_breaker_remediation_has_permissions():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "circuit_breaker_remediation_permissions"' in content


def test_dlq_reprocessor_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "dlq_reprocessor"' in content


def test_dlq_reprocessor_has_permissions():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "dlq_reprocessor_permissions"' in content


def test_circuit_breaker_recovery_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "circuit_breaker_recovery"' in content


def test_circuit_breaker_recovery_has_permissions():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "circuit_breaker_recovery_permissions"' in content


def test_ecs_task_cloudwatch_logs_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "ecs_task_cloudwatch_logs"' in content


def test_ecs_task_cloudwatch_logs_policy_has_create_log_group_action():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert '"logs:CreateLogGroup"' in content


def test_ecs_task_cloudwatch_logs_policy_has_create_log_stream_action():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert '"logs:CreateLogStream"' in content


def test_ecs_task_cloudwatch_logs_policy_has_put_log_events_action():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert '"logs:PutLogEvents"' in content


def test_ecs_task_cloudwatch_logs_policy_has_describe_log_streams_action():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert '"logs:DescribeLogStreams"' in content


def test_ecs_task_cloudwatch_logs_policy_targets_github_runner_diag_log_group():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert "/github-runner/diag" in content
