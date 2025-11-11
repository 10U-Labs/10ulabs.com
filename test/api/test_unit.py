import json
import sys
from pathlib import Path
import importlib.util
from unittest.mock import Mock, patch
import aws_cdk as cdk
from aws_cdk.assertions import Template
import requests


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    assert config_path.exists()


def test_config_has_aws_account_id():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_account_id" in config


def test_config_has_aws_region():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_region" in config


def test_config_has_subdomain_name():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "subdomain_name" in config


def test_config_has_parent_domain():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "parent_domain" in config


def test_api_has_lambda_function():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    resources = template.find_resources("AWS::Lambda::Function")
    assert len(resources) >= 1


def test_api_has_api_gateway():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_has_certificate():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_api_has_route53_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Route53::RecordSet", 1)


def test_api_has_url_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_has_domain_name_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_api_has_endpoint_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "api" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    ApiStack = api_module.ApiStack

    stack = ApiStack(
        app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws_account_id"]),
            region=config["aws_region"]
        )
    )

    template = Template.from_stack(stack)

    outputs = template.find_outputs("*")
    assert "ApiEndpoint" in outputs


sys.path.insert(0, str(Path(__file__).parents[2] / "src" / "api" / "lambda"))
sys.path.insert(0, str(Path(__file__).parents[2] / "src" / "api"))

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
