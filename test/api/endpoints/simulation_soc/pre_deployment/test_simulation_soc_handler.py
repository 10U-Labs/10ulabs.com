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


def test_riscv_native_equals_trimode_ipc(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    native_ipc = body['native_core']['ipc']
    trimode_ipc = body['tri_mode_core']['ipc']
    ipc_equal = abs(native_ipc - trimode_ipc) < 0.001
    assert ipc_equal


def test_riscv_relative_slowdown_equals_one(simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    response = simulation_soc_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    slowdown = body['relative_slowdown']
    slowdown_is_one = abs(slowdown - 1.0) < 0.001
    assert slowdown_is_one


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
