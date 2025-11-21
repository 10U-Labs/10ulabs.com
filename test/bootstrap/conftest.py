import json
import subprocess
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def bootstrap_dir():
    return Path(__file__).parent.parent.parent / "src" / "bootstrap"


@pytest.fixture
def config(bootstrap_dir):
    tfvars_path = bootstrap_dir / "terraform.tfvars"
    config_dict = {}
    with open(tfvars_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                config_dict[key] = value
    return config_dict


@pytest.fixture
def iam_client(config):
    return boto3.client('iam', region_name=config['aws_region'])


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws_region'])


@pytest.fixture
def cloudtrail_client(config):
    return boto3.client('cloudtrail', region_name=config['aws_region'])


@pytest.fixture
def s3_client(config):
    return boto3.client('s3', region_name=config['aws_region'])


@pytest.fixture
def logs_client(config):
    return boto3.client('logs', region_name=config['aws_region'])


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws_region'])


@pytest.fixture
def hosted_zone(route53_client, config):
    zone_id = config['hosted_zone_id']
    response = route53_client.get_hosted_zone(Id=zone_id)
    return response['HostedZone']


@pytest.fixture
def expected_resource_count(bootstrap_dir):
    tf_files = list(bootstrap_dir.glob('*.tf'))
    module_files = list(bootstrap_dir.glob('modules/**/*.tf'))
    all_files = tf_files + module_files

    resource_count = 0
    for tf_file in all_files:
        with open(tf_file, encoding='utf-8') as f:
            content = f.read()
            resource_count += content.count('\nresource "')
            if content.startswith('resource "'):
                resource_count += 1

    return resource_count


@pytest.fixture
def terraform_state_resources(bootstrap_dir):
    result = subprocess.run(
        ['terraform', 'state', 'list'],
        cwd=bootstrap_dir,
        capture_output=True,
        text=True,
        check=True
    )
    resources = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return resources
