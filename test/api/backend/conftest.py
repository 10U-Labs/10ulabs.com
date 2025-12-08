"""Pytest fixtures and configuration for API backend tests."""
import re
from pathlib import Path
from typing import Any, Dict, List

from test.api.conftest import get_runner_labels

import boto3
import pytest


def parse_bootstrap_tfvar(var_name: str) -> str:
    """Parse a variable from bootstrap terraform.tfvars file."""
    base = Path(__file__).parent.parent.parent.parent
    tfvars_path = base / "src" / "bootstrap" / "terraform.tfvars"
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


def parse_health_tfvars() -> Dict[str, str]:
    """Parse health endpoint terraform.tfvars configuration."""
    base = Path(__file__).parent.parent.parent.parent
    tfvars_path = base / "src" / "api" / "endpoints" / "health" / "terraform.tfvars"
    config = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip('"')
    return config


def _parse_api_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Parse API backend locals.tf file for configuration values."""
    base = Path(__file__).parent.parent.parent.parent
    locals_path = base / "src" / "api" / "backend" / "locals.tf"
    config = {}
    with open(locals_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('locals'):
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        config[key] = value[1:-1]
                    elif 'module.shared.' in value:
                        ref = value.replace('module.shared.', '').strip()
                        config[key] = shared_config.get(ref, '')
    config['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    github_org = shared_config.get('github_org', '')
    github_repo = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


def _add_derived_config(result: Dict[str, str]) -> None:
    """Add derived configuration values based on prefix and lambda function name."""
    prefix = result['resource_prefix']
    lambda_fn = result.get('lambda_function_name', '')
    result['circuit_breaker_state_table_name'] = f"{prefix}-circuit-breaker-state"
    result['workflow_runners_table_name'] = f"{prefix}-workflow-runners"
    result['firehose_delivery_stream_name'] = f"{prefix}-CloudWatchLogs"
    result['firehose_role_name'] = f"{prefix}-FirehoseCloudWatchLogs"
    result['cloudwatch_logs_firehose_role_name'] = f"{prefix}-CloudWatchLogsFirehose"
    result['lambda_runners_role_name'] = f"{lambda_fn}-ServiceRole"
    result['webhook_handler_service_role_name'] = f"{lambda_fn}-ServiceRole"
    result['circuit_breaker_remediation_log_group_name'] = (
        f"/aws/lambda/{prefix}-CircuitBreakerRemediation"
    )
    result['dlq_reprocessor_log_group_name'] = f"/aws/lambda/{prefix}-DLQReprocessor"
    result['circuit_breaker_recovery_log_group_name'] = (
        f"/aws/lambda/{prefix}-CircuitBreakerRecovery"
    )


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide merged configuration from terraform files."""
    base = Path(__file__).parent.parent.parent.parent
    tfvars_path = base / "src" / "api" / "backend" / "terraform.tfvars"
    result = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    api_locals = _parse_api_locals(shared_config)
    result['aws_region'] = api_locals.get('aws_region', '')
    result['aws_account_id'] = api_locals.get('aws_account_id', '')
    result['central_logs_bucket'] = shared_config.get('name_for_central_logs_bucket', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_org'] = shared_config.get('github_org', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    ssm_param = parse_bootstrap_tfvar('ssm_parameter_name_for_github_pat')
    result['ssm_parameter_name_for_github_pat'] = ssm_param
    _add_derived_config(result)
    result['ec2_runner_ami_purpose_tag'] = api_locals.get('ec2_runner_ami_purpose_tag', '')
    result['ec2_runner_ami_purpose_value'] = api_locals.get('ec2_runner_ami_purpose_value', '')
    result['ec2_runner_ami_stable_tag'] = api_locals.get('ec2_runner_ami_stable_tag', '')
    result['ecr_repository_name'] = shared_config.get('ecr_repository_name', '')
    result.update(get_runner_labels())
    health_config = parse_health_tfvars()
    result['health_handler_function_name'] = health_config.get('health_handler_function_name', '')
    result['health_handler_log_group_name'] = health_config.get('health_handler_log_group_name', '')
    return result


@pytest.fixture
def sns_client():
    """Provide SNS client for us-east-1."""
    return boto3.client('sns', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    """Provide DynamoDB client for us-east-1."""
    return boto3.client('dynamodb', region_name='us-east-1')


@pytest.fixture
def lambda_client():
    """Provide Lambda client for us-east-1."""
    return boto3.client('lambda', region_name='us-east-1')


@pytest.fixture
def cloudwatch_client():
    """Provide CloudWatch client for us-east-1."""
    return boto3.client('cloudwatch', region_name='us-east-1')


@pytest.fixture
def events_client():
    """Provide EventBridge client for us-east-1."""
    return boto3.client('events', region_name='us-east-1')


@pytest.fixture
def logs_client():
    """Provide CloudWatch Logs client for us-east-1."""
    return boto3.client('logs', region_name='us-east-1')


def find_sns_topic_arns(client: Any, topic_name: str) -> List[str]:
    """Find SNS topic ARNs matching the given topic name."""
    topics = client.list_topics()
    topic_arns = [t['TopicArn'] for t in topics['Topics']]
    matching_topics = [t for t in topic_arns if topic_name in t]
    return matching_topics
