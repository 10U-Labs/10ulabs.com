import os
import re
from pathlib import Path
from typing import Any, Dict, List
import boto3
import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
RUNNERS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


def parse_shared_config() -> Dict[str, Any]:
    config_path = REPO_ROOT / "etc" / "runners.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_shared_module_outputs() -> Dict[str, str]:
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config


def get_bootstrap_output(output_name: str, default: str = "") -> str:
    env_var_name = output_name.upper()
    return os.environ.get(env_var_name, default)


def parse_runners_locals() -> Dict[str, str]:
    locals_path = RUNNERS_SRC_PATH / "locals.tf"
    shared = parse_shared_module_outputs()
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
                        config[key] = shared.get(ref, '')
    config['api_fqdn'] = f"api.{shared.get('domain_name', '')}"
    config['github_repo_full'] = f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    tfvars_path = RUNNERS_SRC_PATH / "terraform.tfvars"
    result = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    shared = parse_shared_module_outputs()
    runners_locals = parse_runners_locals()
    result['aws_region'] = runners_locals.get('aws_region', shared.get('aws_region', ''))
    result['aws_account_id'] = runners_locals.get('aws_account_id', shared.get('aws_account_id', ''))
    result['central_logs_bucket'] = shared.get('name_for_central_logs_bucket', '')
    result['api_fqdn'] = runners_locals.get('api_fqdn', '')
    result['github_org'] = shared.get('github_org', '')
    result['github_repo'] = runners_locals.get('github_repo_full', '')
    result['resource_prefix'] = runners_locals.get('resource_prefix', shared.get('resource_prefix', ''))
    result['ssm_parameter_name_for_github_pat'] = get_bootstrap_output('ssm_parameter_name_for_github_pat', '/test/github/pat')
    result['ssm_parameter_name_for_api_key'] = result.get('ssm_parameter_name_for_api_key', '/api/key')
    prefix = result['resource_prefix']
    lambda_fn = result.get('webhook_handler_function_name', '')
    result['circuit_breaker_state_table_name'] = f"{prefix}-circuit-breaker-state"
    result['workflow_runners_table_name'] = f"{prefix}-workflow-runners"
    result['lambda_runners_role_name'] = f"{lambda_fn}-ServiceRole"
    result['webhook_handler_service_role_name'] = f"{lambda_fn}-ServiceRole"
    result['circuit_breaker_remediation_log_group_name'] = f"/aws/lambda/{prefix}-CircuitBreakerRemediation"
    result['dlq_reprocessor_log_group_name'] = f"/aws/lambda/{prefix}-DLQReprocessor"
    result['circuit_breaker_recovery_log_group_name'] = f"/aws/lambda/{prefix}-CircuitBreakerRecovery"
    shared_config = parse_shared_config()
    runner_labels = shared_config.get('runner_labels', {})
    result['runner_label_ec2_spot'] = runner_labels.get('ec2_spot', '')
    result['runner_label_fargate_spot'] = runner_labels.get('fargate_spot', '')
    result['runner_label_ec2_spot_e2e_test'] = runner_labels.get('ec2_spot_e2e_test', '')
    result['runner_label_fargate_spot_e2e_test'] = runner_labels.get('fargate_spot_e2e_test', '')
    result['api_version'] = 'v1'
    return result


@pytest.fixture
def sns_client():
    return boto3.client('sns', region_name='us-east-1')


@pytest.fixture
def dynamodb_client():
    return boto3.client('dynamodb', region_name='us-east-1')


@pytest.fixture
def lambda_client():
    return boto3.client('lambda', region_name='us-east-1')


@pytest.fixture
def cloudwatch_client():
    return boto3.client('cloudwatch', region_name='us-east-1')


@pytest.fixture
def events_client():
    return boto3.client('events', region_name='us-east-1')


@pytest.fixture
def logs_client():
    return boto3.client('logs', region_name='us-east-1')


def find_sns_topic_arns(client: Any, topic_name: str) -> List[str]:
    topics = client.list_topics()
    topic_arns = [t['TopicArn'] for t in topics['Topics']]
    matching_topics = [t for t in topic_arns if topic_name in t]
    return matching_topics
