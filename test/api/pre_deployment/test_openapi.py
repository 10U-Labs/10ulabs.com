from pathlib import Path


def test_openapi_spec_file_exists():
    openapi_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "files" / "openapi.yml"
    assert openapi_path.exists()


def test_openapi_spec_is_valid_yaml(openapi_spec):
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


def test_openapi_spec_has_echo_endpoint(openapi_spec):
    assert '/v1/echo' in openapi_spec['paths']


def test_openapi_spec_echo_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/echo']


def test_openapi_spec_has_runners_post_endpoint(openapi_spec):
    assert '/v1/runners' in openapi_spec['paths']


def test_openapi_spec_runners_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/runners']


def test_openapi_spec_has_runners_health_endpoint(openapi_spec):
    assert '/v1/runners/health' in openapi_spec['paths']


def test_openapi_spec_runners_health_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/v1/runners/health']


def test_openapi_spec_has_ec2_ami_base_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_latest_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners/latest' in openapi_spec['paths']


def test_openapi_spec_has_ec2_ami_delete_endpoint(openapi_spec):
    assert '/v1/image-for-ec2-runners/{ami_id}' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_base_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_latest_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners/latest' in openapi_spec['paths']


def test_openapi_spec_has_docker_image_delete_endpoint(openapi_spec):
    assert '/v1/image-for-docker-runners/{digest}' in openapi_spec['paths']


def test_openapi_spec_has_docker_runner_endpoint(openapi_spec):
    assert '/v1/docker-runner' in openapi_spec['paths']


def test_openapi_spec_docker_runner_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/docker-runner']


def test_openapi_spec_docker_runner_has_get_method(openapi_spec):
    assert 'get' in openapi_spec['paths']['/v1/docker-runner']


def test_openapi_spec_does_not_have_docker_runner_latest(openapi_spec):
    assert '/v1/docker-runner/latest' not in openapi_spec['paths']


def test_openapi_spec_has_ec2_runner_endpoint(openapi_spec):
    assert '/v1/ec2-runner' in openapi_spec['paths']


def test_openapi_spec_ec2_runner_has_post_method(openapi_spec):
    assert 'post' in openapi_spec['paths']['/v1/ec2-runner']


def test_openapi_spec_has_catchall_endpoint(openapi_spec):
    assert '/{proxy+}' in openapi_spec['paths']


def test_openapi_spec_health_has_options_method(openapi_spec):
    assert 'options' in openapi_spec['paths']['/health']


def test_openapi_spec_health_options_has_mock_integration(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    assert 'x-amazon-apigateway-integration' in options
    assert options['x-amazon-apigateway-integration']['type'] == 'mock'


def test_openapi_spec_health_options_returns_cors_headers(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    assert 'responses' in integration
    assert 'default' in integration['responses']
    response_params = integration['responses']['default'].get('responseParameters', {})
    assert 'method.response.header.Access-Control-Allow-Origin' in response_params
    assert 'method.response.header.Access-Control-Allow-Methods' in response_params
    assert 'method.response.header.Access-Control-Allow-Headers' in response_params


def test_openapi_spec_health_options_allows_wildcard_origin(openapi_spec):
    options = openapi_spec['paths']['/health']['options']
    integration = options['x-amazon-apigateway-integration']
    response_params = integration['responses']['default']['responseParameters']
    origin_value = response_params['method.response.header.Access-Control-Allow-Origin']
    assert "'*'" in origin_value
