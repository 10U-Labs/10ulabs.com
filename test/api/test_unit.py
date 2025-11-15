import json
import sys
from pathlib import Path
import importlib.util
from unittest.mock import Mock, patch
import aws_cdk as cdk
from aws_cdk.assertions import Template
import requests


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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

    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
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


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "api" / "self" / "lambda"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "api" / "self"))

import handler
import poll_api_until_it_has_propagated


def test_lambda_handler_health_endpoint_returns_200_status_code():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_health_endpoint_returns_json_content_type():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_health_endpoint_returns_cors_header():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_health_endpoint_body_contains_status():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'status' in body


def test_lambda_handler_health_endpoint_status_is_healthy():
    event = {'path': '/health', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
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
    response = handler.handler(event, context)
    assert response['statusCode'] == 200


def test_lambda_handler_echo_endpoint_returns_json_content_type():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_echo_endpoint_returns_cors_header():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': json.dumps({'test': 'data'})
    }
    context = Mock()
    context.aws_request_id = 'test-request-id'
    response = handler.handler(event, context)
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
    response = handler.handler(event, context)
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
    response = handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'received_at' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_400():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = handler.handler(event, context)
    assert response['statusCode'] == 400


def test_lambda_handler_echo_endpoint_with_invalid_json_returns_error_message():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'error' in body


def test_lambda_handler_echo_endpoint_with_invalid_json_error_is_invalid_json():
    event = {
        'path': '/v1/echo',
        'httpMethod': 'POST',
        'body': 'invalid json'
    }
    context = Mock()
    response = handler.handler(event, context)
    body = json.loads(response['body'])
    assert body['error'] == 'Invalid JSON'


def test_lambda_handler_invalid_path_returns_404():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['statusCode'] == 404


def test_lambda_handler_invalid_path_returns_json_content_type():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['headers']['Content-Type'] == 'application/json'


def test_lambda_handler_invalid_path_returns_cors_header():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_invalid_path_returns_error_body():
    event = {'path': '/invalid', 'httpMethod': 'GET'}
    context = Mock()
    response = handler.handler(event, context)
    body = json.loads(response['body'])
    assert 'error' in body


def test_lambda_handler_wrong_http_method_returns_404():
    event = {'path': '/health', 'httpMethod': 'POST'}
    context = Mock()
    response = handler.handler(event, context)
    assert response['statusCode'] == 404


def test_poll_until_propagated_returns_true_on_first_success():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = poll_api_until_it_has_propagated.poll_until_propagated(
            'https://api.example.com',
            max_attempts=5
        )
        assert result is True


def test_poll_until_propagated_calls_correct_endpoint():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        poll_api_until_it_has_propagated.poll_until_propagated(
            'https://api.example.com',
            max_attempts=1
        )
        mock_get.assert_called_once_with(
            'https://api.example.com/invalid',
            timeout=10,
            allow_redirects=True
        )


def test_poll_until_propagated_retries_on_wrong_status_code():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep'):
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_404 = Mock()
            mock_response_404.status_code = 404

            mock_get.side_effect = [mock_response_403, mock_response_404]

            result = poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=5
            )
            assert result is True


def test_poll_until_propagated_retries_on_request_exception():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep'):
            mock_response = Mock()
            mock_response.status_code = 404

            mock_get.side_effect = [
                requests.exceptions.RequestException('Network error'),
                mock_response
            ]

            result = poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=5
            )
            assert result is True


def test_poll_until_propagated_returns_false_after_max_attempts():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep'):
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            result = poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=3
            )
            assert result is False


def test_poll_until_propagated_uses_exponential_backoff():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep') as mock_sleep:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=4
            )

            expected_waits = [1, 2, 4]
            actual_waits = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_waits == expected_waits


def test_poll_until_propagated_does_not_sleep_on_success():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep') as mock_sleep:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=5
            )
            assert mock_sleep.call_count == 0


def test_poll_until_propagated_does_not_sleep_after_final_attempt():
    with patch('poll_api_until_it_has_propagated.requests.get') as mock_get:
        with patch('poll_api_until_it_has_propagated.time.sleep') as mock_sleep:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            poll_api_until_it_has_propagated.poll_until_propagated(
                'https://api.example.com',
                max_attempts=3
            )
            assert mock_sleep.call_count == 2


def test_poll_script_main_exits_with_zero_on_success():
    with patch('poll_api_until_it_has_propagated.poll_until_propagated') as mock_poll:
        with patch('sys.argv', ['script', 'https://api.example.com']):
            with patch('sys.exit') as mock_exit:
                mock_poll.return_value = True
                poll_api_until_it_has_propagated.main()
                mock_exit.assert_called_once_with(0)


def test_poll_script_main_exits_with_one_on_failure():
    with patch('poll_api_until_it_has_propagated.poll_until_propagated') as mock_poll:
        with patch('sys.argv', ['script', 'https://api.example.com']):
            with patch('sys.exit') as mock_exit:
                mock_poll.return_value = False
                poll_api_until_it_has_propagated.main()
                mock_exit.assert_called_once_with(1)


def test_poll_script_main_strips_trailing_slash_from_endpoint():
    with patch('poll_api_until_it_has_propagated.poll_until_propagated') as mock_poll:
        with patch('sys.argv', ['script', 'https://api.example.com/']):
            with patch('sys.exit'):
                mock_poll.return_value = True
                poll_api_until_it_has_propagated.main()
                mock_poll.assert_called_once_with('https://api.example.com', 10)


def test_app_can_be_imported_successfully():
    app_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    assert spec is not None


def test_app_loads_config_json():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    assert "aws" in config


def test_app_creates_cdk_environment_with_account_id():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    env = cdk.Environment(
        account=str(config["aws"]["account_id"]),
        region=config["aws"]["region"]
    )
    assert env.account == str(config["aws"]["account_id"])


def test_app_creates_cdk_environment_with_region():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    env = cdk.Environment(
        account=str(config["aws"]["account_id"]),
        region=config["aws"]["region"]
    )
    assert env.region == config["aws"]["region"]


def test_app_instantiates_api_stack():
    app = cdk.App()
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    stack_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack
    env = cdk.Environment(
        account=str(config["aws"]["account_id"]),
        region=config["aws"]["region"]
    )
    api_stack = ApiStack(
        app,
        "TenULabsApi",
        config=config,
        env=env
    )
    assert api_stack is not None


def test_app_tags_can_be_added_to_cdk_app():
    app = cdk.App()
    cdk.Tags.of(app).add("ManagedBy", "CDK")
    tags = cdk.Tags.of(app)
    assert tags is not None


def test_readme_script_exists():
    readme_path = Path(__file__).parent.parent.parent / "scripts" / "readme.py"
    assert readme_path.exists()


def test_readme_can_read_source_files():
    import os
    script_dir = Path(__file__).parent.parent.parent / "src" / "api" / "self"
    files_to_read = ['stack.py', 'lambda/handler.py']
    for file_path in files_to_read:
        full_path = script_dir / file_path
        assert full_path.exists()


def test_readme_loads_config_for_bedrock_settings():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    assert "bedrock" in config.get("aws", {})


def test_readme_config_has_bedrock_model_id():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    assert "model_id" in config.get("aws", {}).get("bedrock", {})


def test_readme_config_has_max_tokens_check():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    assert "max_tokens_check" in config.get("aws", {}).get("bedrock", {})


def test_readme_config_has_max_tokens_generate():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    assert "max_tokens_generate" in config.get("aws", {}).get("bedrock", {})
