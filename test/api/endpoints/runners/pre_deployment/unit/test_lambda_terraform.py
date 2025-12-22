"""Unit tests for runners Lambda terraform configuration.

This module tests the Lambda infrastructure configuration including:
- Lambda function resource definitions
- archive_file data source definitions
- Lambda package contents (regression tests for ImportModuleError)
- Environment variable configuration
"""
from test.api.endpoints.conftest import assert_archive_includes_file

# List of all common modules that must be included in Lambda packages
# that import from common/__init__.py (which imports everything)
COMMON_MODULES = [
    "common/__init__.py",
    "common/aws_clients.py",
    "common/circuit_breaker_utils.py",
    "common/cloudwatch.py",
    "common/ec2_utils.py",
    "common/ecs_utils.py",
    "common/github_api.py",
    "common/lambda_utils.py",
    "common/webhook_ingress.py",
]


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


# =============================================================================
# Archive File Existence Tests
# =============================================================================


def test_runners_handler_archive_file_exists(runners_src_path):
    """Test runners_handler archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "runners_handler"' in content


def test_runner_starter_archive_file_exists(runners_src_path):
    """Test runner_starter archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "runner_starter"' in content


def test_runner_terminator_archive_file_exists(runners_src_path):
    """Test runner_terminator archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "runner_terminator"' in content


def test_ignored_events_archiver_archive_file_exists(runners_src_path):
    """Test ignored_events_archiver archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "ignored_events_archiver"' in content


def test_drift_recovery_archive_file_exists(runners_src_path):
    """Test drift_recovery archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "drift_recovery"' in content


def test_spot_interruption_handler_archive_file_exists(runners_src_path):
    """Test spot_interruption_handler archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "spot_interruption_handler"' in content


def test_stale_runner_cleanup_archive_file_exists(runners_src_path):
    """Test stale_runner_cleanup archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "stale_runner_cleanup"' in content


# =============================================================================
# Lambda Package Contents - Regression Tests for ImportModuleError
#
# These tests ensure that Lambda packages include all required common modules.
# Without these modules, Lambdas fail at runtime with:
#   Runtime.ImportModuleError: No module named 'common.xxx'
#
# The common/__init__.py imports all modules at the top level, so any Lambda
# that imports from common needs ALL modules present, not just the ones it
# directly uses.
# =============================================================================


def test_runners_handler_archive_includes_all_common_modules(runners_src_path):
    """Test runners_handler archive includes all common modules.

    Regression test: The webhook_router.py imports from common.aws_clients,
    common.cloudwatch, and common.webhook_ingress. However, common/__init__.py
    imports from ALL common modules, so all must be present or the Lambda
    fails with ImportModuleError.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "runners_handler", module)


def test_runner_starter_archive_includes_all_common_modules(runners_src_path):
    """Test runner_starter archive includes all common modules.

    Regression test: runner_starter.py imports from common.aws_clients,
    common.cloudwatch, and common.lambda_utils, but common/__init__.py
    requires all modules to be present.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "runner_starter", module)


def test_runner_terminator_archive_includes_all_common_modules(runners_src_path):
    """Test runner_terminator archive includes all common modules.

    Regression test: runner_terminator.py imports from common.aws_clients,
    common.cloudwatch, common.ec2_utils, common.ecs_utils, and
    common.lambda_utils, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "runner_terminator", module)


def test_ignored_events_archiver_archive_includes_all_common_modules(runners_src_path):
    """Test ignored_events_archiver archive includes all common modules.

    Regression test: ignored_events_archiver.py imports from common.aws_clients,
    common.cloudwatch, and common.lambda_utils, but common/__init__.py
    requires all modules to be present.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "ignored_events_archiver", module)


def test_drift_recovery_archive_includes_all_common_modules(runners_src_path):
    """Test drift_recovery archive includes all common modules.

    Regression test: drift_recovery.py imports from common.aws_clients and
    common.github_api, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "drift_recovery", module)


def test_spot_interruption_handler_archive_includes_all_common_modules(runners_src_path):
    """Test spot_interruption_handler archive includes all common modules.

    Regression test: spot_interruption_handler.py imports from common.aws_clients
    and common.github_api, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "spot_interruption_handler", module)


def test_stale_runner_cleanup_archive_includes_all_common_modules(runners_src_path):
    """Test stale_runner_cleanup archive includes all common modules.

    Regression test: stale_runner_cleanup.py imports from common.aws_clients,
    common.ec2_utils, common.ecs_utils, and common.github_api, but
    common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "stale_runner_cleanup", module)


# =============================================================================
# runner_labels.py Inclusion Tests
#
# These tests ensure Lambda packages include the shared runner_labels module.
# =============================================================================


def test_runners_handler_archive_includes_runner_labels(runners_src_path):
    """Test runners_handler archive includes runner_labels.py shared module.

    Regression test: webhook_router.py imports get_runner_type_from_labels
    from runner_labels. Without this module, the Lambda fails with
    ImportModuleError when processing workflow_job events.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(lambda_file, "runners_handler", "runner_labels.py")


def test_runner_starter_archive_includes_runner_labels(runners_src_path):
    """Test runner_starter archive includes runner_labels.py shared module."""
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(lambda_file, "runner_starter", "runner_labels.py")


def test_spot_interruption_handler_archive_includes_runner_labels(runners_src_path):
    """Test spot_interruption_handler archive includes runner_labels.py."""
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "spot_interruption_handler", "runner_labels.py"
    )


# =============================================================================
# runners.json Config File Inclusion Tests
# =============================================================================


def test_runners_handler_archive_includes_runners_config(runners_src_path):
    """Test runners_handler archive includes etc/runners.json config."""
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(lambda_file, "runners_handler", "etc/runners.json")


def test_runner_starter_archive_includes_runners_config(runners_src_path):
    """Test runner_starter archive includes etc/runners.json config."""
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(lambda_file, "runner_starter", "etc/runners.json")


# =============================================================================
# Circuit Breaker Lambda Archive File Existence Tests
# =============================================================================


def test_circuit_breaker_reset_archive_file_exists(runners_src_path):
    """Test circuit_breaker_reset archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "circuit_breaker_reset"' in content


def test_circuit_breaker_remediation_archive_file_exists(runners_src_path):
    """Test circuit_breaker_remediation archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "circuit_breaker_remediation"' in content


def test_circuit_breaker_recovery_archive_file_exists(runners_src_path):
    """Test circuit_breaker_recovery archive_file data source exists."""
    lambda_file = runners_src_path / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "circuit_breaker_recovery"' in content


# =============================================================================
# Circuit Breaker Lambda Package Contents Tests
#
# These tests ensure circuit breaker Lambda packages include all required
# common modules. These Lambdas import from common.circuit_breaker_utils,
# which triggers common/__init__.py to import all modules.
# =============================================================================


def test_circuit_breaker_reset_archive_includes_all_common_modules(runners_src_path):
    """Test circuit_breaker_reset archive includes all common modules.

    Regression test: circuit_breaker_reset.py imports from
    common.circuit_breaker_utils, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "circuit_breaker_reset", module)


def test_circuit_breaker_remediation_archive_includes_all_common_modules(runners_src_path):
    """Test circuit_breaker_remediation archive includes all common modules.

    Regression test: circuit_breaker_remediation.py imports from
    common.circuit_breaker_utils, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "circuit_breaker_remediation", module)


def test_circuit_breaker_recovery_archive_includes_all_common_modules(runners_src_path):
    """Test circuit_breaker_recovery archive includes all common modules.

    Regression test: circuit_breaker_recovery.py imports from
    common.circuit_breaker_utils, but common/__init__.py requires all modules.
    """
    lambda_file = runners_src_path / "lambda.tf"
    for module in COMMON_MODULES:
        assert_archive_includes_file(lambda_file, "circuit_breaker_recovery", module)


# =============================================================================
# Circuit Breaker Lambda runner_labels.py Inclusion Tests
# =============================================================================


def test_circuit_breaker_reset_archive_includes_runner_labels(runners_src_path):
    """Test circuit_breaker_reset archive includes runner_labels.py.

    Required because common/__init__.py imports from runner_labels.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(lambda_file, "circuit_breaker_reset", "runner_labels.py")


def test_circuit_breaker_remediation_archive_includes_runner_labels(runners_src_path):
    """Test circuit_breaker_remediation archive includes runner_labels.py.

    Required because common/__init__.py imports from runner_labels.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "circuit_breaker_remediation", "runner_labels.py"
    )


def test_circuit_breaker_recovery_archive_includes_runner_labels(runners_src_path):
    """Test circuit_breaker_recovery archive includes runner_labels.py.

    Required because common/__init__.py imports from runner_labels.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "circuit_breaker_recovery", "runner_labels.py"
    )


# =============================================================================
# Circuit Breaker Lambda runners.json Config Inclusion Tests
#
# runner_labels.py loads etc/runners.json at module load time, so all Lambdas
# that import from common need this config file.
# =============================================================================


def test_circuit_breaker_reset_archive_includes_runners_config(runners_src_path):
    """Test circuit_breaker_reset archive includes etc/runners.json.

    Required because runner_labels.py loads this config at import time.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "circuit_breaker_reset", "etc/runners.json"
    )


def test_circuit_breaker_remediation_archive_includes_runners_config(runners_src_path):
    """Test circuit_breaker_remediation archive includes etc/runners.json.

    Required because runner_labels.py loads this config at import time.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "circuit_breaker_remediation", "etc/runners.json"
    )


def test_circuit_breaker_recovery_archive_includes_runners_config(runners_src_path):
    """Test circuit_breaker_recovery archive includes etc/runners.json.

    Required because runner_labels.py loads this config at import time.
    """
    lambda_file = runners_src_path / "lambda.tf"
    assert_archive_includes_file(
        lambda_file, "circuit_breaker_recovery", "etc/runners.json"
    )
