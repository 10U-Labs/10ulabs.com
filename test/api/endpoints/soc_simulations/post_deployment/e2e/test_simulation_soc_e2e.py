"""End-to-end tests for the simulation-soc API endpoint.

E2E tests verify the full user journey from HTTP request to response.
These tests run against the deployed API in production.
"""
import time
import requests


TEST_HEADERS = {"x-test-mode": "true"}


# =============================================================================
# Security Tests
# =============================================================================


def test_simulation_soc_endpoint_has_cors_headers(api_url):
    """Verify endpoint returns CORS headers."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    has_cors = "Access-Control-Allow-Origin" in response.headers
    assert has_cors, "Response missing Access-Control-Allow-Origin header"


def test_simulation_soc_options_returns_cors_headers(api_url):
    """Verify OPTIONS request returns CORS headers for preflight."""
    response = requests.options(
        f"{api_url}/v1/soc-simulations",
        timeout=10
    )
    has_cors_methods = "Access-Control-Allow-Methods" in response.headers
    assert has_cors_methods, "OPTIONS missing Access-Control-Allow-Methods header"


def test_simulation_soc_response_has_json_content_type(api_url):
    """Verify endpoint returns application/json content type."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    content_type = response.headers.get("Content-Type", "")
    is_json = "application/json" in content_type
    assert is_json, f"Content-Type is {content_type}, expected application/json"


def test_simulation_soc_endpoint_handles_missing_content_type(api_url):
    """Verify endpoint handles request without Content-Type header."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        data='{"persona": "riscv"}',
        headers={"x-test-mode": "true"},
        timeout=10
    )
    # Should return either 200 or 400, not 500
    is_not_server_error = response.status_code < 500
    assert is_not_server_error, f"Server error: {response.status_code}"


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_simulation_soc_endpoint_returns_400_for_invalid_json(api_url):
    """Verify endpoint returns 400 for malformed JSON."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        data="not valid json",
        headers={**TEST_HEADERS, "Content-Type": "application/json"},
        timeout=10
    )
    is_bad_request = response.status_code == 400
    assert is_bad_request, f"Expected 400, got {response.status_code}"


def test_simulation_soc_endpoint_error_response_has_error_field(api_url):
    """Verify error response contains error field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "invalid"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_error = "error" in data
    assert has_error, "Error response missing 'error' field"


def test_simulation_soc_endpoint_error_response_success_is_false(api_url):
    """Verify error response has success set to false."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "invalid"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    success_is_false = data.get("success") is False
    assert success_is_false, "Error response 'success' should be False"


def test_simulation_soc_endpoint_returns_400_for_invalid_persona(api_url):
    """Verify endpoint returns 400 for invalid persona."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "invalid_persona"},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_bad_request = response.status_code == 400
    assert is_bad_request, f"Expected 400 for invalid persona, got {response.status_code}"


def test_simulation_soc_endpoint_returns_400_for_missing_persona(api_url):
    """Verify endpoint returns 400 when persona is missing."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_bad_request = response.status_code == 400
    assert is_bad_request, f"Expected 400 for missing persona, got {response.status_code}"


def test_simulation_soc_endpoint_returns_404_for_get_method(api_url):
    """Verify endpoint returns 404 for GET method."""
    response = requests.get(
        f"{api_url}/v1/soc-simulations",
        headers=TEST_HEADERS,
        timeout=10
    )
    is_not_found = response.status_code == 404
    assert is_not_found, f"Expected 404 for GET, got {response.status_code}"


# =============================================================================
# Happy Path Tests
# =============================================================================


def test_simulation_soc_endpoint_accessible_without_auth(api_url):
    """Verify endpoint is accessible in test mode without authentication."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_riscv(api_url):
    """Verify endpoint returns 200 for RISC-V persona."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_desktop64(api_url):
    """Verify endpoint returns 200 for Desktop64 persona."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "desktop64"},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_returns_200_for_mobile64(api_url):
    """Verify endpoint returns 200 for Mobile64 persona."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "mobile64"},
        headers=TEST_HEADERS,
        timeout=10
    )
    is_successful = response.status_code == 200
    assert is_successful


def test_simulation_soc_endpoint_response_contains_success_field(api_url):
    """Verify response contains success field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_success = "success" in data
    assert has_success


def test_simulation_soc_endpoint_response_contains_persona_field(api_url):
    """Verify response contains matching persona field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "mobile64"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    persona_matches = data.get("persona") == "mobile64"
    assert persona_matches


def test_simulation_soc_endpoint_response_contains_soc_config(api_url):
    """Verify response contains soc_config field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_soc_config = "soc_config" in data
    assert has_soc_config


def test_simulation_soc_endpoint_response_contains_instruction_count(api_url):
    """Verify response contains instruction_count field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_instruction_count = "instruction_count" in data
    assert has_instruction_count


def test_simulation_soc_endpoint_response_contains_native_core(api_url):
    """Verify response contains native_core field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_native_core = "native_core" in data
    assert has_native_core


def test_simulation_soc_endpoint_response_contains_tri_mode_core(api_url):
    """Verify response contains tri_mode_core field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_tri_mode_core = "tri_mode_core" in data
    assert has_tri_mode_core


def test_simulation_soc_endpoint_response_contains_relative_slowdown(api_url):
    """Verify response contains relative_slowdown field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_slowdown = "relative_slowdown" in data
    assert has_slowdown


def test_simulation_soc_endpoint_native_core_has_ipc(api_url):
    """Verify native_core contains ipc field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_ipc = "ipc" in data.get("native_core", {})
    assert has_ipc


def test_simulation_soc_endpoint_native_core_has_runtime_seconds(api_url):
    """Verify native_core contains runtime_seconds field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_runtime = "runtime_seconds" in data.get("native_core", {})
    assert has_runtime


def test_simulation_soc_endpoint_tri_mode_core_has_ipc(api_url):
    """Verify tri_mode_core contains ipc field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_ipc = "ipc" in data.get("tri_mode_core", {})
    assert has_ipc


def test_simulation_soc_endpoint_tri_mode_core_has_runtime_seconds(api_url):
    """Verify tri_mode_core contains runtime_seconds field."""
    response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    data = response.json()
    has_runtime = "runtime_seconds" in data.get("tri_mode_core", {})
    assert has_runtime


# =============================================================================
# Performance and Stability Tests
# =============================================================================


def test_simulation_soc_endpoint_stable_over_sequential_requests(api_url):
    """Verify endpoint returns consistent success status over multiple calls."""
    responses = [
        requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": "riscv"},
            headers=TEST_HEADERS,
            timeout=10
        )
        for _ in range(5)
    ]
    statuses = [r.status_code for r in responses]
    all_successful = all(s == 200 for s in statuses)
    assert all_successful


def test_simulation_soc_endpoint_consistent_persona_results(api_url):
    """Verify same persona returns identical IPC values across requests."""
    responses = [
        requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": "mobile64"},
            headers=TEST_HEADERS,
            timeout=10
        )
        for _ in range(3)
    ]
    bodies = [r.json() for r in responses]
    all_same_ipc = len(set(b["native_core"]["ipc"] for b in bodies)) == 1
    assert all_same_ipc


def test_simulation_soc_endpoint_average_response_time_acceptable(api_url):
    """Verify average response time is under 2 seconds."""
    times = []
    for _ in range(5):
        start = time.time()
        requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": "riscv"},
            headers=TEST_HEADERS,
            timeout=10
        )
        times.append(time.time() - start)
    avg_time = sum(times) / len(times)
    acceptable_time = avg_time < 2.0
    assert acceptable_time


def test_simulation_soc_endpoint_no_cold_start_degradation(api_url):
    """Verify no performance degradation after brief pause."""
    first_response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    time.sleep(1)
    second_response = requests.post(
        f"{api_url}/v1/soc-simulations",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    same_status = first_response.status_code == second_response.status_code
    assert same_status


def test_simulation_soc_all_personas_return_valid_json(api_url):
    """Verify all personas return valid JSON with expected fields."""
    personas = ["riscv", "desktop64", "mobile64"]
    results = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        data = response.json()
        has_fields = (
            'success' in data and
            'native_core' in data and
            'tri_mode_core' in data
        )
        results.append(has_fields)
    all_valid = all(results)
    assert all_valid


def test_simulation_soc_relative_slowdown_consistent_per_persona(api_url):
    """Verify relative slowdown values are consistent for same persona."""
    responses = [
        requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": "desktop64"},
            headers=TEST_HEADERS,
            timeout=10
        )
        for _ in range(3)
    ]
    slowdowns = [r.json()["relative_slowdown"] for r in responses]
    all_same_slowdown = len(set(slowdowns)) == 1
    assert all_same_slowdown


def test_simulation_soc_riscv_has_highest_native_ipc(api_url):
    """Verify RISC-V has highest native IPC due to simpler ISA."""
    personas = ["riscv", "desktop64", "mobile64"]
    ipcs = {}
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        ipcs[persona] = response.json()["native_core"]["ipc"]
    riscv_has_highest = ipcs["riscv"] >= ipcs["mobile64"] >= ipcs["desktop64"]
    assert riscv_has_highest


def test_simulation_soc_soc_config_consistent_across_personas(api_url):
    """Verify SoC configuration is identical across all personas."""
    personas = ["riscv", "desktop64", "mobile64"]
    soc_configs = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        soc_configs.append(response.json()["soc_config"])
    all_same_config = soc_configs[0] == soc_configs[1] == soc_configs[2]
    assert all_same_config


def test_simulation_soc_instruction_count_consistent_across_personas(api_url):
    """Verify instruction count is identical across all personas."""
    personas = ["riscv", "desktop64", "mobile64"]
    counts = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/soc-simulations",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        counts.append(response.json()["instruction_count"])
    all_same_count = len(set(counts)) == 1
    assert all_same_count
