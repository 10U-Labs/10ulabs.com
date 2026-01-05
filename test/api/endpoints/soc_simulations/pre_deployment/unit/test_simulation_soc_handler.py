"""Unit tests for the simulation-soc Lambda handler."""
import json
import urllib.error
from typing import Any, Dict
from unittest.mock import MagicMock, patch


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


def test_compute_fence_stall_cycles_with_fence_per_store(simulation_soc_handler):
    """Verify fence stall cycles computed when fence_per_store is True."""
    mock_params = {
        'test_persona': {
            'flags_live_rate': 0.0,
            'flags_uops_per_live': 0,
            'fence_per_store': True,
            'extra_decode_stages': 0
        }
    }
    with patch.object(simulation_soc_handler, 'TRIMODE_OVERHEAD_PARAMS', mock_params):
        result = simulation_soc_handler.compute_fence_stall_cycles('test_persona', 100.0)
        expected = (100.0 / 32) * 6  # store_count / STORE_BUFFER_ENTRIES * FENCE_LATENCY
        assert result == expected


def test_verify_google_token_returns_none_without_client_id(simulation_soc_handler):
    """Verify verify_google_token returns None when GOOGLE_CLIENT_ID is not set."""
    with patch.object(simulation_soc_handler, 'GOOGLE_CLIENT_ID', None):
        result = simulation_soc_handler.verify_google_token('fake_token')
        assert result is None


def _create_mock_urlopen_response(data: dict) -> MagicMock:
    """Create a mock response for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(data).encode('utf-8')
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def test_verify_google_token_returns_data_on_success(simulation_soc_handler):
    """Verify verify_google_token returns user data on successful verification."""
    mock_data = {'aud': 'test_client_id', 'email': 'test@example.com'}
    mock_response = _create_mock_urlopen_response(mock_data)
    with patch.object(simulation_soc_handler, 'GOOGLE_CLIENT_ID', 'test_client_id'):
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = simulation_soc_handler.verify_google_token('valid_token')
            assert result == mock_data


def test_verify_google_token_returns_none_on_aud_mismatch(simulation_soc_handler):
    """Verify verify_google_token returns None when audience doesn't match."""
    mock_data = {'aud': 'wrong_client_id', 'email': 'test@example.com'}
    mock_response = _create_mock_urlopen_response(mock_data)
    with patch.object(simulation_soc_handler, 'GOOGLE_CLIENT_ID', 'test_client_id'):
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = simulation_soc_handler.verify_google_token('valid_token')
            assert result is None


def test_verify_google_token_returns_none_on_url_error(simulation_soc_handler):
    """Verify verify_google_token returns None on URL error."""
    with patch.object(simulation_soc_handler, 'GOOGLE_CLIENT_ID', 'test_client_id'):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('error')):
            result = simulation_soc_handler.verify_google_token('bad_token')
            assert result is None


def test_handler_returns_401_when_not_in_test_mode_without_token(
        simulation_soc_handler, lambda_context):
    """Verify handler returns 401 when not in test mode and no auth token."""
    event = {
        'httpMethod': 'POST',
        'path': '/v1/soc-simulations',
        'headers': {},  # No X-Test-Mode header
        'body': '{"persona": "riscv"}'
    }
    response = simulation_soc_handler.handler(event, lambda_context)
    assert response['statusCode'] == 401


def test_handler_returns_401_when_token_invalid(
        simulation_soc_handler, lambda_context):
    """Verify handler returns 401 when token verification fails."""
    event = {
        'httpMethod': 'POST',
        'path': '/v1/soc-simulations',
        'headers': {'Authorization': 'Bearer invalid_token'},
        'body': '{"persona": "riscv"}'
    }
    with patch.object(simulation_soc_handler, 'verify_google_token', return_value=None):
        response = simulation_soc_handler.handler(event, lambda_context)
        assert response['statusCode'] == 401


def test_handler_returns_500_on_value_error(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 500 on ValueError during simulation."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    with patch.object(
        simulation_soc_handler, 'compute_simulation', side_effect=ValueError('test error')
    ):
        response = simulation_soc_handler.handler(event, lambda_context)
        assert response['statusCode'] == 500


def test_handler_returns_500_on_key_error(
        simulation_soc_handler, simulation_soc_post_event_factory, lambda_context):
    """Verify handler returns 500 on KeyError during simulation."""
    event = simulation_soc_post_event_factory(body_data={'persona': 'riscv'})
    with patch.object(
        simulation_soc_handler, 'compute_simulation', side_effect=KeyError('missing_key')
    ):
        response = simulation_soc_handler.handler(event, lambda_context)
        assert response['statusCode'] == 500


def test_get_auth_token_returns_none_when_no_auth_header(simulation_soc_handler):
    """Verify get_auth_token returns None when no Authorization header."""
    event = {'headers': {'Content-Type': 'application/json'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result is None


def test_get_auth_token_returns_raw_token_without_bearer_prefix(simulation_soc_handler):
    """Verify get_auth_token returns raw token when not prefixed with Bearer."""
    event = {'headers': {'Authorization': 'raw_token_value'}}
    result = simulation_soc_handler.get_auth_token(event)
    assert result == 'raw_token_value'
