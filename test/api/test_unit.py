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


def test_api_has_two_lambda_functions():
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
    assert len(resources) >= 2


def test_health_endpoint_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "health" / "handler.py"
    assert handler_path.exists()


def test_echo_endpoint_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "echo" / "handler.py"
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
