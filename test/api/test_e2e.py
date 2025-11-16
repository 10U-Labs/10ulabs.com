import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure"))
import poll_api_until_it_has_propagated


def test_api_propagated_and_accessible(api_endpoint):
    result = poll_api_until_it_has_propagated.poll_until_propagated(api_endpoint, max_attempts=11)
    assert result is True


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


def test_root_endpoint_returns_200(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert response.status_code == 200


def test_root_endpoint_returns_html_content_type(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert 'text/html' in response.headers['Content-Type']


def test_root_endpoint_contains_redoc_element(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert '<redoc' in response.text.lower()


def test_root_endpoint_references_openapi_spec(api_endpoint):
    response = requests.get(api_endpoint, timeout=10)
    assert 'openapi.yaml' in response.text


def test_openapi_yaml_endpoint_returns_200(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yaml", timeout=10)
    assert response.status_code == 200


def test_openapi_yaml_returns_yaml_or_text_content_type(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yaml", timeout=10)
    content_type = response.headers['Content-Type']
    assert 'yaml' in content_type or 'text' in content_type or 'octet-stream' in content_type


def test_openapi_yaml_contains_paths_section(api_endpoint):
    response = requests.get(f"{api_endpoint}/openapi.yaml", timeout=10)
    assert 'paths:' in response.text


def test_custom_domain_name_works():
    response = requests.get('https://api.10ulabs.com/health', timeout=10)
    assert response.status_code == 200
