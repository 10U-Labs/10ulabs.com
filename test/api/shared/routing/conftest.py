"""Pytest fixtures and configuration for API backend tests."""
from pathlib import Path
from typing import Any, Dict, List

from test.api.conftest import get_runner_labels

import boto3
import pytest
from test_fixtures.config import parse_tfvars_file, parse_locals_file

# Import layer-based test dependency tracking for all test subdirectories
pytest_plugins = ['test_fixtures.aws', 'pytest_layers']


def parse_bootstrap_tfvar(var_name: str) -> str:
    """Parse a variable from bootstrap terraform.tfvars file."""
    base = Path(__file__).parent.parent.parent.parent.parent
    tfvars_path = base / "src" / "bootstrap" / "terraform.tfvars"
    config = parse_tfvars_file(tfvars_path)
    return config.get(var_name, "")


def parse_health_tfvars() -> Dict[str, str]:
    """Parse health endpoint terraform.tfvars configuration."""
    base = Path(__file__).parent.parent.parent.parent.parent
    tfvars_path = base / "src" / "api" / "operational" / "health" / "terraform.tfvars"
    return parse_tfvars_file(tfvars_path)


def _parse_api_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Parse API backend locals.tf file for configuration values."""
    base = Path(__file__).parent.parent.parent.parent.parent
    locals_path = base / "src" / "api" / "shared" / "routing" / "locals.tf"
    config = parse_locals_file(locals_path, shared_config)
    domain_name = shared_config.get('domain_name', '')
    config['domain'] = domain_name
    config['api_fqdn'] = f"api.{domain_name}"
    github_org = shared_config.get('github_org', '')
    github_repo = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


def _add_derived_config(result: Dict[str, str]) -> None:
    """Add derived configuration values based on prefix and lambda function name."""
    prefix = result['resource_prefix']
    stack_name = result.get('stack_name', prefix)
    lambda_fn = result.get('lambda_function_name', '')
    result['circuit_breaker_state_table_name'] = f"{prefix}-circuit-breaker-state"
    result['workflow_runners_table_name'] = f"{prefix}-workflow-runners"
    result['firehose_delivery_stream_name'] = f"{prefix}-CloudWatchLogs"
    result['firehose_role_name'] = f"{prefix}-FirehoseCloudWatchLogs"
    result['cloudwatch_logs_firehose_role_name'] = f"{prefix}-CloudWatchLogsFirehose"
    # API Gateway CloudWatch role uses stack_name (not resource_prefix)
    result['api_gateway_cloudwatch_role_name'] = f"{stack_name}-api-gateway-cloudwatch"
    result['lambda_runners_role_name'] = f"{lambda_fn}-ServiceRole"
    result['webhook_handler_service_role_name'] = f"{lambda_fn}-ServiceRole"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, Any]:
    """Provide merged configuration from terraform files."""
    base = Path(__file__).parent.parent.parent.parent.parent
    tfvars_path = base / "src" / "api" / "shared" / "routing" / "terraform.tfvars"
    result: Dict[str, Any] = dict(parse_tfvars_file(tfvars_path))
    api_locals = _parse_api_locals(shared_config)
    result['aws_region'] = shared_config['aws_region']
    result['aws_account_id'] = api_locals.get('aws_account_id', '')
    result['central_logs_bucket'] = shared_config.get('name_for_central_logs_bucket', '')
    result['domain'] = api_locals.get('domain', '')
    result['api_fqdn'] = api_locals.get('api_fqdn', '')
    result['github_org'] = shared_config.get('github_org', '')
    result['github_repo'] = api_locals.get('github_repo_full', '')
    result['resource_prefix'] = api_locals.get('resource_prefix', '')
    # stack_name is the terraform tfvars value for API Gateway resources
    result['stack_name'] = result.get('stack_name', '')
    ssm_param = parse_bootstrap_tfvar('ssm_parameter_name_for_github_pat')
    result['ssm_parameter_name_for_github_pat'] = ssm_param
    _add_derived_config(result)
    result['ec2_runner_ami_purpose_tag'] = api_locals.get('ec2_runner_ami_purpose_tag', '')
    result['ec2_runner_ami_purpose_value'] = api_locals.get('ec2_runner_ami_purpose_value', '')
    result['ec2_runner_ami_stable_tag'] = api_locals.get('ec2_runner_ami_stable_tag', '')
    result.update(get_runner_labels())
    health_config = parse_health_tfvars()
    result['health_handler_function_name'] = health_config.get('health_handler_function_name', '')
    result['health_handler_log_group_name'] = health_config.get('health_handler_log_group_name', '')
    # Add catchall handler function name from shared_config
    result['catchall_handler_function_name'] = shared_config.get(
        'lambda_handler_names', {}
    ).get('catchall', 'TenULabsCatchAllHandler')
    return result


@pytest.fixture
def sns_client(aws_region):
    """Provide SNS client for the configured AWS region."""
    return boto3.client('sns', region_name=aws_region)


@pytest.fixture(name="dynamodb_client", scope="module")
def dynamodb_client_fixture(aws_region):
    """Provide DynamoDB client for the configured AWS region."""
    return boto3.client('dynamodb', region_name=aws_region)


@pytest.fixture
def cloudwatch_client(aws_region):
    """Provide CloudWatch client for the configured AWS region."""
    return boto3.client('cloudwatch', region_name=aws_region)


@pytest.fixture
def events_client(aws_region):
    """Provide EventBridge client for the configured AWS region."""
    return boto3.client('events', region_name=aws_region)


@pytest.fixture
def logs_client(aws_region):
    """Provide CloudWatch Logs client for the configured AWS region."""
    return boto3.client('logs', region_name=aws_region)


def find_sns_topic_arns(client: Any, topic_name: str) -> List[str]:
    """Find SNS topic ARNs matching the given topic name."""
    topics = client.list_topics()
    topic_arns = [t['TopicArn'] for t in topics['Topics']]
    matching_topics = [t for t in topic_arns if topic_name in t]
    return matching_topics
