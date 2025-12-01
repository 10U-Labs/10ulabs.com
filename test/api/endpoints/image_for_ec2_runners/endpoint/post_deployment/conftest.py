from typing import Any, Dict, Optional

import boto3
import pytest
import requests

from ..helpers import get_api_fqdn, get_aws_region


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture() -> str:
    return get_aws_region()


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture() -> str:
    return f"https://{get_api_fqdn()}"


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region: str) -> Any:
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region: str) -> Any:
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(ssm_client: Any) -> str:
    param_response = ssm_client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value']


@pytest.fixture(name="config", scope="module")
def config_fixture(aws_region: str, api_url: str, api_key: str) -> Dict[str, Any]:
    return {
        'aws_region': aws_region,
        'api_url': api_url,
        'api_key': api_key,
        'ami_purpose_tag': 'Purpose',
        'ami_purpose_value': 'GitHub self-hosted EC2 runner',
        'ami_stable_tag': 'Stable',
    }


def make_authenticated_get(url: str, api_key: str, timeout: int = 10) -> requests.Response:
    headers = {"x-api-key": api_key}
    return requests.get(url, headers=headers, timeout=timeout)


def make_authenticated_post(url: str, api_key: str, json: Optional[Dict[str, Any]] = None, timeout: int = 10) -> requests.Response:
    headers = {"x-api-key": api_key, "x-test-mode": "true"}
    return requests.post(url, json=json, headers=headers, timeout=timeout)
