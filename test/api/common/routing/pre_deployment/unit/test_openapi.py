from pathlib import Path
from typing import Any, Dict


def _get_openapi_path() -> Path:
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "www" / "api" / "openapi.json"


def test_openapi_spec_file_exists() -> None:
    assert _get_openapi_path().exists()


def test_openapi_spec_is_valid_json(openapi_spec: Dict[str, Any]) -> None:
    assert openapi_spec is not None


def test_openapi_spec_has_openapi_field(openapi_spec: Dict[str, Any]) -> None:
    assert 'openapi' in openapi_spec


def test_openapi_spec_version_starts_with_3_0(openapi_spec: Dict[str, Any]) -> None:
    assert openapi_spec['openapi'].startswith('3.0')


def test_openapi_spec_has_info_section(openapi_spec: Dict[str, Any]) -> None:
    assert 'info' in openapi_spec


def test_openapi_spec_info_has_title(openapi_spec: Dict[str, Any]) -> None:
    assert 'title' in openapi_spec['info']


def test_openapi_spec_info_has_version(openapi_spec: Dict[str, Any]) -> None:
    assert 'version' in openapi_spec['info']


def test_openapi_spec_has_paths_section(openapi_spec: Dict[str, Any]) -> None:
    assert 'paths' in openapi_spec


def test_openapi_spec_paths_not_empty(openapi_spec: Dict[str, Any]) -> None:
    assert len(openapi_spec['paths']) > 0


def test_openapi_spec_has_catchall_endpoint(openapi_spec: Dict[str, Any]) -> None:
    assert '/{proxy+}' in openapi_spec['paths']


def test_openapi_spec_has_contact_submissions_endpoint(openapi_spec: Dict[str, Any]) -> None:
    assert '/v1/contact-submissions' in openapi_spec['paths']


def test_openapi_spec_contact_submissions_has_post_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'post' in openapi_spec['paths']['/v1/contact-submissions']


def test_openapi_spec_contact_submissions_has_options_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'options' in openapi_spec['paths']['/v1/contact-submissions']


def test_openapi_spec_has_rack_configurations_endpoint(openapi_spec: Dict[str, Any]) -> None:
    assert '/v1/rack-configurations' in openapi_spec['paths']


def test_openapi_spec_rack_configurations_has_post_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'post' in openapi_spec['paths']['/v1/rack-configurations']


def test_openapi_spec_rack_configurations_has_options_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'options' in openapi_spec['paths']['/v1/rack-configurations']


def test_openapi_spec_has_rack_configuration_hash_endpoint(openapi_spec: Dict[str, Any]) -> None:
    assert '/v1/rack-configurations/{config_hash}' in openapi_spec['paths']


def test_openapi_spec_rack_configuration_hash_has_get_method(openapi_spec: Dict[str, Any]) -> None:
    path = '/v1/rack-configurations/{config_hash}'
    assert 'get' in openapi_spec['paths'][path]


def test_openapi_spec_rack_configuration_hash_has_options_method(
    openapi_spec: Dict[str, Any]
) -> None:
    path = '/v1/rack-configurations/{config_hash}'
    assert 'options' in openapi_spec['paths'][path]


def test_openapi_spec_has_session_events_endpoint(openapi_spec: Dict[str, Any]) -> None:
    assert '/v1/sessions/{session_id}/events' in openapi_spec['paths']


def test_openapi_spec_session_events_has_post_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'post' in openapi_spec['paths']['/v1/sessions/{session_id}/events']


def test_openapi_spec_session_events_has_options_method(openapi_spec: Dict[str, Any]) -> None:
    assert 'options' in openapi_spec['paths']['/v1/sessions/{session_id}/events']


def test_openapi_spec_has_request_validators(openapi_spec: Dict[str, Any]) -> None:
    assert 'x-amazon-apigateway-request-validators' in openapi_spec


def test_openapi_spec_has_validate_headers_validator(openapi_spec: Dict[str, Any]) -> None:
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert 'validate-headers' in validators


def test_openapi_spec_validate_headers_validates_parameters(openapi_spec: Dict[str, Any]) -> None:
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert validators['validate-headers']['validateRequestParameters'] is True


def test_openapi_spec_has_gateway_responses(openapi_spec: Dict[str, Any]) -> None:
    assert 'x-amazon-apigateway-gateway-responses' in openapi_spec


def test_openapi_spec_has_bad_request_parameters_response(openapi_spec: Dict[str, Any]) -> None:
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert 'BAD_REQUEST_PARAMETERS' in responses


def test_openapi_spec_bad_request_parameters_returns_400(openapi_spec: Dict[str, Any]) -> None:
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert responses['BAD_REQUEST_PARAMETERS']['statusCode'] == 400


def test_openapi_spec_response_templates_do_not_use_input_json_in_quotes() -> None:
    content = _get_openapi_path().read_text()
    assert '"$input.json(' not in content, (
        "Do not use $input.json() in quoted response templates - "
        "use $input.path() instead to avoid double-quoting"
    )
