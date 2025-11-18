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
    assert 'openapi.yaml' in response.text


def test_openapi_yaml_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yaml", timeout=10)
    assert response.status_code == 200


def test_openapi_yaml_contains_paths_section(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yaml", timeout=10)
    assert 'paths:' in response.text


def test_custom_domain_name_works():
    response = requests.get('https://api.10ulabs.com/health', timeout=10)
    assert response.status_code == 200
