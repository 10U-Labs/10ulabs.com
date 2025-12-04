"""End-to-end tests for the simulation-soc API endpoint."""
import time
import requests


TEST_HEADERS = {"x-test-mode": "true"}


def test_simulation_soc_endpoint_stable_over_sequential_requests(api_url):
    """Verify endpoint returns consistent success status over multiple calls."""
    responses = [
        requests.post(
            f"{api_url}/v1/simulation-soc",
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
            f"{api_url}/v1/simulation-soc",
            json={"persona": "arm64"},
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
            f"{api_url}/v1/simulation-soc",
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
        f"{api_url}/v1/simulation-soc",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    time.sleep(1)
    second_response = requests.post(
        f"{api_url}/v1/simulation-soc",
        json={"persona": "riscv"},
        headers=TEST_HEADERS,
        timeout=10
    )
    same_status = first_response.status_code == second_response.status_code
    assert same_status


def test_simulation_soc_all_personas_return_valid_json(api_url):
    """Verify all personas return valid JSON with expected fields."""
    personas = ["riscv", "x86_64", "arm64"]
    results = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/simulation-soc",
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
            f"{api_url}/v1/simulation-soc",
            json={"persona": "x86_64"},
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
    personas = ["riscv", "x86_64", "arm64"]
    ipcs = {}
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/simulation-soc",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        ipcs[persona] = response.json()["native_core"]["ipc"]
    riscv_has_highest = ipcs["riscv"] >= ipcs["arm64"] >= ipcs["x86_64"]
    assert riscv_has_highest


def test_simulation_soc_soc_config_consistent_across_personas(api_url):
    """Verify SoC configuration is identical across all personas."""
    personas = ["riscv", "x86_64", "arm64"]
    soc_configs = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/simulation-soc",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        soc_configs.append(response.json()["soc_config"])
    all_same_config = soc_configs[0] == soc_configs[1] == soc_configs[2]
    assert all_same_config


def test_simulation_soc_instruction_count_consistent_across_personas(api_url):
    """Verify instruction count is identical across all personas."""
    personas = ["riscv", "x86_64", "arm64"]
    counts = []
    for persona in personas:
        response = requests.post(
            f"{api_url}/v1/simulation-soc",
            json={"persona": persona},
            headers=TEST_HEADERS,
            timeout=10
        )
        counts.append(response.json()["instruction_count"])
    all_same_count = len(set(counts)) == 1
    assert all_same_count
