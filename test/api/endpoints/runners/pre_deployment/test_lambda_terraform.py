def test_lambda_terraform_file_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    assert lambda_file.exists()


def test_stale_runner_cleanup_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "stale_runner_cleanup"' in content


def test_stale_runner_cleanup_has_ec2_managed_by_tag_env_var(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'EC2_MANAGED_BY_TAG' in stale_section


def test_stale_runner_cleanup_has_ecs_cluster_env_var(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'ECS_CLUSTER' in stale_section


def test_stale_runner_cleanup_has_github_repo_env_var(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'GITHUB_REPO' in stale_section


def test_stale_runner_cleanup_has_github_token_env_var(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'GITHUB_TOKEN_SECRET_NAME' in stale_section


def test_stale_runner_cleanup_has_workflow_runners_table_env_var(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'WORKFLOW_RUNNERS_TABLE' in stale_section


def test_runners_handler_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "runners_handler"' in content


def test_circuit_breaker_remediation_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_remediation"' in content


def test_dlq_reprocessor_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "dlq_reprocessor"' in content


def test_circuit_breaker_recovery_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_recovery"' in content


def test_drift_recovery_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "drift_recovery"' in content


def test_spot_interruption_handler_lambda_exists(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "spot_interruption_handler"' in content


def test_all_lambdas_use_python313_runtime(runners_src_path):
    import re
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    lambda_count = content.count('resource "aws_lambda_function"')
    python313_count = len(re.findall(r'runtime\s+=\s+"python3\.13"', content))
    assert python313_count == lambda_count


def test_stale_runner_cleanup_ec2_tag_references_ec2_runner_output(runners_src_path):
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag' in stale_section
