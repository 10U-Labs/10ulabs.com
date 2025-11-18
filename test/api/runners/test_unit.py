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


def test_get_webhook_secret_raises_runtime_error_on_secrets_manager_failure(webhook_router_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError
    import pytest

    webhook_router_module._webhook_secret_cache['value'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'InternalServiceError', 'Message': 'Service unavailable'}},
        'GetSecretValue'
    )

    with patch.object(webhook_router_module, 'get_secretsmanager_client', return_value=mock_client):
        with pytest.raises(RuntimeError):
            webhook_router_module.get_webhook_secret()


def test_lambda_handler_returns_500_when_secret_retrieval_fails_with_signature(webhook_router_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError
    import json

    webhook_router_module._webhook_secret_cache['value'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'InternalServiceError', 'Message': 'Service unavailable'}},
        'GetSecretValue'
    )

    event = {
        'body': json.dumps({'action': 'queued'}),
        'headers': {
            'x-hub-signature-256': 'sha256=abcd1234',
            'x-github-event': 'workflow_job'
        }
    }

    with patch.object(webhook_router_module, 'get_secretsmanager_client', return_value=mock_client):
        result = webhook_router_module.lambda_handler(event, None)
        assert result['statusCode'] == 500


def test_configure_webhook_handler_file_exists(configure_webhook_handler_path):
    assert configure_webhook_handler_path.exists()


def test_configure_webhook_handler_has_get_github_pat_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'get_github_pat')


def test_configure_webhook_handler_has_get_or_create_webhook_secret_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'get_or_create_webhook_secret')


def test_configure_webhook_handler_has_create_github_webhook_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'create_github_webhook')


def test_configure_webhook_handler_has_delete_github_webhook_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'delete_github_webhook')


def test_configure_webhook_handler_has_send_response_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'send_response')


def test_configure_webhook_handler_has_lambda_handler_function(configure_webhook_handler_module):
    assert hasattr(configure_webhook_handler_module, 'lambda_handler')


def test_get_github_pat_retrieves_secret_successfully(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'ghp_test_token_12345'}

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        result = configure_webhook_handler_module.get_github_pat()
        assert result == 'ghp_test_token_12345'


def test_get_github_pat_uses_environment_variable_for_secret_name(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import os

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'test_token'}

    with patch.dict(os.environ, {'GITHUB_PAT_SECRET_NAME': 'custom-pat-secret'}):
        with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
            configure_webhook_handler_module.get_github_pat()
            mock_client.get_secret_value.assert_called_with(SecretId='custom-pat-secret')


def test_get_github_pat_returns_empty_string_on_client_error(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        result = configure_webhook_handler_module.get_github_pat()
        assert result == ''


def test_get_github_pat_returns_empty_string_when_secret_not_found(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        result = configure_webhook_handler_module.get_github_pat()
        assert result == ''


def test_get_github_pat_logs_error_on_failure(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'InternalServiceError', 'Message': 'Internal error'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        with patch.object(configure_webhook_handler_module.logger, 'error') as mock_logger:
            configure_webhook_handler_module.get_github_pat()
            assert mock_logger.called


def test_get_or_create_webhook_secret_returns_existing_secret(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'existing_webhook_secret_value'}

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        result = configure_webhook_handler_module.get_or_create_webhook_secret()
        assert result == 'existing_webhook_secret_value'


def test_get_or_create_webhook_secret_creates_new_secret_when_not_found(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.exceptions.ResourceNotFoundException = type('ResourceNotFoundException', (ClientError,), {})
    mock_client.get_secret_value.side_effect = mock_client.exceptions.ResourceNotFoundException(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Not found'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        with patch('secrets.token_urlsafe', return_value='new_generated_secret'):
            result = configure_webhook_handler_module.get_or_create_webhook_secret()
            assert result == 'new_generated_secret'


def test_get_or_create_webhook_secret_calls_create_secret_with_correct_parameters(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError
    import os

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.exceptions.ResourceNotFoundException = type('ResourceNotFoundException', (ClientError,), {})
    mock_client.get_secret_value.side_effect = mock_client.exceptions.ResourceNotFoundException(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Not found'}},
        'GetSecretValue'
    )

    with patch.dict(os.environ, {'WEBHOOK_SECRET_NAME': 'test-webhook-secret'}):
        with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
            with patch('secrets.token_urlsafe', return_value='generated_secret'):
                configure_webhook_handler_module.get_or_create_webhook_secret()
                mock_client.create_secret.assert_called_once_with(
                    Name='test-webhook-secret',
                    SecretString='generated_secret',
                    Description='GitHub webhook secret for runners endpoint'
                )


def test_get_or_create_webhook_secret_logs_creation(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.exceptions.ResourceNotFoundException = type('ResourceNotFoundException', (ClientError,), {})
    mock_client.get_secret_value.side_effect = mock_client.exceptions.ResourceNotFoundException(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Not found'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        with patch('secrets.token_urlsafe', return_value='new_secret'):
            with patch.object(configure_webhook_handler_module.logger, 'info') as mock_logger:
                configure_webhook_handler_module.get_or_create_webhook_secret()
                assert mock_logger.called


def test_get_or_create_webhook_secret_returns_empty_string_on_other_client_errors(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.exceptions.ResourceNotFoundException = type('ResourceNotFoundException', (ClientError,), {})
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        result = configure_webhook_handler_module.get_or_create_webhook_secret()
        assert result == ''


def test_get_or_create_webhook_secret_logs_error_on_failure(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ClientError

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.exceptions.ResourceNotFoundException = type('ResourceNotFoundException', (ClientError,), {})
    mock_client.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'InternalServiceError', 'Message': 'Internal error'}},
        'GetSecretValue'
    )

    with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
        with patch.object(configure_webhook_handler_module.logger, 'error') as mock_logger:
            configure_webhook_handler_module.get_or_create_webhook_secret()
            assert mock_logger.called


def test_get_or_create_webhook_secret_uses_environment_variable_for_secret_name(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import os

    configure_webhook_handler_module._clients['secretsmanager'] = None

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {'SecretString': 'secret_value'}

    with patch.dict(os.environ, {'WEBHOOK_SECRET_NAME': 'custom-webhook-secret'}):
        with patch.object(configure_webhook_handler_module, 'get_secretsmanager_client', return_value=mock_client):
            configure_webhook_handler_module.get_or_create_webhook_secret()
            mock_client.get_secret_value.assert_called_with(SecretId='custom-webhook-secret')


def test_create_github_webhook_returns_success_on_valid_response(configure_webhook_handler_module):
    from unittest.mock import patch, Mock
    import json

    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'id': 12345, 'active': True}).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'webhook_secret_123',
            'ghp_token_456',
            '10U-Labs-LLC/10ulabs.com'
        )
        assert result['success'] is True


def test_create_github_webhook_returns_webhook_id_on_success(configure_webhook_handler_module):
    from unittest.mock import patch, Mock
    import json

    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'id': 98765}).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert result['webhook_id'] == 98765


def test_create_github_webhook_handles_http_422_duplicate(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    error_response = b'{"message":"Hook already exists"}'
    mock_error = urllib.error.HTTPError(
        'url', 422, 'Unprocessable Entity', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: error_response})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_handles_http_401_unauthorized(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError(
        'url', 401, 'Unauthorized', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: b'{"message":"Bad credentials"}'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'invalid_token',
            'owner/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_handles_http_403_forbidden(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError(
        'url', 403, 'Forbidden', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: b'{"message":"Forbidden"}'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_handles_http_404_not_found(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError(
        'url', 404, 'Not Found', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: b'{"message":"Not Found"}'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'nonexistent/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_includes_error_code_in_failure_response(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError(
        'url', 500, 'Internal Server Error', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: b'Server error'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert 'HTTP 500' in result['error']


def test_create_github_webhook_handles_url_error_network_failure(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Network unreachable')):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_handles_invalid_json_response(configure_webhook_handler_module):
    from unittest.mock import patch, Mock

    mock_response = Mock()
    mock_response.read.return_value = b'invalid json'
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = configure_webhook_handler_module.create_github_webhook(
            'https://api.10ulabs.com/v1/runners',
            'secret',
            'token',
            'owner/repo'
        )
        assert result['success'] is False


def test_create_github_webhook_logs_success(configure_webhook_handler_module):
    from unittest.mock import patch, Mock
    import json

    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'id': 12345}).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        with patch.object(configure_webhook_handler_module.logger, 'info') as mock_logger:
            configure_webhook_handler_module.create_github_webhook(
                'https://api.10ulabs.com/v1/runners',
                'secret',
                'token',
                'owner/repo'
            )
            assert mock_logger.called


def test_create_github_webhook_logs_error_on_failure(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError(
        'url', 500, 'Internal Server Error', {},
        None
    )
    mock_error.fp = type('obj', (object,), {'read': lambda: b'Error'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        with patch.object(configure_webhook_handler_module.logger, 'error') as mock_logger:
            configure_webhook_handler_module.create_github_webhook(
                'https://api.10ulabs.com/v1/runners',
                'secret',
                'token',
                'owner/repo'
            )
            assert mock_logger.called


def test_delete_github_webhook_returns_success_on_successful_deletion(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is True


def test_delete_github_webhook_handles_http_404_as_success(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
    mock_error.fp = None

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is True


def test_delete_github_webhook_handles_http_401_unauthorized(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError('url', 401, 'Unauthorized', {}, None)
    mock_error.fp = type('obj', (object,), {'read': lambda: b'Unauthorized'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is False


def test_delete_github_webhook_handles_http_403_forbidden(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)
    mock_error.fp = type('obj', (object,), {'read': lambda: b'Forbidden'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is False


def test_delete_github_webhook_handles_http_500_server_error(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError('url', 500, 'Internal Server Error', {}, None)
    mock_error.fp = type('obj', (object,), {'read': lambda: b'Server error'})()

    with patch('urllib.request.urlopen', side_effect=mock_error):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is False


def test_delete_github_webhook_handles_url_error_network_failure(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Network unreachable')):
        result = configure_webhook_handler_module.delete_github_webhook(
            123456,
            'ghp_test_token',
            'owner/repo'
        )
        assert result['success'] is False


def test_delete_github_webhook_logs_success(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        with patch.object(configure_webhook_handler_module.logger, 'info') as mock_logger:
            configure_webhook_handler_module.delete_github_webhook(
                123456,
                'ghp_test_token',
                'owner/repo'
            )
            assert mock_logger.called


def test_delete_github_webhook_logs_warning_on_404(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    mock_error = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
    mock_error.fp = None

    with patch('urllib.request.urlopen', side_effect=mock_error):
        with patch.object(configure_webhook_handler_module.logger, 'warning') as mock_logger:
            configure_webhook_handler_module.delete_github_webhook(
                123456,
                'ghp_test_token',
                'owner/repo'
            )
            assert mock_logger.called


def test_send_response_returns_true_on_success(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )
        assert result is True


def test_send_response_includes_status_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['Status'] == 'SUCCESS'


def test_send_response_includes_reason_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['Reason'] == 'Test reason'


def test_send_response_includes_physical_resource_id_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['PhysicalResourceId'] == 'physical-id-123'


def test_send_response_includes_stack_id_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['StackId'] == event['StackId']


def test_send_response_includes_request_id_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['RequestId'] == event['RequestId']


def test_send_response_includes_logical_resource_id_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['LogicalResourceId'] == event['LogicalResourceId']


def test_send_response_includes_data_in_body(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock
    import json

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {'key': 'value'}
        )

        body = json.loads(captured_request.data.decode('utf-8'))
        assert body['Data'] == {'key': 'value'}


def test_send_response_uses_put_method(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    captured_request = None

    def capture_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return mock_response

    with patch('urllib.request.urlopen', side_effect=capture_urlopen):
        configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {}
        )

        assert captured_request.get_method() == 'PUT'


def test_send_response_returns_false_on_url_error(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Network error')):
        result = configure_webhook_handler_module.send_response(
            event,
            'SUCCESS',
            'Test reason',
            'physical-id-123',
            {}
        )
        assert result is False


def test_send_response_logs_success(configure_webhook_handler_module):
    from unittest.mock import patch, MagicMock

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        with patch.object(configure_webhook_handler_module.logger, 'info') as mock_logger:
            configure_webhook_handler_module.send_response(
                event,
                'SUCCESS',
                'Test reason',
                'physical-id-123',
                {}
            )
            assert mock_logger.called


def test_send_response_logs_error_on_failure(configure_webhook_handler_module):
    from unittest.mock import patch
    import urllib.error

    event = {
        'ResponseURL': 'https://cloudformation-custom-resource-response.s3.amazonaws.com/test',
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource'
    }

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Network error')):
        with patch.object(configure_webhook_handler_module.logger, 'error') as mock_logger:
            configure_webhook_handler_module.send_response(
                event,
                'SUCCESS',
                'Test reason',
                'physical-id-123',
                {}
            )
            assert mock_logger.called


def test_lambda_handler_returns_200_on_successful_create(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': True, 'webhook_id': 12345}):
                with patch.object(configure_webhook_handler_module, 'send_response'):
                    result = configure_webhook_handler_module.lambda_handler(event, None)
                    assert result['statusCode'] == 200


def test_lambda_handler_returns_webhook_id_on_successful_create(configure_webhook_handler_module):
    from unittest.mock import patch
    import json

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': True, 'webhook_id': 12345}):
                with patch.object(configure_webhook_handler_module, 'send_response'):
                    result = configure_webhook_handler_module.lambda_handler(event, None)
                    body = json.loads(result['body'])
                    assert body['webhook_id'] == 12345


def test_lambda_handler_returns_500_when_github_pat_fails_on_create(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value=''):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'send_response'):
                result = configure_webhook_handler_module.lambda_handler(event, None)
                assert result['statusCode'] == 500


def test_lambda_handler_returns_500_when_webhook_secret_fails_on_create(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value=''):
            with patch.object(configure_webhook_handler_module, 'send_response'):
                result = configure_webhook_handler_module.lambda_handler(event, None)
                assert result['statusCode'] == 500


def test_lambda_handler_returns_500_when_create_webhook_fails(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': False, 'error': 'API error'}):
                with patch.object(configure_webhook_handler_module, 'send_response'):
                    result = configure_webhook_handler_module.lambda_handler(event, None)
                    assert result['statusCode'] == 500


def test_lambda_handler_returns_200_on_successful_delete(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Delete',
        'ResourceProperties': {
            'WebhookId': '12345',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response',
        'PhysicalResourceId': 'github-webhook-owner-repo'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'delete_github_webhook', return_value={'success': True}):
            with patch.object(configure_webhook_handler_module, 'send_response'):
                result = configure_webhook_handler_module.lambda_handler(event, None)
                assert result['statusCode'] == 200


def test_lambda_handler_returns_200_when_no_webhook_id_on_delete(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Delete',
        'ResourceProperties': {
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response',
        'PhysicalResourceId': 'github-webhook-owner-repo'
    }

    with patch.object(configure_webhook_handler_module, 'send_response'):
        result = configure_webhook_handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 200


def test_lambda_handler_returns_500_when_github_pat_fails_on_delete(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Delete',
        'ResourceProperties': {
            'WebhookId': '12345',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response',
        'PhysicalResourceId': 'github-webhook-owner-repo'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value=''):
        with patch.object(configure_webhook_handler_module, 'send_response'):
            result = configure_webhook_handler_module.lambda_handler(event, None)
            assert result['statusCode'] == 500


def test_lambda_handler_returns_500_when_delete_webhook_fails(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Delete',
        'ResourceProperties': {
            'WebhookId': '12345',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response',
        'PhysicalResourceId': 'github-webhook-owner-repo'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'delete_github_webhook', return_value={'success': False, 'error': 'API error'}):
            with patch.object(configure_webhook_handler_module, 'send_response'):
                result = configure_webhook_handler_module.lambda_handler(event, None)
                assert result['statusCode'] == 500


def test_lambda_handler_returns_400_for_unsupported_request_type(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Unknown',
        'ResourceProperties': {
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'send_response'):
        result = configure_webhook_handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 400


def test_lambda_handler_calls_send_response(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': True, 'webhook_id': 12345}):
                with patch.object(configure_webhook_handler_module, 'send_response') as mock_send:
                    configure_webhook_handler_module.lambda_handler(event, None)
                    assert mock_send.called


def test_lambda_handler_handles_update_request(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Update',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response',
        'PhysicalResourceId': 'github-webhook-owner-repo'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': True, 'webhook_id': 12345}):
                with patch.object(configure_webhook_handler_module, 'send_response'):
                    result = configure_webhook_handler_module.lambda_handler(event, None)
                    assert result['statusCode'] == 200


def test_lambda_handler_generates_physical_resource_id(configure_webhook_handler_module):
    from unittest.mock import patch

    event = {
        'RequestType': 'Create',
        'ResourceProperties': {
            'WebhookUrl': 'https://api.10ulabs.com/v1/runners',
            'Repository': 'owner/repo'
        },
        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test/guid',
        'RequestId': 'unique-request-id',
        'LogicalResourceId': 'MyResource',
        'ResponseURL': 'https://cloudformation.example.com/response'
    }

    with patch.object(configure_webhook_handler_module, 'get_github_pat', return_value='ghp_token'):
        with patch.object(configure_webhook_handler_module, 'get_or_create_webhook_secret', return_value='secret123'):
            with patch.object(configure_webhook_handler_module, 'create_github_webhook', return_value={'success': True, 'webhook_id': 12345}):
                with patch.object(configure_webhook_handler_module, 'send_response') as mock_send:
                    configure_webhook_handler_module.lambda_handler(event, None)
                    call_args = mock_send.call_args[0]
                    assert call_args[3] == 'github-webhook-owner-repo'
