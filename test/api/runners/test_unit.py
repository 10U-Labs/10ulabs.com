import json
import sys
from pathlib import Path
import importlib.util
from unittest.mock import Mock, patch, MagicMock
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_config_file_exists_in_correct_location():
    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "config.json"
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


def test_runners_stack_creates_lambda_function():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "stack.py"
    spec = importlib.util.spec_from_file_location("runners_stack", stack_path)
    runners_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runners_module)
    RunnersStack = runners_module.RunnersStack

    with patch('aws_cdk.Fn.import_value') as mock_import:
        mock_import.side_effect = lambda x: f"mock-{x}"

        stack = RunnersStack(
            app,
            "TestRunnersStack",
            config=config,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )

        template = Template.from_stack(stack)

        resources = template.find_resources("AWS::Lambda::Function")
        assert len(resources) == 1


def test_runners_stack_creates_api_gateway_resource():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "stack.py"
    spec = importlib.util.spec_from_file_location("runners_stack", stack_path)
    runners_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runners_module)
    RunnersStack = runners_module.RunnersStack

    with patch('aws_cdk.Fn.import_value') as mock_import:
        mock_import.side_effect = lambda x: f"mock-{x}"

        stack = RunnersStack(
            app,
            "TestRunnersStack",
            config=config,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )

        template = Template.from_stack(stack)

        resources = template.find_resources("AWS::ApiGateway::Resource")
        assert len(resources) == 1


def test_runners_stack_creates_api_gateway_method():
    app = cdk.App()

    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    stack_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "stack.py"
    spec = importlib.util.spec_from_file_location("runners_stack", stack_path)
    runners_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runners_module)
    RunnersStack = runners_module.RunnersStack

    with patch('aws_cdk.Fn.import_value') as mock_import:
        mock_import.side_effect = lambda x: f"mock-{x}"

        stack = RunnersStack(
            app,
            "TestRunnersStack",
            config=config,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )

        template = Template.from_stack(stack)

        resources = template.find_resources("AWS::ApiGateway::Method")
        assert len(resources) == 1


def test_webhook_router_handler_file_exists():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    assert handler_path.exists()


def test_webhook_router_has_lambda_handler_function():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)
    assert hasattr(webhook_router_module, 'lambda_handler')


def test_webhook_router_has_verify_signature_function():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)
    assert hasattr(webhook_router_module, 'verify_signature')


def test_webhook_router_has_handle_workflow_job_function():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)
    assert hasattr(webhook_router_module, 'handle_workflow_job')


def test_webhook_router_has_route_runner_request_function():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)
    assert hasattr(webhook_router_module, 'route_runner_request')


def test_verify_signature_validates_correct_signature():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

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


def test_verify_signature_rejects_incorrect_signature():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

    payload = "test payload"
    secret = "test_secret"
    wrong_signature = "sha256=wrong_signature"

    result = webhook_router_module.verify_signature(payload, wrong_signature, secret)
    assert result is False


def test_handle_workflow_job_ignores_non_queued_actions():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

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


def test_handle_workflow_job_ignores_jobs_without_runner_labels():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

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


def test_route_runner_request_identifies_ec2_runner():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

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
        assert result['runner_type'] == 'ec2'


def test_route_runner_request_identifies_fargate_runner():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

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
        assert result['runner_type'] == 'fargate'


def test_route_runner_request_returns_error_for_unknown_runner_type():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "webhook_router.py"
    spec = importlib.util.spec_from_file_location("webhook_router", handler_path)
    webhook_router_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webhook_router_module)

    result = webhook_router_module.route_runner_request(
        job_id=789,
        job_labels=['unknown-runner-type'],
        github_repo='test/repo'
    )

    assert result['success'] is False
