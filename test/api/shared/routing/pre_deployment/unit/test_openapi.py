"""Tests for OpenAPI specification validation."""
from pathlib import Path


def _get_openapi_path() -> Path:
    """Get the path to openapi.json file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "www" / "api" / "openapi.json"


def test_openapi_spec_file_exists():
    """Verify openapi.json file exists."""
    assert _get_openapi_path().exists()


def test_openapi_spec_is_valid_json(openapi_spec):
    """Verify spec is valid JSON."""
    assert openapi_spec is not None


def test_openapi_spec_has_openapi_field(openapi_spec):
    """Verify spec has openapi field."""
    assert 'openapi' in openapi_spec


def test_openapi_spec_version_starts_with_3_0(openapi_spec):
    """Verify OpenAPI version starts with 3.0."""
    assert openapi_spec['openapi'].startswith('3.0')


def test_openapi_spec_has_info_section(openapi_spec):
    """Verify spec has info section."""
    assert 'info' in openapi_spec


def test_openapi_spec_info_has_title(openapi_spec):
    """Verify info section has title."""
    assert 'title' in openapi_spec['info']


def test_openapi_spec_info_has_version(openapi_spec):
    """Verify info section has version."""
    assert 'version' in openapi_spec['info']


def test_openapi_spec_has_paths_section(openapi_spec):
    """Verify spec has paths section."""
    assert 'paths' in openapi_spec


def test_openapi_spec_paths_not_empty(openapi_spec):
    """Verify paths section is not empty."""
    assert len(openapi_spec['paths']) > 0


def test_openapi_spec_has_health_endpoint(openapi_spec):
    """Verify spec has /health endpoint."""
    assert '/health' in openapi_spec['paths']


def test_openapi_spec_health_has_get_method(openapi_spec):
    """Verify /health has GET method."""
    assert 'get' in openapi_spec['paths']['/health']


def test_openapi_spec_has_diagnostics_echo_endpoint(openapi_spec):
    """Verify spec has /diagnostics/echo endpoint."""
    assert '/diagnostics/echo' in openapi_spec['paths']


def test_openapi_spec_diagnostics_echo_has_post_method(openapi_spec):
    """Verify /diagnostics/echo has POST method."""
    assert 'post' in openapi_spec['paths']['/diagnostics/echo']


def test_openapi_spec_has_jit_runner_requests_post_endpoint(openapi_spec):
    """Verify spec has /v1/webhooks/github/jit-runner-requests endpoint."""
    assert '/v1/webhooks/github/jit-runner-requests' in openapi_spec['paths']


def test_openapi_spec_jit_runner_requests_has_post_method(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']


def test_openapi_spec_has_jit_runner_requests_health_endpoint(openapi_spec):
    """Verify spec has /v1/webhooks/github/jit-runner-requests/health endpoint."""
    assert '/v1/webhooks/github/jit-runner-requests/health' in openapi_spec['paths']


def test_openapi_spec_jit_runner_requests_health_has_get_method(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests/health has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests/health']


def test_openapi_spec_has_ec2_ami_base_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ec2/images endpoint."""
    assert '/v1/runners/ec2/images' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_latest_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ec2/images/latest endpoint."""
    assert '/v1/runners/ec2/images/latest' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_delete_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ec2/images/{ami_id} endpoint."""
    assert '/v1/runners/ec2/images/{ami_id}' in openapi_spec['paths']


def test_openapi_spec_has_ecs_runner_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ecs endpoint."""
    assert '/v1/runners/ecs' in openapi_spec['paths']


def test_openapi_spec_ecs_runner_has_post_method(openapi_spec):
    """Verify /v1/runners/ecs has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/runners/ecs']


def test_openapi_spec_ecs_runner_has_get_method(openapi_spec):
    """Verify /v1/runners/ecs has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/ecs']


def test_openapi_spec_does_not_have_ecs_runner_latest(openapi_spec):
    """Verify spec does not have /v1/runners/ecs/latest endpoint."""
    assert '/v1/runners/ecs/latest' not in openapi_spec['paths']


def test_openapi_spec_has_ec2_runner_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ec2 endpoint."""
    assert '/v1/runners/ec2' in openapi_spec['paths']


def test_openapi_spec_ec2_runner_has_post_method(openapi_spec):
    """Verify /v1/runners/ec2 has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/runners/ec2']


def test_openapi_spec_has_catchall_endpoint(openapi_spec):
    """Verify spec has /{proxy+} catchall endpoint."""
    assert '/{proxy+}' in openapi_spec['paths']


def test_openapi_spec_health_has_options_method(openapi_spec):
    """Verify /health has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/health']


def test_openapi_spec_health_options_has_integration_key(openapi_spec):
    """Verify /health OPTIONS has API Gateway integration key."""
    options = openapi_spec['paths']['/health']['options']
    assert 'x-amazon-apigateway-integration' in options


def test_openapi_spec_health_options_integration_type_is_mock(openapi_spec):
    """Verify /health OPTIONS integration type is mock."""
    options = openapi_spec['paths']['/health']['options']
    assert options['x-amazon-apigateway-integration']['type'] == 'mock'


def test_openapi_spec_health_options_integration_has_responses(openapi_spec):
    """Verify /health OPTIONS integration has responses."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    assert 'responses' in integration


def test_openapi_spec_health_options_integration_has_default_response(openapi_spec):
    """Verify /health OPTIONS integration has default response."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    assert 'default' in integration['responses']


def test_openapi_spec_health_options_returns_allow_origin_header(openapi_spec):
    """Verify /health OPTIONS returns Access-Control-Allow-Origin header."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Origin' in response_params


def test_openapi_spec_health_options_returns_allow_methods_header(openapi_spec):
    """Verify /health OPTIONS returns Access-Control-Allow-Methods header."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Methods' in response_params


def test_openapi_spec_health_options_returns_allow_headers_header(openapi_spec):
    """Verify /health OPTIONS returns Access-Control-Allow-Headers header."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    assert 'method.response.header.Access-Control-Allow-Headers' in response_params


def test_openapi_spec_health_options_allows_wildcard_origin(openapi_spec):
    """Verify /health OPTIONS allows wildcard origin."""
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    origin_key = 'method.response.header.Access-Control-Allow-Origin'
    origin_value = response_params[origin_key]
    assert "'*'" in origin_value


def test_openapi_spec_has_simulation_soc_endpoint(openapi_spec):
    """Verify spec has /v1/simulation-soc endpoint."""
    assert '/v1/simulation-soc' in openapi_spec['paths']


def test_openapi_spec_simulation_soc_has_post_method(openapi_spec):
    """Verify /v1/simulation-soc has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/simulation-soc']


def test_openapi_spec_simulation_soc_has_options_method(openapi_spec):
    """Verify /v1/simulation-soc has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/simulation-soc']


def test_openapi_spec_has_ecs_image_base_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ecs/images endpoint."""
    assert '/v1/runners/ecs/images' in openapi_spec['paths']


def test_openapi_spec_ecs_image_has_get_method(openapi_spec):
    """Verify /v1/runners/ecs/images has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/ecs/images']


def test_openapi_spec_ecs_image_has_post_method(openapi_spec):
    """Verify /v1/runners/ecs/images has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/runners/ecs/images']


def test_openapi_spec_ecs_image_has_options_method(openapi_spec):
    """Verify /v1/runners/ecs/images has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ecs/images']


def test_openapi_spec_has_ecs_image_latest_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ecs/images/latest endpoint."""
    assert '/v1/runners/ecs/images/latest' in openapi_spec['paths']


def test_openapi_spec_ecs_image_latest_has_get_method(openapi_spec):
    """Verify /v1/runners/ecs/images/latest has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/ecs/images/latest']


def test_openapi_spec_ecs_image_latest_has_options_method(openapi_spec):
    """Verify /v1/runners/ecs/images/latest has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ecs/images/latest']


def test_openapi_spec_has_ecs_image_digest_endpoint(openapi_spec):
    """Verify spec has /v1/runners/ecs/images/{digest} endpoint."""
    assert '/v1/runners/ecs/images/{digest}' in openapi_spec['paths']


def test_openapi_spec_ecs_image_digest_has_get_method(openapi_spec):
    """Verify /v1/runners/ecs/images/{digest} has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/ecs/images/{digest}']


def test_openapi_spec_ecs_image_digest_has_delete_method(openapi_spec):
    """Verify /v1/runners/ecs/images/{digest} has DELETE method."""
    assert 'delete' in openapi_spec['paths']['/v1/runners/ecs/images/{digest}']


def test_openapi_spec_ecs_image_digest_has_options_method(openapi_spec):
    """Verify /v1/runners/ecs/images/{digest} has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ecs/images/{digest}']


def test_openapi_spec_ec2_runner_has_get_method(openapi_spec):
    """Verify /v1/runners/ec2 has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/ec2']


def test_openapi_spec_ec2_runner_has_options_method(openapi_spec):
    """Verify /v1/runners/ec2 has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ec2']


def test_openapi_spec_has_contact_endpoint(openapi_spec):
    """Verify spec has /v1/contact endpoint."""
    assert '/v1/contact' in openapi_spec['paths']


def test_openapi_spec_contact_has_post_method(openapi_spec):
    """Verify /v1/contact has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/contact']


def test_openapi_spec_contact_has_options_method(openapi_spec):
    """Verify /v1/contact has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/contact']


def test_openapi_spec_has_rack_designer_configurations_endpoint(openapi_spec):
    """Verify spec has /v1/rack-designer/configurations endpoint."""
    assert '/v1/rack-designer/configurations' in openapi_spec['paths']


def test_openapi_spec_rack_designer_configurations_has_post_method(openapi_spec):
    """Verify /v1/rack-designer/configurations has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/rack-designer/configurations']


def test_openapi_spec_rack_designer_configurations_has_options_method(openapi_spec):
    """Verify /v1/rack-designer/configurations has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/rack-designer/configurations']


def test_openapi_spec_has_rack_designer_configuration_hash_endpoint(openapi_spec):
    """Verify spec has /v1/rack-designer/configurations/{config_hash} endpoint."""
    assert '/v1/rack-designer/configurations/{config_hash}' in openapi_spec['paths']


def test_openapi_spec_rack_designer_configuration_hash_has_get_method(openapi_spec):
    """Verify /v1/rack-designer/configurations/{config_hash} has GET method."""
    path = '/v1/rack-designer/configurations/{config_hash}'
    assert 'get' in openapi_spec['paths'][path]


def test_openapi_spec_rack_designer_configuration_hash_has_options_method(openapi_spec):
    """Verify /v1/rack-designer/configurations/{config_hash} has OPTIONS method."""
    path = '/v1/rack-designer/configurations/{config_hash}'
    assert 'options' in openapi_spec['paths'][path]


def test_openapi_spec_has_rack_designer_events_endpoint(openapi_spec):
    """Verify spec has /v1/rack-designer/events endpoint."""
    assert '/v1/rack-designer/events' in openapi_spec['paths']


def test_openapi_spec_rack_designer_events_has_post_method(openapi_spec):
    """Verify /v1/rack-designer/events has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/rack-designer/events']


def test_openapi_spec_rack_designer_events_has_options_method(openapi_spec):
    """Verify /v1/rack-designer/events has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/rack-designer/events']


def test_openapi_spec_diagnostics_echo_has_options_method(openapi_spec):
    """Verify /diagnostics/echo has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/diagnostics/echo']


def test_openapi_spec_jit_runner_requests_has_options_method(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']


def test_openapi_spec_jit_runner_requests_health_has_options_method(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests/health has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests/health']


def test_openapi_spec_ec2_ami_base_has_options_method(openapi_spec):
    """Verify /v1/runners/ec2/images has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ec2/images']


def test_openapi_spec_ec2_ami_latest_has_options_method(openapi_spec):
    """Verify /v1/runners/ec2/images/latest has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ec2/images/latest']


def test_openapi_spec_ec2_ami_delete_has_options_method(openapi_spec):
    """Verify /v1/runners/ec2/images/{ami_id} has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ec2/images/{ami_id}']


def test_openapi_spec_ecs_runner_has_options_method(openapi_spec):
    """Verify /v1/runners/ecs has OPTIONS method."""
    assert 'options' in openapi_spec['paths']['/v1/runners/ecs']


def test_openapi_spec_has_request_validators(openapi_spec):
    """Verify spec has x-amazon-apigateway-request-validators section."""
    assert 'x-amazon-apigateway-request-validators' in openapi_spec


def test_openapi_spec_has_validate_headers_validator(openapi_spec):
    """Verify spec has validate-headers validator defined."""
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert 'validate-headers' in validators


def test_openapi_spec_validate_headers_validates_parameters(openapi_spec):
    """Verify validate-headers validator validates request parameters."""
    validators = openapi_spec['x-amazon-apigateway-request-validators']
    assert validators['validate-headers']['validateRequestParameters'] is True


def test_openapi_spec_jit_runner_requests_post_has_request_validator(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests POST has request validator reference."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    assert 'x-amazon-apigateway-request-validator' in post


def test_openapi_spec_jit_runner_requests_post_uses_validate_headers(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests POST uses validate-headers validator."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    assert post['x-amazon-apigateway-request-validator'] == 'validate-headers'


def test_openapi_spec_jit_runner_requests_post_has_parameters(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests POST has parameters defined."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    assert 'parameters' in post


def test_openapi_spec_jit_runner_requests_post_has_github_event_parameter(openapi_spec):
    """Verify /v1/webhooks/github/jit-runner-requests POST has x-github-event parameter."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    parameters = post['parameters']
    param_names = [p.get('name') for p in parameters]
    assert 'x-github-event' in param_names


def test_openapi_spec_jit_runner_requests_post_github_event_is_header(openapi_spec):
    """Verify x-github-event parameter is a header parameter."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    parameters = post['parameters']
    github_event_param = next(
        (p for p in parameters if p.get('name') == 'x-github-event'),
        None
    )
    assert github_event_param['in'] == 'header'


def test_openapi_spec_jit_runner_requests_post_github_event_is_required(openapi_spec):
    """Verify x-github-event header is required."""
    post = openapi_spec['paths']['/v1/webhooks/github/jit-runner-requests']['post']
    parameters = post['parameters']
    github_event_param = next(
        (p for p in parameters if p.get('name') == 'x-github-event'),
        None
    )
    assert github_event_param['required'] is True


def test_openapi_spec_has_gateway_responses(openapi_spec):
    """Verify spec has x-amazon-apigateway-gateway-responses section."""
    assert 'x-amazon-apigateway-gateway-responses' in openapi_spec


def test_openapi_spec_has_bad_request_parameters_response(openapi_spec):
    """Verify spec has BAD_REQUEST_PARAMETERS gateway response."""
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert 'BAD_REQUEST_PARAMETERS' in responses


def test_openapi_spec_bad_request_parameters_returns_400(openapi_spec):
    """Verify BAD_REQUEST_PARAMETERS returns 400 status code."""
    responses = openapi_spec['x-amazon-apigateway-gateway-responses']
    assert responses['BAD_REQUEST_PARAMETERS']['statusCode'] == 400
