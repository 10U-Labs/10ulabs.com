from pathlib import Path
from unittest.mock import Mock
import json


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "config.json"
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    assert "account_id" in config["aws"]


def test_config_has_aws_region(config):
    assert "region" in config["aws"]


def test_config_has_subdomain_name(config):
    assert "subdomain" in config["domain_names"]


def test_config_has_parent_domain(config):
    assert "parent" in config["domain_names"]


def test_api_has_lambda_function(cdk_template):
    resources = cdk_template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 1


def test_api_has_api_gateway(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_gateway_has_no_custom_domain(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::DomainName", 0)


def test_api_has_certificate(cdk_template):
    cdk_template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_api_has_route53_record(cdk_template):
    cdk_template.resource_count_is("AWS::Route53::RecordSet", 1)


def test_api_has_url_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_has_domain_name_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_api_has_endpoint_output(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiEndpoint" in outputs


def test_lambda_handler_health_endpoint_returns_200_status_code(health_handler):
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health_handler.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_health_endpoint_returns_json_content_type(health_handler):
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health_handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_health_endpoint_returns_cors_header(health_handler):
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health_handler.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_health_endpoint_body_contains_status(health_handler):
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health_handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'status' in body


def test_lambda_handler_health_endpoint_status_is_healthy(health_handler):
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health_handler.handler(event, context)
    body = json.loads(response['body'])
    assert body['status'] == 'healthy'


def test_lambda_handler_echo_endpoint_returns_200_status_code(v1_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'}),
        'requestContext': {'requestId': 'test-request-id'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_echo_endpoint_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'}),
        'requestContext': {'requestId': 'test-request-id'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_echo_endpoint_echoes_input_data(v1_handler):
    payload = {'message': 'hello', 'number': 42}
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps(payload),
        'requestContext': {'requestId': 'test-request-id'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    body = json.loads(response['body'])
    assert body['echo'] == payload


def test_lambda_handler_echo_endpoint_includes_received_at(v1_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'}),
        'requestContext': {'requestId': 'test-request-id'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    body = json.loads(response['body'])
    assert 'received_at' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_400(v1_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'not valid json',
        'requestContext': {'requestId': 'test-request-id'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_catchall_returns_404_for_unknown_path(catchall_handler):
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall_handler.handler(event, context)
    assert response['statusCode'] == 404


def test_lambda_handler_catchall_returns_json_content_type(catchall_handler):
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall_handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_catchall_returns_cors_header(catchall_handler):
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall_handler.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_catchall_body_contains_error_message(catchall_handler):
    event = {'path': '/unknown', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall_handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'error' in body


def test_openapi_spec_file_exists():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yml"
    assert openapi_path.exists()


def test_openapi_spec_is_valid_yaml(openapi_spec):
    assert openapi_spec is not None


def test_openapi_spec_has_correct_version(openapi_spec):
    assert 'openapi' in openapi_spec
    assert openapi_spec['openapi'].startswith('3.0')


def test_openapi_spec_has_info_section(openapi_spec):
    assert 'info' in openapi_spec
    assert 'title' in openapi_spec['info']
    assert 'version' in openapi_spec['info']


def test_openapi_spec_has_paths_section(openapi_spec):
    assert 'paths' in openapi_spec
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
    assert 'post' in openapi_spec['paths']['/v1/ec2-runner']


def test_openapi_spec_has_catchall_endpoint(openapi_spec):
    assert '/{proxy+}' in openapi_spec['paths']


def test_lambda_handler_docker_runner_post_with_missing_job_id_returns_400(v1_handler):
    event = {
        'path': '/v1/docker-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'github_repo': '10U-Labs-LLC/10ulabs.com'})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_docker_runner_post_with_missing_repo_returns_400(v1_handler):
    event = {
        'path': '/v1/docker-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'job_id': 12345})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_docker_runner_post_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/docker-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'job_id': 12345, 'github_repo': '10U-Labs-LLC/10ulabs.com'})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_docker_runner_get_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/docker-runner',
        'httpMethod': 'GET'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_docker_runner_unsupported_method_returns_404(v1_handler):
    event = {
        'path': '/v1/docker-runner',
        'httpMethod': 'DELETE'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 404


def test_lambda_handler_ec2_runner_post_with_missing_job_id_returns_400(v1_handler):
    event = {
        'path': '/v1/ec2-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'github_repo': '10U-Labs-LLC/10ulabs.com'})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_ec2_runner_post_with_missing_repo_returns_400(v1_handler):
    event = {
        'path': '/v1/ec2-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'job_id': 12345})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_ec2_runner_post_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/ec2-runner',
        'httpMethod': 'POST',
        'body': json.dumps({'job_id': 12345, 'github_repo': '10U-Labs-LLC/10ulabs.com'})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_docker_runners_post_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-docker-runners',
        'httpMethod': 'POST',
        'body': json.dumps({})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_docker_runners_get_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-docker-runners',
        'httpMethod': 'GET'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_docker_runners_delete_without_digest_returns_400(v1_handler):
    event = {
        'path': '/v1/image-for-docker-runners/sha256:abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_image_for_docker_runners_delete_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-docker-runners/sha256:abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {'digest': 'sha256:abc123'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_docker_runners_unsupported_method_returns_404(v1_handler):
    event = {
        'path': '/v1/image-for-docker-runners',
        'httpMethod': 'PUT'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 404


def test_lambda_handler_image_for_ec2_runners_post_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-ec2-runners',
        'httpMethod': 'POST',
        'body': json.dumps({})
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_ec2_runners_get_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-ec2-runners',
        'httpMethod': 'GET'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_ec2_runners_delete_without_ami_id_returns_400(v1_handler):
    event = {
        'path': '/v1/image-for-ec2-runners/ami-abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_image_for_ec2_runners_delete_returns_json_content_type(v1_handler):
    event = {
        'path': '/v1/image-for-ec2-runners/ami-abc123',
        'httpMethod': 'DELETE',
        'pathParameters': {'ami_id': 'ami-abc123'}
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_image_for_ec2_runners_unsupported_method_returns_404(v1_handler):
    event = {
        'path': '/v1/image-for-ec2-runners',
        'httpMethod': 'PATCH'
    }
    context = Mock()
    response = v1_handler.lambda_handler(event, context)
    assert response['statusCode'] == 404
