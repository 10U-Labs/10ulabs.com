from pathlib import Path
from unittest.mock import Mock
import json


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
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


def test_lambda_handler_echo_endpoint_returns_200_status_code(echo_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_echo_endpoint_returns_json_content_type(echo_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_echo_endpoint_returns_cors_header(echo_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_echo_endpoint_echoes_input_data(echo_handler):
    payload = {'message': 'hello', 'number': 42}
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps(payload)
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
    body = json.loads(response['body'])
    assert body['echo'] == payload


def test_lambda_handler_echo_endpoint_includes_received_at(echo_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'received_at' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_400(echo_handler):
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'not valid json'
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo_handler.handler(event, context)
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
