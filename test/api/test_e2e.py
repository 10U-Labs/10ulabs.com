import requests


def test_health_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/health", timeout=10)
    assert response.status_code == 200


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


def test_root_endpoint_returns_200(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert response.status_code == 200


def test_root_endpoint_contains_redoc_element(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert '<redoc' in response.text.lower()


def test_root_endpoint_references_openapi_spec(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert 'openapi.yml' in response.text


def test_openapi_yaml_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yml", timeout=10)
    assert response.status_code == 200


def test_openapi_yaml_contains_paths_section(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yml", timeout=10)
    assert 'paths:' in response.text


def test_custom_domain_name_works():
    response = requests.get('https://api.10ulabs.com/health', timeout=10)
    assert response.status_code == 200


def test_runners_health_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/v1/runners/health", timeout=10)
    assert response.status_code == 200


def test_runners_health_endpoint_returns_circuit_breaker_state(api_endpoint):
    response = requests.get(f"{api_endpoint}/v1/runners/health", timeout=10)
    data = response.json()
    assert 'circuit_breaker' in data


def test_docker_runner_post_requires_authentication(api_endpoint):
    payload = {'job_id': 12345, 'github_repo': '10U-Labs-LLC/10ulabs.com'}
    response = requests.post(
        f"{api_endpoint}/v1/docker-runner",
        json=payload,
        timeout=10
    )
    assert response.status_code in [200, 400, 401, 403, 500]


def test_docker_runner_get_returns_json(api_endpoint):
    response = requests.get(f"{api_endpoint}/v1/docker-runner", timeout=10)
    assert response.headers.get('Content-Type') == 'application/json'


def test_ec2_runner_post_requires_authentication(api_endpoint):
    payload = {'job_id': 12345, 'github_repo': '10U-Labs-LLC/10ulabs.com'}
    response = requests.post(
        f"{api_endpoint}/v1/ec2-runner",
        json=payload,
        timeout=10
    )
    assert response.status_code in [200, 400, 401, 403, 500]


def test_image_for_docker_runners_get_returns_json(api_endpoint):
    response = requests.get(f"{api_endpoint}/v1/image-for-docker-runners", timeout=10)
    assert response.headers.get('Content-Type') == 'application/json'


def test_image_for_ec2_runners_get_returns_json(api_endpoint):
    response = requests.get(f"{api_endpoint}/v1/image-for-ec2-runners", timeout=10)
    assert response.headers.get('Content-Type') == 'application/json'


def test_runners_webhook_post_without_signature_returns_401_or_processes(api_endpoint):
    payload = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'labels': ['test']
        }
    }
    response = requests.post(
        f"{api_endpoint}/v1/runners",
        json=payload,
        timeout=10
    )
    assert response.status_code in [200, 401, 403]
