import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_simulation_soc_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_riscv(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_x86_64(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "x86_64"}, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_arm64(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "arm64"}, headers=TEST_HEADERS, timeout=10)
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_400_for_invalid_persona(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "invalid"}, headers=TEST_HEADERS, timeout=10)
    is_client_error = response.status_code == 400
    assert is_client_error


def test_simulation_soc_endpoint_returns_400_for_missing_persona(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={}, headers=TEST_HEADERS, timeout=10)
    is_client_error = response.status_code == 400
    assert is_client_error


def test_simulation_soc_endpoint_response_contains_success_field(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_success = 'success' in data
    assert has_success


def test_simulation_soc_endpoint_response_contains_persona_field(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "arm64"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    persona_matches = data.get('persona') == 'arm64'
    assert persona_matches


def test_simulation_soc_endpoint_response_contains_soc_config(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_soc_config = 'soc_config' in data
    assert has_soc_config


def test_simulation_soc_endpoint_response_contains_instruction_count(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_instruction_count = 'instruction_count' in data
    assert has_instruction_count


def test_simulation_soc_endpoint_response_contains_native_core(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_native_core = 'native_core' in data
    assert has_native_core


def test_simulation_soc_endpoint_response_contains_tri_mode_core(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_tri_mode_core = 'tri_mode_core' in data
    assert has_tri_mode_core


def test_simulation_soc_endpoint_response_contains_relative_slowdown(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_slowdown = 'relative_slowdown' in data
    assert has_slowdown


def test_simulation_soc_endpoint_native_core_has_ipc(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_ipc = 'ipc' in data.get('native_core', {})
    assert has_ipc


def test_simulation_soc_endpoint_native_core_has_runtime_seconds(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_runtime = 'runtime_seconds' in data.get('native_core', {})
    assert has_runtime


def test_simulation_soc_endpoint_tri_mode_core_has_ipc(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_ipc = 'ipc' in data.get('tri_mode_core', {})
    assert has_ipc


def test_simulation_soc_endpoint_tri_mode_core_has_runtime_seconds(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "riscv"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_runtime = 'runtime_seconds' in data.get('tri_mode_core', {})
    assert has_runtime


def test_simulation_soc_endpoint_error_response_contains_error_field(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "invalid"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    has_error = 'error' in data
    assert has_error


def test_simulation_soc_endpoint_error_response_success_is_false(api_url):
    response = requests.post(f"{api_url}/v1/simulation-soc", json={"persona": "invalid"}, headers=TEST_HEADERS, timeout=10)
    data = response.json()
    success_is_false = data.get('success') is False
    assert success_is_false
