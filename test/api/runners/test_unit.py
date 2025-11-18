def test_config_file_exists_in_correct_location(config_path):
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    assert "account_id" in config["aws"]


def test_config_has_aws_region(config):
    assert "region" in config["aws"]


def test_config_has_fqdn(config):
    assert "fqdn" in config


def test_config_has_lambda_function_name(config):
    assert "function_name" in config["aws"]["lambda"]


def test_config_has_lambda_timeout(config):
    assert "timeout_seconds" in config["aws"]["lambda"]


def test_config_has_lambda_memory(config):
    assert "memory_mb" in config["aws"]["lambda"]


def test_runners_stack_creates_lambda_function(cdk_template, function_name):
    cdk_template.has_resource_properties("AWS::Lambda::Function", {
        "FunctionName": function_name,
        "Runtime": "python3.14"
    })


def test_runners_stack_creates_api_gateway_resource(cdk_template):
    resources = cdk_template.find_resources("AWS::ApiGateway::Resource")
    assert len(resources) == 1


def test_runners_stack_creates_api_gateway_method(cdk_template):
    resources = cdk_template.find_resources("AWS::ApiGateway::Method")
    assert len(resources) == 1


def test_webhook_router_handler_file_exists(webhook_router_path):
    assert webhook_router_path.exists()


def test_webhook_router_has_lambda_handler_function(webhook_router_module):
    assert hasattr(webhook_router_module, 'lambda_handler')


def test_webhook_router_has_verify_signature_function(webhook_router_module):
    assert hasattr(webhook_router_module, 'verify_signature')


def test_webhook_router_has_handle_workflow_job_function(webhook_router_module):
    assert hasattr(webhook_router_module, 'handle_workflow_job')


def test_webhook_router_has_route_runner_request_function(webhook_router_module):
    assert hasattr(webhook_router_module, 'route_runner_request')


def test_verify_signature_validates_correct_signature(webhook_router_module):
    import hashlib
    import hmac

    payload = "test payload"
    secret = "test_secret"
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    result = webhook_router_module.verify_signature(payload, f"sha256={signature}", secret)
    assert result is True


def test_verify_signature_rejects_incorrect_signature(webhook_router_module):
    payload = "test payload"
    secret = "test_secret"
    wrong_signature = "sha256=wrong_signature"

    result = webhook_router_module.verify_signature(payload, wrong_signature, secret)
    assert result is False


def test_handle_workflow_job_ignores_non_queued_actions(webhook_router_module):
    event_data = {
        'action': 'completed',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['self-hosted'],
            'status': 'completed'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    result = webhook_router_module.handle_workflow_job(event_data)
    assert result['statusCode'] == 200


def test_handle_workflow_job_ignores_jobs_without_runner_labels(webhook_router_module):
    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['self-hosted', 'linux'],
            'status': 'queued'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    result = webhook_router_module.handle_workflow_job(event_data)
    assert result['statusCode'] == 200


def test_route_runner_request_succeeds_for_ec2_runner(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.route_runner_request(
            job_id=123,
            job_labels=['ephemeral-ec2-spot-instance'],
            github_repo='test/repo'
        )

        assert result['success'] is True


def test_route_runner_request_identifies_ec2_runner_type(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.route_runner_request(
            job_id=123,
            job_labels=['ephemeral-ec2-spot-instance'],
            github_repo='test/repo'
        )

        assert result['runner_type'] == 'ec2'


def test_route_runner_request_succeeds_for_fargate_runner(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.route_runner_request(
            job_id=456,
            job_labels=['ephemeral-ecs-fargate-spot'],
            github_repo='test/repo'
        )

        assert result['success'] is True


def test_route_runner_request_identifies_fargate_runner_type(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.route_runner_request(
            job_id=456,
            job_labels=['ephemeral-ecs-fargate-spot'],
            github_repo='test/repo'
        )

        assert result['runner_type'] == 'fargate'


def test_route_runner_request_returns_error_for_unknown_runner_type(webhook_router_module):
    result = webhook_router_module.route_runner_request(
        job_id=789,
        job_labels=['unknown-runner-type'],
        github_repo='test/repo'
    )

    assert result['success'] is False


def test_handle_workflow_job_returns_success_response(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.handle_workflow_job(event_data)
        assert result['statusCode'] == 200


def test_handle_workflow_job_returns_runner_type_in_success_response(webhook_router_module):
    import json
    from unittest.mock import MagicMock, Mock, patch

    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'success': True}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = webhook_router_module.handle_workflow_job(event_data)
        body = json.loads(result['body'])
        assert body['runner_type'] == 'ec2'


def test_handle_workflow_job_returns_error_response_on_failure(webhook_router_module):
    import urllib.error
    from unittest.mock import patch

    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Network error")):
        result = webhook_router_module.handle_workflow_job(event_data)
        assert result['statusCode'] == 500


def test_handle_workflow_job_includes_error_message_in_failure_response(webhook_router_module):
    import json
    import urllib.error
    from unittest.mock import patch

    event_data = {
        'action': 'queued',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {
            'full_name': 'test/repo'
        }
    }

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Network error")):
        result = webhook_router_module.handle_workflow_job(event_data)
        body = json.loads(result['body'])
        assert 'error' in body


def test_lambda_handler_handles_base64_encoded_body(webhook_router_module):
    import base64
    import json

    payload = {'zen': 'test'}
    body_str = json.dumps(payload)
    encoded_body = base64.b64encode(body_str.encode('utf-8')).decode('utf-8')

    event = {
        'body': encoded_body,
        'isBase64Encoded': True,
        'headers': {
            'x-github-event': 'ping'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    assert result['statusCode'] == 200


def test_lambda_handler_handles_form_encoded_payload(webhook_router_module):
    import json
    import urllib.parse

    payload = {'zen': 'test'}
    encoded_payload = urllib.parse.quote(json.dumps(payload))
    body = f'payload={encoded_payload}'

    event = {
        'body': body,
        'headers': {
            'x-github-event': 'ping'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    assert result['statusCode'] == 200


def test_lambda_handler_returns_400_for_invalid_json(webhook_router_module):
    event = {
        'body': 'invalid json',
        'headers': {
            'x-github-event': 'ping'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    assert result['statusCode'] == 400


def test_lambda_handler_returns_401_for_invalid_signature(webhook_router_module):
    import json
    from unittest.mock import patch

    payload = {'zen': 'test'}
    event = {
        'body': json.dumps(payload),
        'headers': {
            'x-github-event': 'ping',
            'x-hub-signature-256': 'sha256=invalid_signature'
        }
    }

    with patch.object(webhook_router_module, 'get_webhook_secret', return_value='test_secret'):
        result = webhook_router_module.lambda_handler(event, None)
        assert result['statusCode'] == 401


def test_lambda_handler_accepts_valid_signature(webhook_router_module):
    import json
    import hashlib
    import hmac
    from unittest.mock import patch

    payload = {'zen': 'test'}
    body_str = json.dumps(payload)
    secret = 'test_secret'
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=body_str.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    event = {
        'body': body_str,
        'headers': {
            'x-github-event': 'ping',
            'x-hub-signature-256': f'sha256={signature}'
        }
    }

    with patch.object(webhook_router_module, 'get_webhook_secret', return_value=secret):
        result = webhook_router_module.lambda_handler(event, None)
        assert result['statusCode'] == 200


def test_lambda_handler_proceeds_without_signature_header(webhook_router_module):
    import json

    payload = {'zen': 'test'}
    event = {
        'body': json.dumps(payload),
        'headers': {
            'x-github-event': 'ping'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    assert result['statusCode'] == 200


def test_lambda_handler_routes_to_handle_workflow_job(webhook_router_module):
    import json
    from unittest.mock import patch

    payload = {
        'action': 'completed',
        'workflow_job': {
            'id': 123,
            'name': 'test-job'
        }
    }
    event = {
        'body': json.dumps(payload),
        'headers': {
            'x-github-event': 'workflow_job'
        }
    }

    with patch.object(webhook_router_module, 'handle_workflow_job', return_value={'statusCode': 200, 'body': '{}'}) as mock_handle:
        result = webhook_router_module.lambda_handler(event, None)
        mock_handle.assert_called_once_with(payload)
        assert result['statusCode'] == 200


def test_lambda_handler_returns_pong_for_ping_event(webhook_router_module):
    import json

    event = {
        'body': json.dumps({'zen': 'test'}),
        'headers': {
            'x-github-event': 'ping'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    body = json.loads(result['body'])
    assert body['message'] == 'pong'


def test_lambda_handler_ignores_unknown_event_types(webhook_router_module):
    import json

    event = {
        'body': json.dumps({'action': 'opened'}),
        'headers': {
            'x-github-event': 'issues'
        }
    }

    result = webhook_router_module.lambda_handler(event, None)
    assert result['statusCode'] == 200


def test_get_secretsmanager_client_returns_boto3_client(webhook_router_module):
    from unittest.mock import patch, MagicMock

    webhook_router_module._clients['secretsmanager'] = None

    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = webhook_router_module.get_secretsmanager_client()
        mock_boto_client.assert_called_once_with('secretsmanager')
        assert client == mock_client


def test_get_secretsmanager_client_caches_client(webhook_router_module):
    from unittest.mock import patch, MagicMock

    webhook_router_module._clients['secretsmanager'] = None

    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client1 = webhook_router_module.get_secretsmanager_client()
        client2 = webhook_router_module.get_secretsmanager_client()

        assert mock_boto_client.call_count == 1
        assert client1 == client2


def test_get_webhook_secret_retrieves_secret(webhook_router_module):
    from unittest.mock import patch, MagicMock
    import os

    webhook_router_module._webhook_secret_cache['value'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'my_secret_value'}

    with patch.object(webhook_router_module, 'get_secretsmanager_client', return_value=mock_client):
        with patch.dict(os.environ, {'WEBHOOK_SECRET_NAME': 'test-secret'}):
            secret = webhook_router_module.get_webhook_secret()
            mock_client.get_secret_value.assert_called_once_with(SecretId='test-secret')
            assert secret == 'my_secret_value'


def test_get_webhook_secret_caches_secret(webhook_router_module):
    from unittest.mock import patch, MagicMock

    webhook_router_module._webhook_secret_cache['value'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'my_secret_value'}

    with patch.object(webhook_router_module, 'get_secretsmanager_client', return_value=mock_client):
        secret1 = webhook_router_module.get_webhook_secret()
        secret2 = webhook_router_module.get_webhook_secret()

        assert mock_client.get_secret_value.call_count == 1
        assert secret1 == secret2
