"""Tests for OpenAPI specification validation."""
from pathlib import Path


def _get_openapi_path() -> Path:
    """Get the path to openapi.yml file."""
    base = Path(__file__).parent.parent.parent.parent.parent
    return base / "src" / "www" / "api" / "openapi.yml"


def test_openapi_spec_file_exists():
    """Verify openapi.yml file exists."""
    assert _get_openapi_path().exists()


def test_openapi_spec_is_valid_yaml(openapi_spec):
    """Verify spec is valid YAML."""
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


def test_openapi_spec_has_echo_endpoint(openapi_spec):
    """Verify spec has /v1/echo endpoint."""
    assert '/v1/echo' in openapi_spec['paths']


def test_openapi_spec_echo_has_post_method(openapi_spec):
    """Verify /v1/echo has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/echo']


def test_openapi_spec_has_runners_post_endpoint(openapi_spec):
    """Verify spec has /v1/runners endpoint."""
    assert '/v1/runners' in openapi_spec['paths']


def test_openapi_spec_runners_has_post_method(openapi_spec):
    """Verify /v1/runners has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/runners']


def test_openapi_spec_has_runners_health_endpoint(openapi_spec):
    """Verify spec has /v1/runners/health endpoint."""
    assert '/v1/runners/health' in openapi_spec['paths']


def test_openapi_spec_runners_health_has_get_method(openapi_spec):
    """Verify /v1/runners/health has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/runners/health']


def test_openapi_spec_has_ec2_ami_base_endpoint(openapi_spec):
    """Verify spec has /v1/image-for-ec2-runners endpoint."""
    assert '/v1/image-for-ec2-runners' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_latest_endpoint(openapi_spec):
    """Verify spec has /v1/image-for-ec2-runners/latest endpoint."""
    assert '/v1/image-for-ec2-runners/latest' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_delete_endpoint(openapi_spec):
    """Verify spec has /v1/image-for-ec2-runners/{ami_id} endpoint."""
    assert '/v1/image-for-ec2-runners/{ami_id}' in openapi_spec['paths']


def test_openapi_spec_has_ecs_runner_endpoint(openapi_spec):
    """Verify spec has /v1/ecs-runner endpoint."""
    assert '/v1/ecs-runner' in openapi_spec['paths']


def test_openapi_spec_ecs_runner_has_post_method(openapi_spec):
    """Verify /v1/ecs-runner has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/ecs-runner']


def test_openapi_spec_ecs_runner_has_get_method(openapi_spec):
    """Verify /v1/ecs-runner has GET method."""
    assert 'get' in openapi_spec['paths']['/v1/ecs-runner']


def test_openapi_spec_does_not_have_ecs_runner_latest(openapi_spec):
    """Verify spec does not have /v1/ecs-runner/latest endpoint."""
    assert '/v1/ecs-runner/latest' not in openapi_spec['paths']


def test_openapi_spec_has_ec2_runner_endpoint(openapi_spec):
    """Verify spec has /v1/ec2-runner endpoint."""
    assert '/v1/ec2-runner' in openapi_spec['paths']


def test_openapi_spec_ec2_runner_has_post_method(openapi_spec):
    """Verify /v1/ec2-runner has POST method."""
    assert 'post' in openapi_spec['paths']['/v1/ec2-runner']


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
