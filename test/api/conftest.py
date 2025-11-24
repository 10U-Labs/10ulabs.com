import ast
import re
from pathlib import Path
from typing import Any, Dict, List
import boto3
import pytest


@pytest.fixture(name="tfvars", scope="module")
def tfvars_fixture() -> Dict[str, str]:
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
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


@pytest.fixture(name="cfg")
def cfg_fixture() -> Dict[str, Any]:
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "api" / "terraform.tfvars"
    tfvars = {}
    with open(tfvars_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('['):
                    value = ast.literal_eval(value)
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                tfvars[key] = value

    return {
        "aws": {
            "account_id": tfvars.get("aws_account_id"),
            "region": tfvars.get("aws_region")
        },
        "naming": {
            "vpc_name": tfvars.get("vpc_name")
        },
        "github": {
            "runner_version": tfvars.get("github_runner_version")
        }
    }


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
