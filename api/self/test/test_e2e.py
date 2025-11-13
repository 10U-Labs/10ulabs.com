import json
from pathlib import Path
import boto3
import requests
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[1] / "config.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws']['region'])


@pytest.fixture
def api_endpoint(cloudformation_client, config):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])

    for output in outputs:
        if output['OutputKey'] == 'ApiEndpoint':
            return output['OutputValue']

    subdomain = config['domain_names']['subdomain']
    return f"https://{subdomain}"


def test_health_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    assert response.status_code == 200


def test_health_endpoint_returns_json(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    data = response.json()
    assert 'status' in data


def test_health_endpoint_status_is_healthy(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    data = response.json()
    assert data['status'] == 'healthy'


def test_echo_endpoint_returns_200_with_valid_json(api_endpoint):
    payload = {'message': 'test'}
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        json=payload,
        timeout=10
    )
    assert response.status_code == 200


def test_echo_endpoint_echoes_input(api_endpoint):
    payload = {'message': 'hello world', 'number': 42}
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        json=payload,
        timeout=10
    )
    data = response.json()
    assert data['echo'] == payload


def test_echo_endpoint_returns_request_id(api_endpoint):
    payload = {'test': 'data'}
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        json=payload,
        timeout=10
    )
    data = response.json()
    assert 'received_at' in data


def test_invalid_endpoint_returns_404(api_endpoint):
    response = requests.get(f"{api_endpoint}/invalid", timeout=10)
    assert response.status_code == 404


def test_health_endpoint_returns_cors_header(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    assert 'Access-Control-Allow-Origin' in response.headers


def test_health_endpoint_cors_allows_all_origins(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    assert response.headers['Access-Control-Allow-Origin'] == '*'


def test_health_endpoint_returns_json_content_type(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    assert response.headers['Content-Type'] == 'application/json'


def test_echo_endpoint_returns_cors_header(api_endpoint):
    payload = {'test': 'data'}
    response = requests.post(f"{api_endpoint}/v1/echo", json=payload, timeout=10)
    assert 'Access-Control-Allow-Origin' in response.headers


def test_echo_endpoint_cors_allows_all_origins(api_endpoint):
    payload = {'test': 'data'}
    response = requests.post(f"{api_endpoint}/v1/echo", json=payload, timeout=10)
    assert response.headers['Access-Control-Allow-Origin'] == '*'


def test_echo_endpoint_returns_json_content_type(api_endpoint):
    payload = {'test': 'data'}
    response = requests.post(f"{api_endpoint}/v1/echo", json=payload, timeout=10)
    assert response.headers['Content-Type'] == 'application/json'


def test_echo_endpoint_with_invalid_json_returns_400(api_endpoint):
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        data='invalid json',
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    assert response.status_code == 400


def test_echo_endpoint_with_invalid_json_returns_error_message(api_endpoint):
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        data='invalid json',
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    data = response.json()
    assert 'error' in data


def test_echo_endpoint_with_invalid_json_error_is_invalid_json(api_endpoint):
    response = requests.post(
        f"{api_endpoint}/v1/echo",
        data='invalid json',
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    data = response.json()
    assert data['error'] == 'Invalid JSON'


def test_invalid_endpoint_returns_cors_header(api_endpoint):
    response = requests.get(f"{api_endpoint}/invalid", timeout=10)
    assert 'Access-Control-Allow-Origin' in response.headers


def test_invalid_endpoint_returns_json_content_type(api_endpoint):
    response = requests.get(f"{api_endpoint}/invalid", timeout=10)
    assert response.headers['Content-Type'] == 'application/json'
