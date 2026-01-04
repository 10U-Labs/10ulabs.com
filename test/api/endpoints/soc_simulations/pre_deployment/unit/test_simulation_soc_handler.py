"""Unit tests for the simulation-soc Lambda handler."""
import json
from typing import Any, Dict


def parse_response_body(response: Dict[str, Any]) -> Any:
    """Parse JSON body from Lambda response."""
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    """Assert the response has the expected HTTP status code."""
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    """Assert the response has JSON content type header."""
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    """Assert the response has CORS headers."""
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_handler_returns_200_for_riscv_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 200 for RISC-V persona."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_returns_200_for_desktop64_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 200 for Desktop64 persona."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'desktop64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_returns_200_for_mobile64_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 200 for Mobile64 persona."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'mobile64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_returns_json_content_type(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns JSON content type."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


def test_handler_returns_cors_header(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns CORS headers."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_handler_returns_400_for_invalid_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 400 for invalid persona."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handler_returns_400_for_missing_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 400 when persona is missing."""
    event = simulation_soc_post_event_factory(body_data={})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handler_returns_400_for_invalid_json(simulation_soc_handler, lambda_context):
    """Verify handler returns 400 for invalid JSON body."""
    event = {
        'path': '/v1/soc-simulations',
        'httpMethod': 'POST',
        'body': 'not valid json',
        'headers': {'Content-Type': 'application/json', 'x-test-mode': 'true'},
        'requestContext': {'requestId': 'test-request-id'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handler_options_returns_200(simulation_soc_handler, lambda_context):
    """Verify handler returns 200 for OPTIONS request."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_unknown_route_returns_404(simulation_soc_handler, lambda_context):
    """Verify handler returns 404 for unknown route."""
    event = {'path': '/v1/unknown', 'httpMethod': 'POST', 'body': '{}'}
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 404


def test_response_contains_success_field(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains success field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_success = 'success' in body
    assert has_success


def test_response_success_is_true_for_valid_request(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify success is true for valid request."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    success_is_true = body['success'] is True
    assert success_is_true


def test_response_contains_persona_field(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains matching persona field."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'mobile64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    persona_matches = body['persona'] == 'mobile64'
    assert persona_matches


def test_response_contains_soc_config(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains soc_config field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_soc_config = 'soc_config' in body
    assert has_soc_config


def test_response_soc_config_has_issue_width(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains issue_width field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_issue_width = 'issue_width' in body['soc_config']
    assert has_issue_width


def test_response_soc_config_has_rob_entries(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains rob_entries field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_rob_entries = 'rob_entries' in body['soc_config']
    assert has_rob_entries


def test_response_soc_config_has_l1_size_kb(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains l1_size_kb field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l1_size = 'l1_size_kb' in body['soc_config']
    assert has_l1_size


def test_response_soc_config_has_l2_size_kb(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains l2_size_kb field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l2_size = 'l2_size_kb' in body['soc_config']
    assert has_l2_size


def test_response_soc_config_has_clock_ghz(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains clock_ghz field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_clock = 'clock_ghz' in body['soc_config']
    assert has_clock


def test_response_contains_instruction_count(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains instruction_count field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_instruction_count = 'instruction_count' in body
    assert has_instruction_count


def test_response_contains_native_core(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains native_core field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_native_core = 'native_core' in body
    assert has_native_core


def test_response_native_core_has_ipc(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains ipc field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ipc = 'ipc' in body['native_core']
    assert has_ipc


def test_response_native_core_has_runtime_seconds(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains runtime_seconds field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_runtime = 'runtime_seconds' in body['native_core']
    assert has_runtime


def test_response_contains_tri_mode_core(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains tri_mode_core field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_tri_mode_core = 'tri_mode_core' in body
    assert has_tri_mode_core


def test_response_tri_mode_core_has_ipc(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri_mode_core contains ipc field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ipc = 'ipc' in body['tri_mode_core']
    assert has_ipc


def test_response_tri_mode_core_has_runtime_seconds(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri_mode_core contains runtime_seconds field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_runtime = 'runtime_seconds' in body['tri_mode_core']
    assert has_runtime


def test_response_contains_relative_slowdown(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify response contains relative_slowdown field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_slowdown = 'relative_slowdown' in body
    assert has_slowdown


def test_tri_mode_ipc_is_less_than_native_ipc_for_desktop64(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri-mode IPC is less than native for Desktop64."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'desktop64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    tri_mode_slower = body['tri_mode_core']['ipc'] < body['native_core']['ipc']
    assert tri_mode_slower


def test_relative_slowdown_is_greater_than_one_for_desktop64(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify relative slowdown is greater than 1 for Desktop64."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'desktop64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown_greater_than_one = body['relative_slowdown'] > 1.0
    assert slowdown_greater_than_one


def test_tri_mode_ipc_is_less_than_native_ipc_for_mobile64(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri-mode IPC is less than native for Mobile64."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'mobile64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    tri_mode_slower = body['tri_mode_core']['ipc'] < body['native_core']['ipc']
    assert tri_mode_slower


def test_relative_slowdown_is_greater_than_one_for_mobile64(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify relative slowdown is greater than 1 for Mobile64."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'mobile64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown_greater_than_one = body['relative_slowdown'] > 1.0
    assert slowdown_greater_than_one


def test_riscv_trimode_has_zero_ipc_overhead(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify RISC-V has zero IPC overhead in tri-mode."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    native_ipc = body['native_core']['ipc']
    trimode_ipc = body['tri_mode_core']['ipc']
    ipc_equal = abs(trimode_ipc - native_ipc) < 0.0001
    assert ipc_equal


def test_riscv_relative_slowdown_is_one(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify RISC-V relative slowdown is 1.0."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown = body['relative_slowdown']
    slowdown_is_one = abs(slowdown - 1.0) < 0.0001
    assert slowdown_is_one


def test_error_response_contains_success_false(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify error response has success=false."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    success_is_false = body['success'] is False
    assert success_is_false


def test_error_response_contains_error_field(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify error response contains error field."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_error = 'error' in body
    assert has_error


def test_error_response_contains_details_for_invalid_persona(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify error response contains details for invalid persona."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_details = 'details' in body
    assert has_details


def test_native_core_ipc_is_positive(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native core IPC is positive."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    ipc_positive = body['native_core']['ipc'] > 0
    assert ipc_positive


def test_native_core_runtime_is_positive(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native core runtime is positive."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    runtime_positive = body['native_core']['runtime_seconds'] > 0
    assert runtime_positive


def test_tri_mode_core_ipc_is_positive(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri-mode core IPC is positive."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    ipc_positive = body['tri_mode_core']['ipc'] > 0
    assert ipc_positive


def test_tri_mode_core_runtime_is_positive(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri-mode core runtime is positive."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    runtime_positive = body['tri_mode_core']['runtime_seconds'] > 0
    assert runtime_positive


def test_derive_translation_uops_averages_ranges(simulation_soc_handler):
    """Verify derive_translation_uops computes correct averages."""
    ranges = {'alu': (1, 3), 'load': (2, 4)}
    result = simulation_soc_handler.derive_translation_uops(ranges)
    correct_average = result['alu'] == 2.0 and result['load'] == 3.0
    assert correct_average


def test_json_response_has_status_code(simulation_soc_handler):
    """Verify json_response includes status code."""
    response = simulation_soc_handler.json_response(200, {'test': 'data'})
    has_status = response['statusCode'] == 200
    assert has_status


def test_json_response_has_json_body(simulation_soc_handler):
    """Verify json_response has JSON-encoded body."""
    response = simulation_soc_handler.json_response(200, {'test': 'data'})
    body = json.loads(response['body'])
    body_correct = body['test'] == 'data'
    assert body_correct


def test_json_response_has_cors_headers(simulation_soc_handler):
    """Verify json_response includes CORS headers."""
    response = simulation_soc_handler.json_response(200, {})
    has_cors = 'Access-Control-Allow-Origin' in response['headers']
    assert has_cors


def test_error_response_without_details(simulation_soc_handler):
    """Verify error_response works without details."""
    response = simulation_soc_handler.error_response(400, 'Test error')
    body = json.loads(response['body'])
    no_details = 'details' not in body
    assert no_details


def test_error_response_with_details(simulation_soc_handler):
    """Verify error_response includes details when provided."""
    response = simulation_soc_handler.error_response(400, 'Test error', 'Test details')
    body = json.loads(response['body'])
    has_details = body['details'] == 'Test details'
    assert has_details


def test_parse_body_with_string(simulation_soc_handler):
    """Verify parse_body handles string body."""
    event = {'body': '{"key": "value"}'}
    result = simulation_soc_handler.parse_body(event)
    parsed_correctly = result['key'] == 'value'
    assert parsed_correctly


def test_parse_body_with_dict(simulation_soc_handler):
    """Verify parse_body handles dict body."""
    event = {'body': {'key': 'value'}}
    result = simulation_soc_handler.parse_body(event)
    parsed_correctly = result['key'] == 'value'
    assert parsed_correctly


def test_build_soc_config_output_has_issue_width(simulation_soc_handler):
    """Verify build_soc_config_output includes issue_width."""
    config = simulation_soc_handler.build_soc_config_output()
    has_issue_width = 'issue_width' in config
    assert has_issue_width


def test_build_soc_config_output_has_clock_ghz(simulation_soc_handler):
    """Verify build_soc_config_output includes clock_ghz."""
    config = simulation_soc_handler.build_soc_config_output()
    has_clock = 'clock_ghz' in config
    assert has_clock


def test_compute_uop_counts_returns_total_uops(simulation_soc_handler):
    """Verify compute_uop_counts returns total_uops."""
    result = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    has_total = 'total_uops' in result
    assert has_total


def test_compute_uop_counts_total_is_positive(simulation_soc_handler):
    """Verify compute_uop_counts total is positive."""
    result = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    total_positive = result['total_uops'] > 0
    assert total_positive


def test_compute_frontend_ipc_returns_ipc(simulation_soc_handler):
    """Verify compute_frontend_ipc returns ipc_frontend."""
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_frontend_ipc('riscv', uop_stats)
    has_ipc = 'ipc_frontend' in result
    assert has_ipc


def test_compute_frontend_ipc_trimode_lower_for_desktop64(simulation_soc_handler):
    """Verify frontend IPC is lower for tri-mode Desktop64."""
    uop_stats = simulation_soc_handler.compute_uop_counts('desktop64', 1000)
    adjusted = simulation_soc_handler.compute_adjusted_uop_stats('desktop64', 1000)
    native = simulation_soc_handler.compute_frontend_ipc('desktop64', uop_stats)
    trimode = simulation_soc_handler.compute_frontend_ipc('desktop64', adjusted)
    trimode_lower = trimode['ipc_frontend'] < native['ipc_frontend']
    assert trimode_lower


def test_compute_backend_ipc_returns_ipc(simulation_soc_handler):
    """Verify backend IPC computation returns ipc_backend field."""
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_backend_ipc('riscv', uop_stats, 1000)
    has_ipc = 'ipc_backend' in result
    assert has_ipc


def test_compute_backend_ipc_is_positive(simulation_soc_handler):
    """Verify backend IPC is a positive value."""
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_backend_ipc('riscv', uop_stats, 1000)
    ipc_positive = result['ipc_backend'] > 0
    assert ipc_positive


def test_compute_memory_stall_cpi_is_positive(simulation_soc_handler):
    """Verify memory stall CPI is a positive value."""
    workload = simulation_soc_handler.WORKLOADS['riscv']
    result = simulation_soc_handler.compute_memory_stall_cpi(workload, 1000, 1000)
    cpi_positive = result > 0
    assert cpi_positive


def test_compute_native_simulation_returns_ipc(simulation_soc_handler):
    """Verify native simulation returns ipc field."""
    result = simulation_soc_handler.compute_native_simulation('riscv')
    has_ipc = 'ipc' in result
    assert has_ipc


def test_compute_native_simulation_returns_runtime(simulation_soc_handler):
    """Verify native simulation returns runtime_seconds field."""
    result = simulation_soc_handler.compute_native_simulation('riscv')
    has_runtime = 'runtime_seconds' in result
    assert has_runtime


def test_compute_trimode_simulation_returns_ipc(simulation_soc_handler):
    """Verify tri-mode simulation returns ipc field."""
    result = simulation_soc_handler.compute_trimode_simulation('riscv')
    has_ipc = 'ipc' in result
    assert has_ipc


def test_compute_trimode_simulation_ipc_less_than_native_for_desktop64(simulation_soc_handler):
    """Verify tri-mode IPC is lower than native for Desktop64."""
    native = simulation_soc_handler.compute_native_simulation('desktop64')
    trimode = simulation_soc_handler.compute_trimode_simulation('desktop64')
    trimode_lower = trimode['ipc'] < native['ipc']
    assert trimode_lower


def test_compute_resource_limited_upc_is_positive(simulation_soc_handler):
    """Verify resource-limited UPC is a positive value."""
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_resource_limited_upc(uop_stats)
    upc_positive = result > 0
    assert upc_positive


def test_desktop64_has_more_uops_than_riscv(simulation_soc_handler):
    """Verify Desktop64 generates more micro-ops than RISC-V."""
    riscv_uops = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    desktop64_uops = simulation_soc_handler.compute_uop_counts('desktop64', 1000)
    desktop64_more = desktop64_uops['total_uops'] > riscv_uops['total_uops']
    assert desktop64_more


def test_riscv_native_ipc_higher_than_desktop64(simulation_soc_handler):
    """Verify RISC-V native IPC is higher than Desktop64."""
    riscv = simulation_soc_handler.compute_native_simulation('riscv')
    desktop64 = simulation_soc_handler.compute_native_simulation('desktop64')
    riscv_higher = riscv['ipc'] > desktop64['ipc']
    assert riscv_higher


def test_compute_flags_overhead_uops_zero_for_riscv(simulation_soc_handler):
    """Verify flags overhead is zero for RISC-V (no flags register)."""
    result = simulation_soc_handler.compute_flags_overhead_uops('riscv', 1000)
    is_zero = result == 0.0
    assert is_zero


def test_compute_flags_overhead_uops_positive_for_desktop64(simulation_soc_handler):
    """Verify flags overhead is positive for Desktop64."""
    result = simulation_soc_handler.compute_flags_overhead_uops('desktop64', 1000)
    is_positive = result > 0
    assert is_positive


def test_compute_fence_stall_cycles_zero_for_riscv(simulation_soc_handler):
    """Verify fence stall cycles are zero for RISC-V."""
    result = simulation_soc_handler.compute_fence_stall_cycles('riscv', 1000)
    is_zero = result == 0.0
    assert is_zero


def test_compute_fence_stall_cycles_zero_for_desktop64_with_hardware_tso(simulation_soc_handler):
    """Verify fence stall cycles are zero for Desktop64 with hardware TSO."""
    result = simulation_soc_handler.compute_fence_stall_cycles('desktop64', 1000)
    is_zero = result == 0.0
    assert is_zero


def test_compute_trimode_mispredict_penalty_equals_base_with_unified_decode(
        simulation_soc_handler):
    """Verify mispredict penalty equals base penalty with unified decode."""
    result = simulation_soc_handler.compute_trimode_mispredict_penalty('riscv')
    base_penalty = simulation_soc_handler.LATENCIES['branch_mispredict']
    equals_base = result == base_penalty
    assert equals_base


def test_compute_trimode_mispredict_penalty_same_for_all_personas(simulation_soc_handler):
    """Verify mispredict penalty is the same for all personas."""
    riscv = simulation_soc_handler.compute_trimode_mispredict_penalty('riscv')
    desktop64 = simulation_soc_handler.compute_trimode_mispredict_penalty('desktop64')
    mobile64 = simulation_soc_handler.compute_trimode_mispredict_penalty('mobile64')
    all_equal = riscv == desktop64 == mobile64
    assert all_equal


def test_compute_adjusted_uop_stats_returns_dict(simulation_soc_handler):
    """Verify compute_adjusted_uop_stats returns a dictionary."""
    result = simulation_soc_handler.compute_adjusted_uop_stats('desktop64', 1000)
    is_dict = isinstance(result, dict)
    assert is_dict


def test_compute_adjusted_uop_stats_has_total_uops(simulation_soc_handler):
    """Verify adjusted uop stats contains total_uops field."""
    result = simulation_soc_handler.compute_adjusted_uop_stats('desktop64', 1000)
    has_total = 'total_uops' in result
    assert has_total


def test_compute_adjusted_uop_stats_desktop64_higher_than_base(simulation_soc_handler):
    """Verify Desktop64 adjusted uops are higher than base due to overhead."""
    base = simulation_soc_handler.compute_uop_counts('desktop64', 1000)
    adjusted = simulation_soc_handler.compute_adjusted_uop_stats('desktop64', 1000)
    adjusted_higher = adjusted['total_uops'] > base['total_uops']
    assert adjusted_higher


def test_compute_trimode_effective_ipc_less_than_raw(simulation_soc_handler):
    """Verify effective IPC is reduced when fence cycles are present."""
    raw_ipc = 2.0
    fence_cycles = 1000
    instr_count = 10000
    result = simulation_soc_handler.compute_trimode_effective_ipc(
        raw_ipc, fence_cycles, instr_count)
    is_less = result < raw_ipc
    assert is_less


def test_compute_trimode_effective_ipc_equals_raw_when_no_fence(simulation_soc_handler):
    """Verify effective IPC equals raw IPC when no fence stalls occur."""
    raw_ipc = 2.0
    fence_cycles = 0
    instr_count = 10000
    result = simulation_soc_handler.compute_trimode_effective_ipc(
        raw_ipc, fence_cycles, instr_count)
    equals_raw = abs(result - raw_ipc) < 0.0001
    assert equals_raw


# =============================================================================
# Authentication Tests
# =============================================================================


def test_is_test_mode_returns_true_when_header_set(simulation_soc_handler):
    """Verify is_test_mode returns True when x-test-mode header is 'true'."""
    event = {'headers': {'x-test-mode': 'true'}}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is True


def test_is_test_mode_returns_true_for_uppercase_header(simulation_soc_handler):
    """Verify is_test_mode handles uppercase X-Test-Mode header."""
    event = {'headers': {'X-Test-Mode': 'true'}}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is True


def test_is_test_mode_returns_false_when_header_missing(simulation_soc_handler):
    """Verify is_test_mode returns False when header is missing."""
    event = {'headers': {'Content-Type': 'application/json'}}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is False


def test_is_test_mode_returns_false_when_headers_none(simulation_soc_handler):
    """Verify is_test_mode returns False when headers is None."""
    event = {'headers': None}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is False


def test_is_test_mode_returns_false_when_headers_empty(simulation_soc_handler):
    """Verify is_test_mode returns False when headers dict is empty."""
    event = {'headers': {}}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is False


def test_is_test_mode_returns_false_when_value_not_true(simulation_soc_handler):
    """Verify is_test_mode returns False when header value is not 'true'."""
    event = {'headers': {'x-test-mode': 'false'}}
    result = simulation_soc_handler.is_test_mode(event)
    assert result is False


def test_get_auth_token_returns_none_when_no_headers(simulation_soc_handler):
    """Verify get_auth_token returns None when headers is None."""
    event = {'headers': None}
    result = simulation_soc_handler.get_auth_token(event)
    assert result is None


def test_get_auth_token_returns_none_when_headers_empty(simulation_soc_handler):
    """Verify get_auth_token returns None when headers dict is empty."""
    event = {'headers': {}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result is None


def test_get_auth_token_returns_none_when_auth_header_missing(simulation_soc_handler):
    """Verify get_auth_token returns None when Authorization header is missing."""
    event = {'headers': {'Content-Type': 'application/json'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result is None


def test_get_auth_token_extracts_bearer_token(simulation_soc_handler):
    """Verify get_auth_token extracts token from Bearer prefix."""
    event = {'headers': {'Authorization': 'Bearer test-token-123'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result == 'test-token-123'


def test_get_auth_token_handles_lowercase_authorization(simulation_soc_handler):
    """Verify get_auth_token handles lowercase authorization header."""
    event = {'headers': {'authorization': 'Bearer lowercase-token'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result == 'lowercase-token'


def test_get_auth_token_returns_raw_token_without_bearer_prefix(simulation_soc_handler):
    """Verify get_auth_token returns raw token when no Bearer prefix."""
    event = {'headers': {'Authorization': 'raw-token-value'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result == 'raw-token-value'


# =============================================================================
# Google Token Verification Tests
# =============================================================================


def test_verify_google_token_returns_none_when_client_id_not_set(simulation_soc_handler):
    """Verify verify_google_token returns None when GOOGLE_CLIENT_ID is empty."""
    original_client_id = simulation_soc_handler.GOOGLE_CLIENT_ID
    try:
        simulation_soc_handler.GOOGLE_CLIENT_ID = ''
        result = simulation_soc_handler.verify_google_token('some-token')
        assert result is None
    finally:
        simulation_soc_handler.GOOGLE_CLIENT_ID = original_client_id


# =============================================================================
# Handler Edge Case Tests
# =============================================================================


def test_handler_returns_400_for_empty_body(simulation_soc_handler, lambda_context):
    """Verify handler returns 400 for empty string body."""
    event = {
        'path': '/v1/soc-simulations',
        'httpMethod': 'POST',
        'body': '',
        'headers': {'Content-Type': 'application/json', 'x-test-mode': 'true'},
        'requestContext': {'requestId': 'test-request-id'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handler_returns_400_for_null_body(simulation_soc_handler, lambda_context):
    """Verify handler returns 400 for null body."""
    event = {
        'path': '/v1/soc-simulations',
        'httpMethod': 'POST',
        'body': None,
        'headers': {'Content-Type': 'application/json', 'x-test-mode': 'true'},
        'requestContext': {'requestId': 'test-request-id'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_response_native_core_has_cache_stats(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains cache_stats field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_cache_stats = 'cache_stats' in body['native_core']
    assert has_cache_stats


def test_response_native_core_cache_stats_has_l1_miss_rate(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify cache_stats contains l1_miss_rate field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l1_miss = 'l1_miss_rate' in body['native_core']['cache_stats']
    assert has_l1_miss


def test_response_native_core_cache_stats_has_l2_miss_rate(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify cache_stats contains l2_miss_rate field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l2_miss = 'l2_miss_rate' in body['native_core']['cache_stats']
    assert has_l2_miss


def test_response_native_core_has_memory_stall_cpi(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains memory_stall_cpi field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_memory_stall = 'memory_stall_cpi' in body['native_core']
    assert has_memory_stall


def test_response_native_core_has_branch_stall_cpi(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains branch_stall_cpi field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_branch_stall = 'branch_stall_cpi' in body['native_core']
    assert has_branch_stall


def test_response_native_core_has_description(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify native_core contains description field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_description = 'description' in body['native_core']
    assert has_description


def test_response_tri_mode_core_has_description(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify tri_mode_core contains description field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_description = 'description' in body['tri_mode_core']
    assert has_description


def test_response_soc_config_has_ddr_field(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains ddr field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ddr = 'ddr' in body['soc_config']
    assert has_ddr


def test_response_soc_config_has_process_nm_field(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify soc_config contains process_nm field."""
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_process = 'process_nm' in body['soc_config']
    assert has_process


# =============================================================================
# Workload Configuration Tests
# =============================================================================


def test_workload_fractions_sum_to_one_for_riscv(simulation_soc_handler):
    """Verify RISC-V workload fractions sum to 1.0."""
    workload = simulation_soc_handler.WORKLOADS['riscv']
    total = (
        workload['alu_fraction'] +
        workload['load_fraction'] +
        workload['store_fraction'] +
        workload['branch_fraction'] +
        workload['fp_vec_fraction'] +
        workload['complex_fraction']
    )
    sums_to_one = abs(total - 1.0) < 0.0001
    assert sums_to_one


def test_workload_fractions_sum_to_one_for_desktop64(simulation_soc_handler):
    """Verify Desktop64 workload fractions sum to 1.0."""
    workload = simulation_soc_handler.WORKLOADS['desktop64']
    total = (
        workload['alu_fraction'] +
        workload['load_fraction'] +
        workload['store_fraction'] +
        workload['branch_fraction'] +
        workload['fp_vec_fraction'] +
        workload['complex_fraction']
    )
    sums_to_one = abs(total - 1.0) < 0.0001
    assert sums_to_one


def test_workload_fractions_sum_to_one_for_mobile64(simulation_soc_handler):
    """Verify Mobile64 workload fractions sum to 1.0."""
    workload = simulation_soc_handler.WORKLOADS['mobile64']
    total = (
        workload['alu_fraction'] +
        workload['load_fraction'] +
        workload['store_fraction'] +
        workload['branch_fraction'] +
        workload['fp_vec_fraction'] +
        workload['complex_fraction']
    )
    sums_to_one = abs(total - 1.0) < 0.0001
    assert sums_to_one


def test_valid_personas_matches_workloads_keys(simulation_soc_handler):
    """Verify VALID_PERSONAS matches WORKLOADS keys."""
    valid_personas = simulation_soc_handler.VALID_PERSONAS
    workload_keys = set(simulation_soc_handler.WORKLOADS.keys())
    personas_match = valid_personas == workload_keys
    assert personas_match


def test_all_personas_have_translation_uops(simulation_soc_handler):
    """Verify all personas have corresponding TRANSLATION_UOPS entries."""
    valid_personas = simulation_soc_handler.VALID_PERSONAS
    translation_keys = set(simulation_soc_handler.TRANSLATION_UOPS.keys())
    all_have_translations = valid_personas == translation_keys
    assert all_have_translations


def test_all_personas_have_trimode_overhead_params(simulation_soc_handler):
    """Verify all personas have corresponding TRIMODE_OVERHEAD_PARAMS entries."""
    valid_personas = simulation_soc_handler.VALID_PERSONAS
    overhead_keys = set(simulation_soc_handler.TRIMODE_OVERHEAD_PARAMS.keys())
    all_have_params = valid_personas == overhead_keys
    assert all_have_params


# =============================================================================
# OPTIONS Request Tests
# =============================================================================


def test_options_response_has_cors_allow_methods(simulation_soc_handler, lambda_context):
    """Verify OPTIONS response has Access-Control-Allow-Methods header."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    has_allow_methods = 'Access-Control-Allow-Methods' in response['headers']
    assert has_allow_methods


def test_options_response_has_cors_allow_headers(simulation_soc_handler, lambda_context):
    """Verify OPTIONS response has Access-Control-Allow-Headers header."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    has_allow_headers = 'Access-Control-Allow-Headers' in response['headers']
    assert has_allow_headers


def test_options_response_has_cors_allow_origin(simulation_soc_handler, lambda_context):
    """Verify OPTIONS response has Access-Control-Allow-Origin header."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    has_allow_origin = 'Access-Control-Allow-Origin' in response['headers']
    assert has_allow_origin


def test_options_response_body_is_empty(simulation_soc_handler, lambda_context):
    """Verify OPTIONS response body is empty string."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    body_is_empty = response['body'] == ''
    assert body_is_empty


def test_options_allow_methods_includes_post(simulation_soc_handler, lambda_context):
    """Verify OPTIONS Allow-Methods includes POST."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    includes_post = 'POST' in response['headers']['Access-Control-Allow-Methods']
    assert includes_post


def test_options_allow_headers_includes_authorization(simulation_soc_handler, lambda_context):
    """Verify OPTIONS Allow-Headers includes Authorization."""
    event = {'path': '/v1/soc-simulations', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    includes_auth = 'Authorization' in response['headers']['Access-Control-Allow-Headers']
    assert includes_auth


# =============================================================================
# Route Map Tests
# =============================================================================


def test_route_map_contains_soc_simulations_post(simulation_soc_handler):
    """Verify ROUTE_MAP contains /v1/soc-simulations POST route."""
    route = ('/v1/soc-simulations', 'POST')
    route_exists = route in simulation_soc_handler.ROUTE_MAP
    assert route_exists


def test_handler_returns_404_for_get_method(simulation_soc_handler, lambda_context):
    """Verify handler returns 404 for GET method on soc-simulations."""
    event = {
        'path': '/v1/soc-simulations',
        'httpMethod': 'GET',
        'headers': {'x-test-mode': 'true'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 404


def test_handler_returns_404_for_delete_method(simulation_soc_handler, lambda_context):
    """Verify handler returns 404 for DELETE method on soc-simulations."""
    event = {
        'path': '/v1/soc-simulations',
        'httpMethod': 'DELETE',
        'headers': {'x-test-mode': 'true'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 404


# =============================================================================
# Constants Validation Tests
# =============================================================================


def test_instruction_count_is_one_billion(simulation_soc_handler):
    """Verify INSTRUCTION_COUNT is set to 1 billion."""
    expected = 1_000_000_000
    is_one_billion = simulation_soc_handler.INSTRUCTION_COUNT == expected
    assert is_one_billion


def test_soc_config_clock_ghz_is_positive(simulation_soc_handler):
    """Verify SOC_CONFIG clock_ghz is positive."""
    clock = simulation_soc_handler.SOC_CONFIG['clock_ghz']
    is_positive = clock > 0
    assert is_positive


def test_soc_config_issue_width_is_positive(simulation_soc_handler):
    """Verify SOC_CONFIG issue_width is positive."""
    width = simulation_soc_handler.SOC_CONFIG['issue_width']
    is_positive = width > 0
    assert is_positive


def test_latencies_all_positive(simulation_soc_handler):
    """Verify all LATENCIES values are positive."""
    all_positive = all(v > 0 for v in simulation_soc_handler.LATENCIES.values())
    assert all_positive


def test_execution_units_all_positive(simulation_soc_handler):
    """Verify all EXECUTION_UNITS values are positive."""
    all_positive = all(v > 0 for v in simulation_soc_handler.EXECUTION_UNITS.values())
    assert all_positive
