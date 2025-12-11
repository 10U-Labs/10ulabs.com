"""Shared pytest fixtures and utilities for runners endpoint tests."""
import importlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from test.api.conftest import get_runner_labels

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
RUNNERS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "runners"
ECS_RUNNER_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"

# Add lib/python to path for unit tests that use --confcutdir
LIB_DIR = REPO_ROOT / "lib" / "python"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def _get_shared_config() -> Dict[str, str]:
    """Load and return shared config using dynamic import."""
    terraform_config = importlib.import_module("terraform_config")
    return terraform_config.get_shared_config()


@pytest.fixture(name="shared_config", scope="session")
def shared_config_fixture() -> Dict[str, str]:
    """Provide shared config for tests using --confcutdir."""
    return _get_shared_config()


@pytest.fixture(name="aws_region", scope="session")
def aws_region_fixture(shared_config) -> str:
    """Provide the AWS region from shared config."""
    return shared_config["aws_region"]


def parse_bootstrap_tfvar(var_name: str) -> str:
    """Parse a variable from bootstrap terraform.tfvars file."""
    tfvars_path = REPO_ROOT / "src" / "bootstrap" / "terraform.tfvars"
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    if key == var_name:
                        return value.strip('"')
    return ""


def _get_runners_locals(shared_config: Dict[str, Any]) -> Dict[str, str]:
    """Get runners locals using terraform_config module (single source of truth)."""
    terraform_config = importlib.import_module("terraform_config")
    config = terraform_config.get_endpoint_local_values(RUNNERS_SRC_PATH)
    config['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    github_org = shared_config.get('github_org', '')
    github_repo = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide configuration dictionary from Terraform files."""
    # Start with all values from runners locals.tf (single source of truth)
    runners_locals = _get_runners_locals(shared_config)
    result: Dict[str, Any] = dict(runners_locals)
    # Override with tfvars if it exists (for backward compatibility)
    tfvars_path = RUNNERS_SRC_PATH / "terraform.tfvars"
    if tfvars_path.exists():
        with open(tfvars_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                    if match:
                        key, value = match.groups()
                        result[key] = value.strip('"')
    # Add computed/derived values
    result['aws_region'] = runners_locals.get(
        'aws_region', shared_config.get('aws_region', '')
    )
    result['aws_account_id'] = runners_locals.get(
        'aws_account_id', shared_config.get('aws_account_id', '')
    )
    result['central_logs_bucket'] = shared_config.get('name_for_central_logs_bucket', '')
    result['api_fqdn'] = runners_locals.get('api_fqdn', '')
    result['github_org'] = shared_config.get('github_org', '')
    result['github_repo'] = runners_locals.get('github_repo_full', '')
    result['resource_prefix'] = runners_locals.get(
        'resource_prefix', shared_config.get('resource_prefix', '')
    )
    result['ssm_parameter_name_for_github_pat'] = parse_bootstrap_tfvar(
        'ssm_parameter_name_for_github_pat'
    )
    result['ssm_parameter_name_for_api_key'] = result.get(
        'ssm_parameter_name_for_api_key', '/api/key'
    )
    prefix = result['resource_prefix']
    lambda_fn = result.get('webhook_handler_function_name', '')
    result['circuit_breaker_state_table_name'] = f"{prefix}-circuit-breaker-state"
    result['workflow_runners_table_name'] = f"{prefix}-workflow-runners"
    result['lambda_runners_role_name'] = f"{lambda_fn}ServiceRole"
    result['webhook_handler_service_role_name'] = f"{lambda_fn}ServiceRole"
    # Log group names derived from Lambda function names (single source of truth: locals.tf)
    for key in ['circuit_breaker_remediation', 'dlq_reprocessor', 'circuit_breaker_recovery']:
        fn_name = result.get(f'{key}_function_name', '')
        result[f'{key}_log_group_name'] = f"/aws/lambda/{fn_name}"
    result.update(get_runner_labels())
    result['api_version'] = 'v1'
    ecs_runner_tfvars = ECS_RUNNER_SRC_PATH / "terraform.tfvars"
    with open(ecs_runner_tfvars, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    if key == 'cluster_name':
                        result['cluster_name'] = value.strip('"')
    return result


@pytest.fixture
def sns_client(aws_region):
    """Provide SNS client for tests."""
    return boto3.client('sns', region_name=aws_region)


@pytest.fixture
def dynamodb_client(aws_region):
    """Provide DynamoDB client for tests."""
    return boto3.client('dynamodb', region_name=aws_region)


@pytest.fixture
def cloudwatch_client(aws_region):
    """Provide CloudWatch client for tests."""
    return boto3.client('cloudwatch', region_name=aws_region)


@pytest.fixture
def events_client(aws_region):
    """Provide EventBridge client for tests."""
    return boto3.client('events', region_name=aws_region)


@pytest.fixture
def logs_client(aws_region):
    """Provide CloudWatch Logs client for tests."""
    return boto3.client('logs', region_name=aws_region)


def find_sns_topic_arns(client: Any, topic_name: str) -> List[str]:
    """Find SNS topic ARNs matching a name pattern."""
    topics = client.list_topics()
    topic_arns = [t['TopicArn'] for t in topics['Topics']]
    matching_topics = [t for t in topic_arns if topic_name in t]
    return matching_topics
