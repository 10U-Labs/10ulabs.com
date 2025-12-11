"""Unit tests for test lambda terraform."""
import re


def test_lambda_terraform_file_exists(runners_src_path):
    """Test lambda terraform file exists."""
    lambda_file = runners_src_path / "lambda.tf"
    assert lambda_file.exists()


def test_stale_runner_cleanup_lambda_exists(runners_src_path):
    """Test stale runner cleanup lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "stale_runner_cleanup"' in content


def test_stale_runner_cleanup_has_ec2_managed_by_tag_env_var(runners_src_path):
    """Test stale runner cleanup has ec2 managed by tag env var."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'EC2_MANAGED_BY_TAG' in stale_section


def test_stale_runner_cleanup_has_ecs_cluster_env_var(runners_src_path):
    """Test stale runner cleanup has ecs cluster env var."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'ECS_CLUSTER' in stale_section


def test_stale_runner_cleanup_has_github_repo_env_var(runners_src_path):
    """Test stale runner cleanup has github repo env var."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'GITHUB_REPO' in stale_section


def test_stale_runner_cleanup_has_github_token_env_var(runners_src_path):
    """Test stale runner cleanup has github token env var."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'GITHUB_TOKEN_SECRET_NAME' in stale_section


def test_stale_runner_cleanup_has_workflow_runners_table_env_var(runners_src_path):
    """Test stale runner cleanup has workflow runners table env var."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    assert 'WORKFLOW_RUNNERS_TABLE' in stale_section


def test_runners_handler_lambda_exists(runners_src_path):
    """Test runners handler lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "runners_handler"' in content


def test_circuit_breaker_remediation_lambda_exists(runners_src_path):
    """Test circuit breaker remediation lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_remediation"' in content


def test_dlq_reprocessor_lambda_exists(runners_src_path):
    """Test dlq reprocessor lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "dlq_reprocessor"' in content


def test_circuit_breaker_recovery_lambda_exists(runners_src_path):
    """Test circuit breaker recovery lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_recovery"' in content


def test_drift_recovery_lambda_exists(runners_src_path):
    """Test drift recovery lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "drift_recovery"' in content


def test_spot_interruption_handler_lambda_exists(runners_src_path):
    """Test spot interruption handler lambda exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "spot_interruption_handler"' in content


def test_all_lambdas_use_python313_runtime(runners_src_path):
    """Test all lambdas use python313 runtime."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    lambda_count = content.count('resource "aws_lambda_function"')
    python313_count = len(re.findall(r'runtime\s+=\s+"python3\.13"', content))
    assert python313_count == lambda_count


def test_stale_runner_cleanup_ec2_tag_references_ec2_runner_output(runners_src_path):
    """Test stale runner cleanup ec2 tag references ec2 runner output."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    stale_start = content.find('resource "aws_lambda_function" "stale_runner_cleanup"')
    stale_end = content.find('resource "aws_cloudwatch_log_group" "stale_runner_cleanup"')
    stale_section = content[stale_start:stale_end]
    ec2_managed_by_tag = 'data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag'
    assert ec2_managed_by_tag in stale_section


def test_runners_handler_build_null_resource_exists(runners_src_path):
    """Test runners handler build null_resource exists.

    The Lambda package is built using a null_resource that pip installs
    dependencies and copies source files. This test verifies the build
    step is defined in terraform.
    """
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "null_resource" "runners_handler_build"' in content


def test_runners_handler_build_copies_runner_labels(runners_src_path):
    """Test runners handler build copies runner_labels.py.

    This is a regression test to ensure the Lambda build includes the
    runner_labels module. Without this module, the Lambda will fail at runtime
    with a ModuleNotFoundError when processing webhook events.
    """
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    # Find the null_resource block and check it copies runner_labels
    assert "runner_labels/__init__.py" in content
    assert "runner_labels.py" in content


def test_runners_handler_build_copies_runners_yml(runners_src_path):
    """Test runners handler build copies etc/runners.yml.

    The runner_labels module reads configuration from etc/runners.yml.
    Without this file, the Lambda will fail with FileNotFoundError.
    """
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert "etc/runners.yml" in content


def test_runners_handler_build_installs_pyyaml(runners_src_path):
    """Test runners handler build installs pyyaml dependency.

    The runner_labels module requires pyyaml to parse YAML config.
    The build must pip install from requirements.txt.
    """
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert "pip install" in content
    assert "requirements.txt" in content


def test_runners_handler_requirements_txt_exists(runners_src_path):
    """Test requirements.txt exists for Lambda dependencies."""
    requirements_file = runners_src_path / "lambdas" / "requirements.txt"
    assert requirements_file.exists()


def test_runners_handler_requirements_includes_pyyaml(runners_src_path):
    """Test requirements.txt includes PyYAML dependency."""
    requirements_file = runners_src_path / "lambdas" / "requirements.txt"
    with open(requirements_file, encoding="utf-8") as f:
        content = f.read()
    assert "PyYAML" in content or "pyyaml" in content.lower()
