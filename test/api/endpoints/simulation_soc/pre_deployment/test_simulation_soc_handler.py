import json
from typing import Any, Dict


def parse_response_body(response: Dict[str, Any]) -> Any:
    return json.loads(response['body'])


def assert_response_status(response: Dict[str, Any], expected_code: int) -> None:
    assert response['statusCode'] == expected_code


def assert_json_content_type(response: Dict[str, Any]) -> None:
    assert response['headers']['Content-Type'].startswith('application/json')


def assert_cors_headers(response: Dict[str, Any]) -> None:
    assert 'Access-Control-Allow-Origin' in response['headers']


def test_handler_returns_200_for_riscv_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_returns_200_for_x86_64_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'x86_64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_returns_200_for_arm64_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'arm64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_returns_json_content_type(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_json_content_type(response)


def test_handler_returns_cors_header(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_cors_headers(response)


def test_handler_returns_400_for_invalid_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handler_returns_400_for_missing_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={})
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handler_returns_400_for_invalid_json(simulation_soc_handler, lambda_context):
    event = {
        'path': '/v1/simulation-soc',
        'httpMethod': 'POST',
        'body': 'not valid json',
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-request-id'}
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handler_options_returns_200(simulation_soc_handler, lambda_context):
    event = {'path': '/v1/simulation-soc', 'httpMethod': 'OPTIONS'}
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handler_unknown_route_returns_404(simulation_soc_handler, lambda_context):
    event = {'path': '/v1/unknown', 'httpMethod': 'POST', 'body': '{}'}
    response = simulation_soc_handler.handler(event, lambda_context)
    assert_response_status(response, 404)


def test_response_contains_success_field(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_success = 'success' in body
    assert has_success


def test_response_success_is_true_for_valid_request(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    success_is_true = body['success'] is True
    assert success_is_true


def test_response_contains_persona_field(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'arm64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    persona_matches = body['persona'] == 'arm64'
    assert persona_matches


def test_response_contains_soc_config(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_soc_config = 'soc_config' in body
    assert has_soc_config


def test_response_soc_config_has_issue_width(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_issue_width = 'issue_width' in body['soc_config']
    assert has_issue_width


def test_response_soc_config_has_rob_entries(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_rob_entries = 'rob_entries' in body['soc_config']
    assert has_rob_entries


def test_response_soc_config_has_l1_size_kb(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l1_size = 'l1_size_kb' in body['soc_config']
    assert has_l1_size


def test_response_soc_config_has_l2_size_kb(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_l2_size = 'l2_size_kb' in body['soc_config']
    assert has_l2_size


def test_response_soc_config_has_clock_ghz(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_clock = 'clock_ghz' in body['soc_config']
    assert has_clock


def test_response_contains_instruction_count(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_instruction_count = 'instruction_count' in body
    assert has_instruction_count


def test_response_contains_native_core(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_native_core = 'native_core' in body
    assert has_native_core


def test_response_native_core_has_ipc(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ipc = 'ipc' in body['native_core']
    assert has_ipc


def test_response_native_core_has_runtime_seconds(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_runtime = 'runtime_seconds' in body['native_core']
    assert has_runtime


def test_response_contains_tri_mode_core(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_tri_mode_core = 'tri_mode_core' in body
    assert has_tri_mode_core


def test_response_tri_mode_core_has_ipc(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ipc = 'ipc' in body['tri_mode_core']
    assert has_ipc


def test_response_tri_mode_core_has_runtime_seconds(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_runtime = 'runtime_seconds' in body['tri_mode_core']
    assert has_runtime


def test_response_contains_relative_slowdown(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_slowdown = 'relative_slowdown' in body
    assert has_slowdown


def test_tri_mode_ipc_is_less_than_native_ipc_for_x86(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'x86_64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    tri_mode_slower = body['tri_mode_core']['ipc'] < body['native_core']['ipc']
    assert tri_mode_slower


def test_relative_slowdown_is_greater_than_one_for_x86(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'x86_64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown_greater_than_one = body['relative_slowdown'] > 1.0
    assert slowdown_greater_than_one


def test_tri_mode_ipc_is_less_than_native_ipc_for_arm64(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'arm64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    tri_mode_slower = body['tri_mode_core']['ipc'] < body['native_core']['ipc']
    assert tri_mode_slower


def test_relative_slowdown_is_greater_than_one_for_arm64(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'arm64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown_greater_than_one = body['relative_slowdown'] > 1.0
    assert slowdown_greater_than_one


def test_riscv_trimode_has_small_overhead(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    native_ipc = body['native_core']['ipc']
    trimode_ipc = body['tri_mode_core']['ipc']
    trimode_slightly_slower = trimode_ipc < native_ipc
    assert trimode_slightly_slower


def test_riscv_relative_slowdown_is_small(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown = body['relative_slowdown']
    slowdown_is_small = 1.0 < slowdown < 1.05
    assert slowdown_is_small


def test_error_response_contains_success_false(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    success_is_false = body['success'] is False
    assert success_is_false


def test_error_response_contains_error_field(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_error = 'error' in body
    assert has_error


def test_error_response_contains_details_for_invalid_persona(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'invalid'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_details = 'details' in body
    assert has_details


def test_native_core_ipc_is_positive(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    ipc_positive = body['native_core']['ipc'] > 0
    assert ipc_positive


def test_native_core_runtime_is_positive(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    runtime_positive = body['native_core']['runtime_seconds'] > 0
    assert runtime_positive


def test_tri_mode_core_ipc_is_positive(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    ipc_positive = body['tri_mode_core']['ipc'] > 0
    assert ipc_positive


def test_tri_mode_core_runtime_is_positive(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    runtime_positive = body['tri_mode_core']['runtime_seconds'] > 0
    assert runtime_positive


def test_response_contains_real_world_comparison(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_real_world = 'real_world_comparison' in body
    assert has_real_world


def test_real_world_comparison_has_native_core(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_native_core = 'native_core' in body['real_world_comparison']
    assert has_native_core


def test_real_world_comparison_native_core_has_name(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_name = 'name' in body['real_world_comparison']['native_core']
    assert has_name


def test_real_world_comparison_native_core_has_ipc(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_ipc = 'ipc' in body['real_world_comparison']['native_core']
    assert has_ipc


def test_real_world_comparison_has_tri_mode_core(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_tri_mode = 'tri_mode_core' in body['real_world_comparison']
    assert has_tri_mode


def test_real_world_comparison_has_relative_slowdown(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory()
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    has_slowdown = 'relative_slowdown' in body['real_world_comparison']
    assert has_slowdown


def test_real_world_x86_64_core_name_is_pentium4(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'x86_64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    is_pentium4 = 'Pentium' in body['real_world_comparison']['native_core']['name']
    assert is_pentium4


def test_real_world_arm64_core_name_is_cortex(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'arm64'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    is_cortex = 'Cortex' in body['real_world_comparison']['native_core']['name']
    assert is_cortex


def test_real_world_riscv_core_name_is_sifive(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    is_sifive = 'SiFive' in body['real_world_comparison']['native_core']['name']
    assert is_sifive


def test_derive_translation_uops_averages_ranges(simulation_soc_handler):
    ranges = {'alu': (1, 3), 'load': (2, 4)}
    result = simulation_soc_handler.derive_translation_uops(ranges)
    correct_average = result['alu'] == 2.0 and result['load'] == 3.0
    assert correct_average


def test_json_response_has_status_code(simulation_soc_handler):
    response = simulation_soc_handler.json_response(200, {'test': 'data'})
    has_status = response['statusCode'] == 200
    assert has_status


def test_json_response_has_json_body(simulation_soc_handler):
    response = simulation_soc_handler.json_response(200, {'test': 'data'})
    body = json.loads(response['body'])
    body_correct = body['test'] == 'data'
    assert body_correct


def test_json_response_has_cors_headers(simulation_soc_handler):
    response = simulation_soc_handler.json_response(200, {})
    has_cors = 'Access-Control-Allow-Origin' in response['headers']
    assert has_cors


def test_error_response_without_details(simulation_soc_handler):
    response = simulation_soc_handler.error_response(400, 'Test error')
    body = json.loads(response['body'])
    no_details = 'details' not in body
    assert no_details


def test_error_response_with_details(simulation_soc_handler):
    response = simulation_soc_handler.error_response(400, 'Test error', 'Test details')
    body = json.loads(response['body'])
    has_details = body['details'] == 'Test details'
    assert has_details


def test_parse_body_with_string(simulation_soc_handler):
    event = {'body': '{"key": "value"}'}
    result = simulation_soc_handler.parse_body(event)
    parsed_correctly = result['key'] == 'value'
    assert parsed_correctly


def test_parse_body_with_dict(simulation_soc_handler):
    event = {'body': {'key': 'value'}}
    result = simulation_soc_handler.parse_body(event)
    parsed_correctly = result['key'] == 'value'
    assert parsed_correctly


def test_build_soc_config_output_has_issue_width(simulation_soc_handler):
    config = simulation_soc_handler.build_soc_config_output()
    has_issue_width = 'issue_width' in config
    assert has_issue_width


def test_build_soc_config_output_has_clock_ghz(simulation_soc_handler):
    config = simulation_soc_handler.build_soc_config_output()
    has_clock = 'clock_ghz' in config
    assert has_clock


def test_build_real_world_config_riscv_has_name(simulation_soc_handler):
    config = simulation_soc_handler.build_real_world_config('riscv')
    has_name = 'name' in config
    assert has_name


def test_build_real_world_config_x86_has_clock(simulation_soc_handler):
    config = simulation_soc_handler.build_real_world_config('x86_64')
    has_clock = 'clock_ghz' in config
    assert has_clock


def test_compute_uop_counts_returns_total_uops(simulation_soc_handler):
    result = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    has_total = 'total_uops' in result
    assert has_total


def test_compute_uop_counts_total_is_positive(simulation_soc_handler):
    result = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    total_positive = result['total_uops'] > 0
    assert total_positive


def test_compute_frontend_ipc_returns_ipc(simulation_soc_handler):
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_frontend_ipc('riscv', uop_stats)
    has_ipc = 'ipc_frontend' in result
    assert has_ipc


def test_compute_frontend_ipc_trimode_lower_for_x86(simulation_soc_handler):
    uop_stats = simulation_soc_handler.compute_uop_counts('x86_64', 1000)
    adjusted_uop_stats = simulation_soc_handler.compute_adjusted_uop_stats('x86_64', 1000)
    native = simulation_soc_handler.compute_frontend_ipc('x86_64', uop_stats)
    trimode = simulation_soc_handler.compute_frontend_ipc('x86_64', adjusted_uop_stats)
    trimode_lower = trimode['ipc_frontend'] < native['ipc_frontend']
    assert trimode_lower


def test_compute_backend_ipc_returns_ipc(simulation_soc_handler):
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_backend_ipc('riscv', uop_stats, 1000)
    has_ipc = 'ipc_backend' in result
    assert has_ipc


def test_compute_backend_ipc_is_positive(simulation_soc_handler):
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_backend_ipc('riscv', uop_stats, 1000)
    ipc_positive = result['ipc_backend'] > 0
    assert ipc_positive


def test_compute_memory_stall_cpi_is_positive(simulation_soc_handler):
    workload = simulation_soc_handler.WORKLOADS['riscv']
    result = simulation_soc_handler.compute_memory_stall_cpi(workload, 1000, 1000)
    cpi_positive = result > 0
    assert cpi_positive


def test_compute_native_simulation_returns_ipc(simulation_soc_handler):
    result = simulation_soc_handler.compute_native_simulation('riscv')
    has_ipc = 'ipc' in result
    assert has_ipc


def test_compute_native_simulation_returns_runtime(simulation_soc_handler):
    result = simulation_soc_handler.compute_native_simulation('riscv')
    has_runtime = 'runtime_seconds' in result
    assert has_runtime


def test_compute_trimode_simulation_returns_ipc(simulation_soc_handler):
    result = simulation_soc_handler.compute_trimode_simulation('riscv')
    has_ipc = 'ipc' in result
    assert has_ipc


def test_compute_trimode_simulation_ipc_less_than_native_for_x86(simulation_soc_handler):
    native = simulation_soc_handler.compute_native_simulation('x86_64')
    trimode = simulation_soc_handler.compute_trimode_simulation('x86_64')
    trimode_lower = trimode['ipc'] < native['ipc']
    assert trimode_lower


def test_compute_real_world_simulation_returns_core_name(simulation_soc_handler):
    result = simulation_soc_handler.compute_real_world_simulation('riscv')
    has_name = 'core_name' in result
    assert has_name


def test_compute_real_world_simulation_returns_ipc(simulation_soc_handler):
    result = simulation_soc_handler.compute_real_world_simulation('x86_64')
    has_ipc = 'ipc' in result
    assert has_ipc


def test_compute_resource_limited_upc_is_positive(simulation_soc_handler):
    uop_stats = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    result = simulation_soc_handler.compute_resource_limited_upc(uop_stats)
    upc_positive = result > 0
    assert upc_positive


def test_x86_has_more_uops_than_riscv(simulation_soc_handler):
    riscv_uops = simulation_soc_handler.compute_uop_counts('riscv', 1000)
    x86_uops = simulation_soc_handler.compute_uop_counts('x86_64', 1000)
    x86_more = x86_uops['total_uops'] > riscv_uops['total_uops']
    assert x86_more


def test_riscv_native_ipc_higher_than_x86(simulation_soc_handler):
    riscv = simulation_soc_handler.compute_native_simulation('riscv')
    x86 = simulation_soc_handler.compute_native_simulation('x86_64')
    riscv_higher = riscv['ipc'] > x86['ipc']
    assert riscv_higher


def test_compute_flags_overhead_uops_zero_for_riscv(simulation_soc_handler):
    result = simulation_soc_handler.compute_flags_overhead_uops('riscv', 1000)
    is_zero = result == 0.0
    assert is_zero


def test_compute_flags_overhead_uops_positive_for_x86(simulation_soc_handler):
    result = simulation_soc_handler.compute_flags_overhead_uops('x86_64', 1000)
    is_positive = result > 0
    assert is_positive


def test_compute_fence_stall_cycles_zero_for_riscv(simulation_soc_handler):
    result = simulation_soc_handler.compute_fence_stall_cycles('riscv', 1000)
    is_zero = result == 0.0
    assert is_zero


def test_compute_fence_stall_cycles_positive_for_x86(simulation_soc_handler):
    result = simulation_soc_handler.compute_fence_stall_cycles('x86_64', 1000)
    is_positive = result > 0
    assert is_positive


def test_compute_trimode_mispredict_penalty_riscv_greater_than_base(simulation_soc_handler):
    result = simulation_soc_handler.compute_trimode_mispredict_penalty('riscv')
    base_penalty = simulation_soc_handler.LATENCIES['branch_mispredict']
    is_greater = result > base_penalty
    assert is_greater


def test_compute_trimode_mispredict_penalty_x86_greater_than_riscv(simulation_soc_handler):
    riscv_penalty = simulation_soc_handler.compute_trimode_mispredict_penalty('riscv')
    x86_penalty = simulation_soc_handler.compute_trimode_mispredict_penalty('x86_64')
    x86_higher = x86_penalty > riscv_penalty
    assert x86_higher


def test_compute_adjusted_uop_stats_returns_dict(simulation_soc_handler):
    result = simulation_soc_handler.compute_adjusted_uop_stats('x86_64', 1000)
    is_dict = isinstance(result, dict)
    assert is_dict


def test_compute_adjusted_uop_stats_has_total_uops(simulation_soc_handler):
    result = simulation_soc_handler.compute_adjusted_uop_stats('x86_64', 1000)
    has_total = 'total_uops' in result
    assert has_total


def test_compute_adjusted_uop_stats_x86_higher_than_base(simulation_soc_handler):
    base = simulation_soc_handler.compute_uop_counts('x86_64', 1000)
    adjusted = simulation_soc_handler.compute_adjusted_uop_stats('x86_64', 1000)
    adjusted_higher = adjusted['total_uops'] > base['total_uops']
    assert adjusted_higher


def test_compute_trimode_effective_ipc_less_than_raw(simulation_soc_handler):
    raw_ipc = 2.0
    fence_cycles = 1000
    instr_count = 10000
    result = simulation_soc_handler.compute_trimode_effective_ipc(raw_ipc, fence_cycles, instr_count)
    is_less = result < raw_ipc
    assert is_less


def test_compute_trimode_effective_ipc_equals_raw_when_no_fence(simulation_soc_handler):
    raw_ipc = 2.0
    fence_cycles = 0
    instr_count = 10000
    result = simulation_soc_handler.compute_trimode_effective_ipc(raw_ipc, fence_cycles, instr_count)
    equals_raw = abs(result - raw_ipc) < 0.0001
    assert equals_raw
