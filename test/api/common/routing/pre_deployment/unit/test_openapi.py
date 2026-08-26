from pathlib import Path


def _get_openapi_path() -> Path:
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "www" / "api" / "openapi.json"


def test_openapi_spec_file_exists():
    assert _get_openapi_path().exists()


def test_openapi_spec_is_valid_json(openapi_spec):
    assert openapi_spec is not None


def test_openapi_spec_has_openapi_field(openapi_spec):
    assert 'openapi' in openapi_spec


def test_openapi_spec_version_starts_with_3_0(openapi_spec):
    assert openapi_spec['openapi'].startswith('3.0')


def test_openapi_spec_has_info_section(openapi_spec):
    assert 'info' in openapi_spec


def test_openapi_spec_info_has_title(openapi_spec):
    assert 'title' in openapi_spec['info']


def test_openapi_spec_info_has_version(openapi_spec):
    assert 'version' in openapi_spec['info']


def test_openapi_spec_has_paths_section(openapi_spec):
    assert 'paths' in openapi_spec


def test_openapi_spec_paths_not_empty(openapi_spec):
    assert len(openapi_spec['paths']) > 0


def test_openapi_spec_has_health_endpoint(openapi_spec):
    assert '/health' in openapi_spec['paths']


def test_openapi_spec_health_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/health']


def test_openapi_spec_has_diagnostics_echo_endpoint(openapi_spec):
    assert '/diagnostics/echo' in openapi_spec['paths']


def test_openapi_spec_diagnostics_echo_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/diagnostics/echo']


def test_openapi_spec_has_catchall_endpoint(openapi_spec):
    assert '/{proxy+}' in openapi_spec['paths']


def test_openapi_spec_health_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/health']


def test_openapi_spec_health_options_has_integration_key(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    assert 'x-amazon-apigateway-integration' in options


def test_openapi_spec_health_options_integration_type_is_mock(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    assert options['x-amazon-apigateway-integration']['type'] == 'mock'


def test_openapi_spec_health_options_integration_has_responses(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    assert 'responses' in integration


def test_openapi_spec_health_options_integration_has_default_response(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    assert 'default' in integration['responses']


def test_openapi_spec_health_options_returns_allow_origin_header(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Origin' in response_params


def test_openapi_spec_health_options_returns_allow_methods_header(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Methods' in response_params


def test_openapi_spec_health_options_returns_allow_headers_header(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Headers' in response_params


def test_openapi_spec_health_options_allows_wildcard_origin(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    origin_key = 'method.response.header.Access-Control-Allow-Origin'
    origin_value = response_params[origin_key]
    assert "'*'" in origin_value


def test_openapi_spec_has_contact_submissions_endpoint(openapi_spec):
    assert '/v1/contact-submissions' in openapi_spec['paths']


def test_openapi_spec_contact_submissions_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/contact-submissions']


def test_openapi_spec_contact_submissions_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/v1/contact-submissions']


def test_openapi_spec_has_rack_configurations_endpoint(openapi_spec):
    assert '/v1/rack-configurations' in openapi_spec['paths']


def test_openapi_spec_rack_configurations_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/rack-configurations']


def test_openapi_spec_rack_configurations_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/v1/rack-configurations']


def test_openapi_spec_has_rack_configuration_hash_endpoint(openapi_spec):
    assert '/v1/rack-configurations/{config_hash}' in openapi_spec['paths']


def test_openapi_spec_rack_configuration_hash_has_get_method(openapi_spec):
    path = '/v1/rack-configurations/{config_hash}'
    assert 'get' in openapi_spec['paths'][path]


def test_openapi_spec_rack_configuration_hash_has_options_method(openapi_spec):
    path = '/v1/rack-configurations/{config_hash}'
    assert 'options' in openapi_spec['paths'][path]


def test_openapi_spec_has_session_events_endpoint(openapi_spec):
    assert '/v1/sessions/{session_id}/events' in openapi_spec['paths']


def test_openapi_spec_session_events_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/sessions/{session_id}/events']


def test_openapi_spec_session_events_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/v1/sessions/{session_id}/events']


def test_openapi_spec_diagnostics_echo_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/diagnostics/echo']


def test_openapi_spec_has_request_validators(openapi_spec):
    assert 'x-amazon-apigateway-request-validators' in openapi_spec


def test_openapi_spec_has_validate_headers_validator(openapi_spec):
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert 'validate-headers' in validators


def test_openapi_spec_validate_headers_validates_parameters(openapi_spec):
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert validators['validate-headers']['validateRequestParameters'] is True


def test_openapi_spec_has_gateway_responses(openapi_spec):
    assert 'x-amazon-apigateway-gateway-responses' in openapi_spec


def test_openapi_spec_has_bad_request_parameters_response(openapi_spec):
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert 'BAD_REQUEST_PARAMETERS' in responses


def test_openapi_spec_bad_request_parameters_returns_400(openapi_spec):
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert responses['BAD_REQUEST_PARAMETERS']['statusCode'] == 400


def test_openapi_spec_response_templates_do_not_use_input_json_in_quotes():
    content = _get_openapi_path().read_text()
    assert '"$input.json(' not in content, (
        "Do not use $input.json() in quoted response templates - "
        "use $input.path() instead to avoid double-quoting"
    )
