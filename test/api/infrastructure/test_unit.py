import json
import sys
from pathlib import Path
import importlib.util
from unittest.mock import Mock, patch
import yaml
import aws_cdk as cdk
from aws_cdk.assertions import Template


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


def test_api_has_lambda_function():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    resources = template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 1


def test_api_has_api_gateway():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_gateway_has_no_custom_domain():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ApiGateway::DomainName", 0)


def test_api_has_certificate():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_api_has_route53_record():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Route53::RecordSet", 1)


def test_api_has_url_output():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_has_domain_name_output():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_api_has_endpoint_output():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiEndpoint" in outputs


health_handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "health" / "handler.py"
spec = importlib.util.spec_from_file_location("health_handler", health_handler_path)
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)

echo_handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "echo" / "handler.py"
spec = importlib.util.spec_from_file_location("echo_handler", echo_handler_path)
echo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(echo)

catchall_handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "catchall" / "handler.py"
spec = importlib.util.spec_from_file_location("catchall_handler", catchall_handler_path)
catchall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catchall)



def test_lambda_handler_health_endpoint_returns_200_status_code():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_health_endpoint_returns_json_content_type():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_health_endpoint_returns_cors_header():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_health_endpoint_body_contains_status():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health.handler(event, context)
    body = json.loads(response['body'])
    assert 'status' in body


def test_lambda_handler_health_endpoint_status_is_healthy():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = health.handler(event, context)
    body = json.loads(response['body'])
    assert body['status'] == 'healthy'


def test_lambda_handler_echo_endpoint_returns_200_status_code():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_echo_endpoint_returns_json_content_type():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_echo_endpoint_returns_cors_header():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_echo_endpoint_echoes_input_data():
    payload = {'message': 'hello', 'number': 42}
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps(payload)
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo.handler(event, context)
    body = json.loads(response['body'])
    assert body['echo'] == payload


def test_lambda_handler_echo_endpoint_includes_received_at():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = echo.handler(event, context)
    body = json.loads(response['body'])
    assert 'received_at' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_400():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = echo.handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_error_message():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = echo.handler(event, context)
    body = json.loads(response['body'])
    assert 'error' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_error_is_invalid_json():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = echo.handler(event, context)
    body = json.loads(response['body'])
    assert body['error'] == 'Invalid JSON'


def test_lambda_handler_catchall_endpoint_returns_404_status_code():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    assert response['statusCode'] == 404


def test_lambda_handler_catchall_endpoint_returns_json_content_type():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_catchall_endpoint_returns_cors_header():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_catchall_endpoint_body_contains_error():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    body = json.loads(response['body'])
    assert 'error' in body


def test_lambda_handler_catchall_endpoint_error_is_not_found():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    body = json.loads(response['body'])
    assert body['error'] == 'Not Found'


def test_lambda_handler_catchall_endpoint_includes_path():
    event = {'path': '/some/random/path', 'httpMethod': 'GET'}
    context = Mock()
    response = catchall.handler(event, context)
    body = json.loads(response['body'])
    assert body['path'] == '/some/random/path'


def test_openapi_spec_file_exists():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yaml"
    assert openapi_path.exists()


def test_openapi_spec_has_paths():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yaml"
    with open(openapi_path, encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    assert 'paths' in spec


def test_openapi_spec_has_health_path():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yaml"
    with open(openapi_path, encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    assert '/health' in spec['paths']


def test_openapi_spec_has_echo_path():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yaml"
    with open(openapi_path, encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    assert '/v1/echo' in spec['paths']


def test_openapi_spec_has_catchall_path():
    openapi_path = Path(__file__).parent.parent.parent / "src" / "api" / "openapi.yaml"
    with open(openapi_path, encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    assert '/{proxy+}' in spec['paths']


def test_api_has_three_lambda_functions():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    resources = template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 3


def test_health_endpoint_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "health" / "handler.py"
    assert handler_path.exists()


def test_echo_endpoint_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "echo" / "handler.py"
    assert handler_path.exists()


def test_catchall_endpoint_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "catchall" / "handler.py"
    assert handler_path.exists()


def test_api_has_explicit_deployment_construct():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    resources = template.find_resources("AWS::ApiGateway::Deployment")
    assert len(resources) >= 1


def test_api_has_explicit_stage_construct():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    resources = template.find_resources("AWS::ApiGateway::Stage")
    assert len(resources) >= 1


def test_api_stage_name_is_prod():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    stages = template.find_resources("AWS::ApiGateway::Stage")
    stage_name = list(stages.values())[0]["Properties"]["StageName"]
    assert stage_name == "prod"


def test_s3_bucket_has_versioning_disabled():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    buckets = template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    versioning_config = bucket.get("Properties", {}).get("VersioningConfiguration", {})
    status = versioning_config.get("Status", "Suspended")
    assert status != "Enabled"


def test_s3_bucket_has_encryption():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    buckets = template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    assert "BucketEncryption" in bucket.get("Properties", {})


def test_s3_bucket_blocks_public_access():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    buckets = template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    assert "PublicAccessBlockConfiguration" in bucket.get("Properties", {})


def test_api_has_lambda_invoke_permissions():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    permissions = template.find_resources("AWS::Lambda::Permission")
    assert len(permissions) >= 2


def test_lambda_permissions_allow_apigateway_service():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    permissions = template.find_resources("AWS::Lambda::Permission")
    permission = list(permissions.values())[0]
    assert permission["Properties"]["Principal"] == "apigateway.amazonaws.com"


def test_cloudfront_origin_uses_api_gateway_execute_api_url():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    api_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::Join" in o["DomainName"]][0]
    domain_parts = api_origin["DomainName"]["Fn::Join"][1]
    assert any("execute-api" in str(part) for part in domain_parts)


def test_cloudfront_origin_has_prod_path():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    api_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::Join" in o["DomainName"]][0]
    assert api_origin["OriginPath"] == "/prod"


def test_vpc_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_vpc_has_correct_cidr():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    vpcs = template.find_resources("AWS::EC2::VPC")
    vpc = list(vpcs.values())[0]
    assert vpc["Properties"]["CidrBlock"] == config["aws"]["vpc"]["cidr"]


def test_vpc_has_dns_enabled():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    vpcs = template.find_resources("AWS::EC2::VPC")
    vpc = list(vpcs.values())[0]
    assert vpc["Properties"]["EnableDnsHostnames"] is True


def test_vpc_has_public_subnets():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    subnets = template.find_resources("AWS::EC2::Subnet")
    assert len(subnets) > 0


def test_ecs_cluster_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_ecr_repository_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ECR::Repository", 1)


def test_ecr_repository_has_image_scanning():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    repositories = template.find_resources("AWS::ECR::Repository")
    repository = list(repositories.values())[0]
    assert repository["Properties"]["ImageScanningConfiguration"]["ScanOnPush"] is True


def test_fargate_task_definition_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ECS::TaskDefinition", 1)


def test_security_group_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::EC2::SecurityGroup", 1)


def test_ec2_runner_role_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    roles = template.find_resources("AWS::IAM::Role")
    assert len(roles) > 0


def test_cloudfront_has_health_behavior():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    health_behavior = [b for b in behaviors if b["PathPattern"] == "/health"][0]
    assert health_behavior is not None


def test_cloudfront_has_v1_behavior():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    v1_behavior = [b for b in behaviors if b["PathPattern"] == "/v1/*"][0]
    assert v1_behavior is not None


def test_cloudfront_default_behavior_routes_to_api_gateway():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    api_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::Join" in o["DomainName"]][0]
    api_origin_id = api_origin["Id"]
    default_behavior = distribution["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
    assert default_behavior["TargetOriginId"] == api_origin_id


def test_cloudfront_root_path_routes_to_s3():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    s3_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::GetAtt" in o["DomainName"]][0]
    s3_origin_id = s3_origin["Id"]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    root_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/"][0]
    assert root_behavior["TargetOriginId"] == s3_origin_id


def test_cloudfront_openapi_yaml_routes_to_s3():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    s3_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::GetAtt" in o["DomainName"]][0]
    s3_origin_id = s3_origin["Id"]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    openapi_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/openapi.yaml"][0]
    assert openapi_behavior["TargetOriginId"] == s3_origin_id


def test_cloudfront_404_html_routes_to_s3():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    origins = distribution["Properties"]["DistributionConfig"]["Origins"]
    s3_origin = [o for o in origins if isinstance(o["DomainName"], dict) and "Fn::GetAtt" in o["DomainName"]][0]
    s3_origin_id = s3_origin["Id"]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    html_404_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/404.html"][0]
    assert html_404_behavior["TargetOriginId"] == s3_origin_id


def test_cloudfront_health_behavior_does_not_forward_host_header():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    health_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/health"][0]
    assert health_behavior["OriginRequestPolicyId"] == "b689b0a8-53d0-40ab-baf2-68738e2966ac"


def test_cloudfront_v1_behavior_does_not_forward_host_header():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    v1_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/v1/*"][0]
    assert v1_behavior["OriginRequestPolicyId"] == "b689b0a8-53d0-40ab-baf2-68738e2966ac"


def test_cloudfront_function_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::CloudFront::Function", 1)


def test_cloudfront_root_behavior_has_function_association():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    root_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/"][0]
    assert "FunctionAssociations" in root_behavior


def test_cloudfront_root_behavior_function_is_viewer_request():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    root_behavior = [b for b in cache_behaviors if b["PathPattern"] == "/"][0]
    function_associations = root_behavior["FunctionAssociations"]
    assert len(function_associations) == 1
    assert function_associations[0]["EventType"] == "viewer-request"


def test_waf_web_acl_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::WAFv2::WebACL", 1)


def test_waf_is_scoped_to_cloudfront():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    waf_acls = template.find_resources("AWS::WAFv2::WebACL")
    waf_acl = list(waf_acls.values())[0]
    assert waf_acl["Properties"]["Scope"] == "CLOUDFRONT"


def test_secrets_manager_webhook_secret_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_vpc_has_no_nat_gateways():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    nat_gateways = template.find_resources("AWS::EC2::NatGateway")
    assert len(nat_gateways) == 0


def test_cloudfront_invalidation_custom_resource_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    custom_resources = template.find_resources("Custom::AWS")
    assert len(custom_resources) >= 1


def test_cloudfront_invalidation_calls_cloudfront_service():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    custom_resources = template.find_resources("Custom::AWS")
    custom_resource = list(custom_resources.values())[0]
    update_config = str(custom_resource["Properties"]["Update"])
    assert "CloudFront" in update_config


def test_cloudfront_invalidation_has_create_invalidation_permission():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    policies = template.find_resources("AWS::IAM::Policy")
    has_permission = False
    for policy in policies.values():
        policy_doc = policy.get("Properties", {}).get("PolicyDocument", {})
        statements = policy_doc.get("Statement", [])
        for statement in statements:
            action = statement.get("Action", "")
            if action == "cloudfront:CreateInvalidation":
                has_permission = True
    assert has_permission


def test_cloudfront_invalidation_targets_health_path():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    custom_resources = template.find_resources("Custom::AWS")
    custom_resource = list(custom_resources.values())[0]
    update_config = str(custom_resource["Properties"]["Update"])
    assert '"/health"' in update_config


def test_cloudfront_invalidation_targets_v1_path():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    custom_resources = template.find_resources("Custom::AWS")
    custom_resource = list(custom_resources.values())[0]
    update_config = str(custom_resource["Properties"]["Update"])
    assert '"/v1/*"' in update_config

def test_cloudfront_cache_policy_has_correct_ttl():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    cache_policies = template.find_resources("AWS::CloudFront::CachePolicy")
    cache_policy = list(cache_policies.values())[0]
    policy_config = cache_policy["Properties"]["CachePolicyConfig"]
    assert policy_config["DefaultTTL"] == 86400 and policy_config["MinTTL"] == 60 and policy_config["MaxTTL"] == 31536000

def test_cloudfront_cache_policy_compression_enabled():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    cache_policies = template.find_resources("AWS::CloudFront::CachePolicy")
    cache_policy = list(cache_policies.values())[0]
    policy_config = cache_policy["Properties"]["CachePolicyConfig"]
    assert policy_config["ParametersInCacheKeyAndForwardedToOrigin"]["EnableAcceptEncodingGzip"] is True and policy_config["ParametersInCacheKeyAndForwardedToOrigin"]["EnableAcceptEncodingBrotli"] is True

def test_s3_behaviors_use_custom_cache_policy():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    s3_behaviors = [b for b in cache_behaviors if b["PathPattern"] in ["/", "/openapi.yaml", "/404.html"]]
    cache_policy_ids = [b.get("CachePolicyId") for b in s3_behaviors]
    assert len(cache_policy_ids) == 3 and all(policy_id is not None and policy_id != "" for policy_id in cache_policy_ids)

def test_api_behaviors_disable_caching():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    distribution = list(distributions.values())[0]
    cache_behaviors = distribution["Properties"]["DistributionConfig"]["CacheBehaviors"]
    api_behaviors = [b for b in cache_behaviors if b["PathPattern"] in ["/health", "/v1/*"]]
    cache_policy_ids = [b.get("CachePolicyId") for b in api_behaviors]
    assert all(policy_id == "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" for policy_id in cache_policy_ids)

def test_api_gateway_spec_contains_health_integration():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    rest_apis = template.find_resources("AWS::ApiGateway::RestApi")
    rest_api = list(rest_apis.values())[0]
    body = rest_api["Properties"]["Body"]
    assert "/health" in body["paths"]

def test_api_gateway_spec_contains_echo_integration():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    rest_apis = template.find_resources("AWS::ApiGateway::RestApi")
    rest_api = list(rest_apis.values())[0]
    body = rest_api["Properties"]["Body"]
    assert "/v1/echo" in body["paths"]

def test_api_gateway_spec_contains_catchall_integration():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    rest_apis = template.find_resources("AWS::ApiGateway::RestApi")
    rest_api = list(rest_apis.values())[0]
    body = rest_api["Properties"]["Body"]
    assert "/{proxy+}" in body["paths"]

def test_api_gateway_integration_points_to_correct_lambda():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    rest_apis = template.find_resources("AWS::ApiGateway::RestApi")
    rest_api = list(rest_apis.values())[0]
    body = rest_api["Properties"]["Body"]
    health_integration = body["paths"]["/health"]["get"]["x-amazon-apigateway-integration"]["uri"]
    assert isinstance(health_integration, dict) and "Fn::Join" in health_integration

def test_s3_deployment_exists():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    template.resource_count_is("Custom::CDKBucketDeployment", 1)

def test_s3_deployment_points_to_docs_bucket():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    bucket_deployments = template.find_resources("Custom::CDKBucketDeployment")
    deployment = list(bucket_deployments.values())[0]
    assert "DestinationBucketName" in deployment["Properties"]

def test_s3_deployment_has_prune_disabled():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    bucket_deployments = template.find_resources("Custom::CDKBucketDeployment")
    deployment = list(bucket_deployments.values())[0]
    assert deployment["Properties"]["Prune"] is False

def test_s3_deployment_has_source_asset():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    bucket_deployments = template.find_resources("Custom::CDKBucketDeployment")
    deployment = list(bucket_deployments.values())[0]
    assert len(deployment["Properties"]["SourceObjectKeys"]) == 1

def test_lambdas_have_correct_timeout():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    lambdas = template.find_resources("AWS::Lambda::Function")
    api_lambdas = {name: lamb for name, lamb in lambdas.items() if "Handler" in name and "Custom" not in name and "LogRetention" not in name and "AWS679" not in name}
    timeouts = [lamb["Properties"]["Timeout"] for lamb in api_lambdas.values()]
    assert all(timeout == 10 for timeout in timeouts)

def test_lambdas_have_log_retention():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    log_groups = template.find_resources("Custom::LogRetention")
    retentions = [lg["Properties"]["RetentionInDays"] for lg in log_groups.values()]
    assert all(retention == 7 for retention in retentions)

def test_lambdas_have_correct_runtime():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    lambdas = template.find_resources("AWS::Lambda::Function")
    api_lambdas = {name: lamb for name, lamb in lambdas.items() if "Handler" in name and "Custom" not in name and "LogRetention" not in name and "AWS679" not in name}
    runtimes = [lamb["Properties"]["Runtime"] for lamb in api_lambdas.values()]
    assert all(runtime == "python3.14" for runtime in runtimes)

def test_cloudfront_function_code_contains_uri_rewrite():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    functions = template.find_resources("AWS::CloudFront::Function")
    function = list(functions.values())[0]
    code = function["Properties"]["FunctionCode"]
    assert "request.uri = '/index.html'" in code

def test_cloudfront_function_rewrites_root_to_index():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )
    template = Template.from_stack(stack)
    functions = template.find_resources("AWS::CloudFront::Function")
    function = list(functions.values())[0]
    code = function["Properties"]["FunctionCode"]
    assert "request.uri === '/'" in code
