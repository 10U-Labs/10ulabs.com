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
