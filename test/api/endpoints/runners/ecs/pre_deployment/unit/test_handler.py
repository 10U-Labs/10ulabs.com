"""Unit tests for ECS runner Lambda handler."""
import json
import sys
import urllib.error
from datetime import datetime
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from repo_utils import REPO_ROOT
from .conftest import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    create_mock_client_factory,
    create_fargate_runner_env,
    create_mock_ssm_with_token,
    create_mock_ecs_with_run_task,
    create_mock_ecs_for_status,
)

# Add ECS lambda dir to path for importing split modules at runtime
ECS_LAMBDA_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "lambda"
if str(ECS_LAMBDA_DIR) not in sys.path:
    sys.path.insert(0, str(ECS_LAMBDA_DIR))


def test_lambda_handler_ecs_runner_post_with_missing_job_id_returns_400(
    ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post with missing job id returns 400."""
    event = ecs_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_lambda_handler_ecs_runner_post_with_missing_repo_returns_400(
    ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post with missing repo returns 400."""
    event = ecs_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def _create_ecr_mock_with_stable_image():
    """Create mock ECR client with stable image response."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{
            'imageTags': ['stable'],
            'imagePushedAt': datetime(2024, 1, 1),
            'imageDigest': 'sha256:test',
            'imageSizeInBytes': 1000
        }]
    }
    return mock_ecr


def _setup_post_handler_mocks(mock_boto_client):
    """Set up mocks for POST handler tests with ECR, ECS, SSM."""
    mock_ecr = _create_ecr_mock_with_stable_image()
    mock_ecs = create_mock_ecs_with_run_task('test-task')
    mock_ssm = create_mock_ssm_with_token()
    mock_boto_client.side_effect = create_mock_client_factory(
        ecs_mock=mock_ecs, ssm_mock=mock_ssm, ecr_mock=mock_ecr
    )
    return mock_ecs


@patch('boto3.client')
def test_lambda_handler_ecs_runner_post_returns_json_content_type(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post returns json content type."""
    _setup_post_handler_mocks(mock_boto_client)
    event = ecs_runner_post_event_factory(job_id=12345, github_repo='test-org/test-repo')
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


def _invoke_post_handler_and_get_run_task_kwargs(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Set up mocks, invoke POST handler, and return run_task call kwargs."""
    mock_ecs = _setup_post_handler_mocks(mock_boto_client)
    with patch('fargate_ops.get_runner_registration_token', return_value='test-token'):
        event = ecs_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        ecs_runner_handler.lambda_handler(event, lambda_context)
    return mock_ecs.run_task.call_args[1]


@patch('boto3.client')
def test_lambda_handler_ecs_runner_does_not_specify_launch_type_and_capacity_provider(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test handler does not specify launch type and capacity provider together."""
    call_kwargs = _invoke_post_handler_and_get_run_task_kwargs(
        mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
    )
    has_launch_type = 'launchType' in call_kwargs
    has_capacity_provider = 'capacityProviderStrategy' in call_kwargs
    assert not (has_launch_type and has_capacity_provider)


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_type(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test launch fargate runner tags use lowercase key for type."""
    call_kwargs = _invoke_post_handler_and_get_run_task_kwargs(
        mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
    )
    tags = call_kwargs.get('tags', [])
    type_tag = next((t for t in tags if t.get('key') == 'Type'), None)
    assert type_tag is not None


@patch('boto3.client')
def test_lambda_handler_ecs_runner_get_returns_json_content_type(
    mock_boto_client, ecs_runner_handler, lambda_context
):
    """Test lambda handler ecs runner get returns json content type."""
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {'taskArns': []}
    def mock_client(service_name):
        if service_name == 'ecs':
            return mock_ecs
        return MagicMock()
    mock_boto_client.side_effect = mock_client
    event = {'path': '/v1/runners/ecs', 'httpMethod': 'GET'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['headers']['Content-Type'].startswith('application/json')


def test_lambda_handler_ecs_runner_unsupported_method_returns_404(
    ecs_runner_handler, lambda_context
):
    """Test lambda handler ecs runner unsupported method returns 404."""
    event = {'path': '/v1/runners/ecs', 'httpMethod': 'DELETE'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 404


def _setup_ecs_status_mocks():
    """Set up common mocks for ECS status tests."""
    mock_ecs = create_mock_ecs_for_status()
    return patch('fargate_ops.get_ecs_client', return_value=mock_ecs)


def test_get_ecs_runner_status_returns_success_with_no_tasks(ecs_runner_handler):
    """Test get ecs runner status returns success with no tasks."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with _setup_ecs_status_mocks():
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['success'] is True


def test_get_ecs_runner_status_returns_zero_running_tasks_when_empty(ecs_runner_handler):
    """Test get ecs runner status returns zero running tasks when empty."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with _setup_ecs_status_mocks():
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['running_tasks'] == 0


def test_get_ecs_runner_status_returns_empty_task_list_when_no_tasks(ecs_runner_handler):
    """Test get ecs runner status returns empty task list when no tasks."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with _setup_ecs_status_mocks():
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['tasks'] == []


def test_get_ecs_runner_status_returns_cluster_name(ecs_runner_handler):
    """Test get ecs runner status returns cluster name."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with _setup_ecs_status_mocks():
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['cluster'] == 'test-cluster'


def test_get_ecs_runner_status_handles_client_error(ecs_runner_handler):
    """Test get ecs runner status handles client error."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        mock_ecs = MagicMock()
        mock_ecs.list_tasks.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'list_tasks'
        )
        with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['success'] is False


def test_handle_ecs_runner_get_returns_200_status(ecs_runner_handler, lambda_context):
    """Test handle ecs runner get returns 200 status."""
    event = {'path': '/v1/runners/ecs', 'httpMethod': 'GET'}
    with patch.object(ecs_runner_handler, 'get_ecs_runner_status') as mock_status:
        mock_status.return_value = {
            'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'
        }
        response = ecs_runner_handler.lambda_handler(event, lambda_context)
        assert response['statusCode'] == 200


@patch('boto3.client')
def test_get_latest_ecr_image_multiple_stable(mock_boto_client, ecs_runner_handler):
    """Test get laecr image multiple stable."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {
                'imageTags': ['stable'],
                'imagePushedAt': datetime(2024, 1, 1),
                'imageDigest': 'sha256:old',
                'imageSizeInBytes': 1024
            },
            {
                'imageTags': ['stable'],
                'imagePushedAt': datetime(2024, 1, 5),
                'imageDigest': 'sha256:new',
                'imageSizeInBytes': 2048
            }
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = ecs_runner_handler.get_latest_ecr_image()
        assert result['digest'] == 'sha256:new'


@patch('boto3.client')
def test_get_latest_ecr_image_no_stable(mock_boto_client, ecs_runner_handler):
    """Test get laecr image no stable."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {
                'imageTags': ['dev'],
                'imagePushedAt': datetime(2024, 1, 1),
                'imageDigest': 'sha256:dev',
                'imageSizeInBytes': 1024
            }
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = ecs_runner_handler.get_latest_ecr_image()
        assert result['success'] is False


def test_trigger_image_creation_success(ecs_runner_handler, mock_urllib_response_factory):
    """Test trigger image creation success."""
    with patch.dict('os.environ', {'API_FQDN': 'api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(json_data={'success': True})
            mock_urlopen.return_value = mock_response
            result = ecs_runner_handler.trigger_image_creation()
            assert result['success'] is True


def test_trigger_image_creation_url_error(ecs_runner_handler):
    """Test trigger image creation url error."""
    with patch.dict('os.environ', {'API_FQDN': 'api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
            result = ecs_runner_handler.trigger_image_creation()
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_no_github_token(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner no github token."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1)}]
    }
    mock_boto_client.return_value = mock_ecr
    env = {
        'ECR_REPOSITORY': 'test-repo',
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'CONTAINER_NAME': 'runner'
    }
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_github_token', return_value=''):
            result = ecs_runner_handler.launch_fargate_runner(123, ['test'], 'test/repo')
            assert result['success'] is False


def test_get_runner_registration_token_success(ecs_runner_handler, mock_urllib_response_factory):
    """Test get runner registration token success."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = mock_urllib_response_factory(json_data={'token': 'test-token'})
        mock_urlopen.return_value = mock_response
        result = ecs_runner_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == 'test-token'


def test_get_runner_registration_token_http_error(ecs_runner_handler):
    """Test get runner registration token http error."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)
        result = ecs_runner_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == ''


def _setup_fargate_runner_mocks(mock_boto_client, use_spot=None):
    """Set up common mocks for fargate runner tests."""
    mock_ecs = create_mock_ecs_with_run_task()
    mock_ssm = create_mock_ssm_with_token()
    mock_boto_client.side_effect = create_mock_client_factory(
        ecs_mock=mock_ecs, ssm_mock=mock_ssm
    )
    return mock_ecs, create_fargate_runner_env(use_spot=use_spot)


@patch('boto3.client')
def test_launch_fargate_runner_ecs_run_task_success(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner ecs run task success."""
    _, env = _setup_fargate_runner_mocks(mock_boto_client)
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_runner_registration_token', return_value='test-reg-token'):
            result = ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is True


def _get_capacity_provider_from_run_task(mock_boto_client, ecs_runner_handler, use_spot):
    """Launch runner and return capacity provider from run_task call."""
    mock_ecs, env = _setup_fargate_runner_mocks(mock_boto_client, use_spot=use_spot)
    with patch.dict('os.environ', env, clear=False):
        with patch('fargate_ops.get_runner_registration_token', return_value='test-reg-token'):
            ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
    return mock_ecs.run_task.call_args[1]['capacityProviderStrategy'][0]['capacityProvider']


@patch('boto3.client')
def test_launch_fargate_runner_uses_spot_when_configured(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner uses FARGATE_SPOT when USE_SPOT=true."""
    capacity_provider = _get_capacity_provider_from_run_task(
        mock_boto_client, ecs_runner_handler, use_spot=True
    )
    assert capacity_provider == 'FARGATE_SPOT'


@patch('boto3.client')
def test_launch_fargate_runner_uses_on_demand_when_configured(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner uses FARGATE when USE_SPOT=false."""
    capacity_provider = _get_capacity_provider_from_run_task(
        mock_boto_client, ecs_runner_handler, use_spot=False
    )
    assert capacity_provider == 'FARGATE'


def test_is_capacity_error_with_capacity_string(ecs_runner_handler):
    """Test is capacity error with capacity string."""
    result = {'success': False, 'error': 'No capacity in any availability zone'}
    assert ecs_runner_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_capacity_list(ecs_runner_handler):
    """Test is capacity error with capacity list."""
    result = {'success': False, 'error': [{'reason': 'Capacity is unavailable'}]}
    assert ecs_runner_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_non_capacity_error(ecs_runner_handler):
    """Test is capacity error with non capacity error."""
    result = {'success': False, 'error': 'Connection timeout'}
    assert ecs_runner_handler.is_capacity_error(result) is False


def test_lambda_handler_options_request_returns_200(ecs_runner_handler, lambda_context):
    """Test lambda handler options request returns 200."""
    event = {'path': '/v1/runners/ecs', 'httpMethod': 'OPTIONS'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_lambda_handler_options_request_returns_allow_origin_header(
    ecs_runner_handler, lambda_context
):
    """Test lambda handler options request returns allow origin header."""
    event = {'path': '/v1/runners/ecs', 'httpMethod': 'OPTIONS'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Origin' in headers


def test_is_test_mode_returns_false_by_default(ecs_runner_handler):
    """Test is mode returns false by default."""
    ecs_runner_handler.set_test_mode(False)
    result = ecs_runner_handler.is_test_mode()
    assert result is False


def test_is_test_mode_returns_true_when_enabled(ecs_runner_handler):
    """Test is mode returns true when enabled."""
    ecs_runner_handler.set_test_mode(True)
    result = ecs_runner_handler.is_test_mode()
    assert result is True


def test_get_header_case_insensitive_returns_empty_for_none_headers(ecs_runner_handler):
    """Test get header case insensitive returns empty for none headers."""
    result = ecs_runner_handler.get_header_case_insensitive(None, 'X-Test')
    assert result == ''


def test_get_header_case_insensitive_returns_value_for_exact_match(ecs_runner_handler):
    """Test get header case insensitive returns value for exact match."""
    headers = {'X-Test-Mode': 'true'}
    result = ecs_runner_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == 'true'


def test_lambda_handler_test_mode_returns_mock_for_ecs_runner_post(
    ecs_runner_handler, lambda_context
):
    """Test lambda handler mode returns mock for ecs runner post."""
    ecs_runner_handler.set_test_mode(False)
    event = {
        'path': '/v1/runners/ecs',
        'httpMethod': 'POST',
        'headers': {'x-test-mode': 'true'},
        'body': '{"job_id": 123, "github_repo": "test/repo"}'
    }
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['test_mode'] is True


def test_get_fargate_task_status_returns_status_from_describe_tasks(ecs_runner_handler):
    """Test get fargate task status returns status from describe tasks."""
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'lastStatus': 'RUNNING',
            'stoppedReason': '',
            'startedAt': '2024-01-01T00:00:00Z'
        }]
    }
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.get_fargate_task_status('test-cluster', task_arn)
        assert result['status'] == 'RUNNING'


def test_get_fargate_task_status_returns_unknown_on_empty_response(ecs_runner_handler):
    """Test get fargate task status returns unknown on empty response."""
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {'tasks': []}
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.get_fargate_task_status('test-cluster', task_arn)
        assert result['status'] == 'UNKNOWN'


def test_is_fargate_spot_interruption_returns_true_for_spot_interrupt_reason(ecs_runner_handler):
    """Test is fargate spot interruption returns true for spot interrupt reason."""
    task_status = {'stopped_reason': 'Your Spot Task was interrupted.'}
    assert ecs_runner_handler.is_fargate_spot_interruption(task_status) is True


def test_is_fargate_spot_interruption_returns_false_for_other_reasons(ecs_runner_handler):
    """Test is fargate spot interruption returns false for other reasons."""
    task_status = {'stopped_reason': 'Essential container exited'}
    assert ecs_runner_handler.is_fargate_spot_interruption(task_status) is False


def test_wait_for_fargate_task_provisioned_returns_success_when_running(ecs_runner_handler):
    """Test wait for fargate task provisioned returns success when running."""
    task_status = {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
    with patch('fargate_ops.get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is True


def test_wait_for_fargate_task_provisioned_not_spot_interrupted_when_running(ecs_runner_handler):
    """Test wait for fargate task provisioned is not spot interrupted when running."""
    task_status = {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
    with patch('fargate_ops.get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['spot_interrupted'] is False


def test_wait_for_fargate_task_provisioned_returns_failure_on_spot_interruption(ecs_runner_handler):
    """Test wait for fargate task provisioned returns failure on spot interruption."""
    task_status = {
        'status': 'STOPPED',
        'stopped_reason': 'Your Spot Task was interrupted.',
        'started_at': None
    }
    with patch('fargate_ops.get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is False


def test_wait_for_fargate_task_provisioned_sets_spot_interrupted_flag(ecs_runner_handler):
    """Test wait for fargate task provisioned sets spot interrupted flag."""
    task_status = {
        'status': 'STOPPED',
        'stopped_reason': 'Your Spot Task was interrupted.',
        'started_at': None
    }
    with patch('fargate_ops.get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['spot_interrupted'] is True


def _get_github_token_from_run_task(mock_ecs):
    """Extract GITHUB_TOKEN from run_task call args."""
    call_args = mock_ecs.run_task.call_args
    container_overrides = call_args[1]['overrides']['containerOverrides'][0]
    environment = container_overrides.get('environment', [])
    return next((e for e in environment if e['name'] == 'GITHUB_TOKEN'), None)


def _launch_runner_and_get_github_token_env(mock_boto_client, ecs_runner_handler, token_value):
    """Set up mocks, launch runner, and return GITHUB_TOKEN env var from run_task."""
    mock_ecs = create_mock_ecs_with_run_task()
    mock_ssm = create_mock_ssm_with_token(token_value)
    mock_boto_client.side_effect = create_mock_client_factory(
        ecs_mock=mock_ecs, ssm_mock=mock_ssm
    )
    env = create_fargate_runner_env()
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_runner_registration_token', return_value='test-reg-token'):
            ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
    return _get_github_token_from_run_task(mock_ecs)


@patch('boto3.client')
def test_launch_fargate_runner_includes_github_token_env_var(
    mock_boto_client, ecs_runner_handler
):
    """Test launch fargate runner includes GITHUB_TOKEN in container environment."""
    github_token_env = _launch_runner_and_get_github_token_env(
        mock_boto_client, ecs_runner_handler, 'github-token-value'
    )
    assert github_token_env is not None


@patch('boto3.client')
def test_launch_fargate_runner_passes_correct_github_token_value(
    mock_boto_client, ecs_runner_handler
):
    """Test launch fargate runner passes correct GITHUB_TOKEN value to container."""
    github_token_env = _launch_runner_and_get_github_token_env(
        mock_boto_client, ecs_runner_handler, 'github-token-value'
    )
    assert github_token_env['value'] == 'github-token-value'


@patch('boto3.client')
def test_launch_fargate_runner_does_not_pass_empty_github_token(
    mock_boto_client, ecs_runner_handler
):
    """Test launch fargate runner does not pass empty GITHUB_TOKEN to container."""
    mock_ecs = create_mock_ecs_with_run_task()
    mock_ssm = create_mock_ssm_with_token('')
    mock_boto_client.side_effect = create_mock_client_factory(
        ecs_mock=mock_ecs, ssm_mock=mock_ssm
    )
    env = create_fargate_runner_env()
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_runner_registration_token', return_value='test-reg-token'):
            result = ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is False


def test_get_latest_ecr_image_client_error(ecs_runner_handler):
    """Test get latest ecr image returns error on ClientError."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'RepositoryNotFoundException', 'Message': 'Not found'}},
        'describe_images'
    )
    with patch('fargate_ops.get_ecr_client', return_value=mock_ecr):
        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = ecs_runner_handler.get_latest_ecr_image()
            assert result['success'] is False


def test_get_latest_ecr_image_client_error_returns_error_message(ecs_runner_handler):
    """Test get latest ecr image returns error message on ClientError."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'describe_images'
    )
    with patch('fargate_ops.get_ecr_client', return_value=mock_ecr):
        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = ecs_runner_handler.get_latest_ecr_image()
            assert 'error' in result


def test_get_fargate_task_status_returns_unknown_on_client_error(ecs_runner_handler):
    """Test get fargate task status returns unknown on ClientError."""
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.side_effect = ClientError(
        {'Error': {'Code': 'ClusterNotFoundException', 'Message': 'Cluster not found'}},
        'describe_tasks'
    )
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.get_fargate_task_status('test-cluster', task_arn)
        assert result['status'] == 'UNKNOWN'


@patch('fargate_ops.time.sleep')
def test_wait_for_fargate_task_provisioned_waits_on_pending(mock_sleep, ecs_runner_handler):
    """Test wait for fargate task provisioned waits on PENDING status."""
    status_sequence = [
        {'status': 'PENDING', 'stopped_reason': '', 'started_at': None},
        {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
    ]
    with patch('fargate_ops.get_fargate_task_status', side_effect=status_sequence):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is True


@patch('fargate_ops.time.sleep')
def test_wait_for_fargate_task_provisioned_timeout_returns_success(mock_sleep, ecs_runner_handler):
    """Test wait for fargate task provisioned returns success after max poll attempts."""
    pending_status = {'status': 'PENDING', 'stopped_reason': '', 'started_at': None}
    with patch('fargate_ops.get_fargate_task_status', return_value=pending_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is True


def test_wait_for_fargate_task_provisioned_returns_on_unknown_status(ecs_runner_handler):
    """Test wait for fargate task provisioned returns early on UNKNOWN status."""
    unknown_status = {'status': 'DEPROVISIONING', 'stopped_reason': '', 'started_at': None}
    with patch('fargate_ops.get_fargate_task_status', return_value=unknown_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is False


def test_get_capacity_provider_uses_spot_from_labels(ecs_runner_handler):
    """Test _get_capacity_provider returns FARGATE_SPOT when labels specify spot."""
    import fargate_ops
    # Valid label set: platform=ecs, compute=fargate, arch=x86, pricing=spot, runner-id
    result = fargate_ops._get_capacity_provider(['ecs', 'fargate', 'x86', 'spot', 'runner-12345'])
    assert result == 'FARGATE_SPOT'


def test_get_capacity_provider_uses_on_demand_from_labels(ecs_runner_handler):
    """Test _get_capacity_provider returns FARGATE when labels don't specify spot."""
    import fargate_ops
    # Valid label set: platform=ecs, compute=fargate, arch=x86, pricing=on-demand, runner-id
    result = fargate_ops._get_capacity_provider(
        ['ecs', 'fargate', 'x86', 'on-demand', 'runner-12345']
    )
    assert result == 'FARGATE'


def test_get_ecs_runner_status_with_running_tasks(ecs_runner_handler):
    """Test get ecs runner status returns task details when tasks are running."""
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {
        'taskArns': ['arn:aws:ecs:us-east-1:123:task/cluster/task-id-1']
    }
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id-1',
            'lastStatus': 'RUNNING',
            'desiredStatus': 'RUNNING',
            'startedAt': datetime(2024, 1, 1),
            'cpu': '256',
            'memory': '512',
            'tags': [
                {'key': 'GitHubJobId', 'value': '12345'},
                {'key': 'JobLabels', 'value': 'test-label'},
                {'key': 'GitHubRepo', 'value': 'test/repo'}
            ]
        }]
    }
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['running_tasks'] == 1


def test_get_ecs_runner_status_includes_task_details(ecs_runner_handler):
    """Test get ecs runner status includes task metadata."""
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {
        'taskArns': ['arn:aws:ecs:us-east-1:123:task/cluster/task-id-1']
    }
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id-1',
            'lastStatus': 'RUNNING',
            'desiredStatus': 'RUNNING',
            'startedAt': datetime(2024, 1, 1),
            'cpu': '256',
            'memory': '512',
            'tags': [
                {'key': 'GitHubJobId', 'value': '12345'},
                {'key': 'JobLabels', 'value': 'test-label'},
                {'key': 'GitHubRepo', 'value': 'test/repo'}
            ]
        }]
    }
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['tasks'][0]['job_id'] == '12345'


def test_get_ecs_runner_status_extracts_task_id_from_arn(ecs_runner_handler):
    """Test get ecs runner status extracts task ID from ARN."""
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {
        'taskArns': ['arn:aws:ecs:us-east-1:123:task/cluster/task-id-123']
    }
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id-123',
            'lastStatus': 'RUNNING',
            'desiredStatus': 'RUNNING',
            'tags': []
        }]
    }
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['tasks'][0]['task_id'] == 'task-id-123'


@patch('boto3.client')
def test_launch_fargate_runner_dependency_validation_error(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner returns error on dependency validation failure."""
    env = create_fargate_runner_env()
    with patch.dict('os.environ', env):
        with patch('fargate_ops.ensure_dependencies_valid', side_effect=RuntimeError('Failed')):
            result = ecs_runner_handler.launch_fargate_runner(123, ['test'], 'test/repo')
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_dependency_validation_error_message(
    mock_boto_client, ecs_runner_handler
):
    """Test launch fargate runner includes dependency error message."""
    env = create_fargate_runner_env()
    with patch.dict('os.environ', env):
        with patch('fargate_ops.ensure_dependencies_valid', side_effect=RuntimeError('dep fail')):
            result = ecs_runner_handler.launch_fargate_runner(123, ['test'], 'test/repo')
            assert 'dep fail' in result.get('error', '')


@patch('boto3.client')
def test_launch_fargate_runner_reuses_existing_runner(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner reuses existing runner for workflow."""
    env = create_fargate_runner_env()
    mock_ssm = create_mock_ssm_with_token('test-token')
    mock_boto_client.side_effect = create_mock_client_factory(ssm_mock=mock_ssm)
    existing_runner = {'name': 'existing-runner', 'id': 123}
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_existing_runner_for_workflow', return_value=existing_runner):
            result = ecs_runner_handler.launch_fargate_runner(
                123, ['test'], 'test/repo', run_id=456
            )
            assert result['success'] is True


@patch('boto3.client')
def test_launch_fargate_runner_reused_flag_set(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner sets reused flag when runner exists."""
    env = create_fargate_runner_env()
    mock_ssm = create_mock_ssm_with_token('test-token')
    mock_boto_client.side_effect = create_mock_client_factory(ssm_mock=mock_ssm)
    existing_runner = {'name': 'existing-runner', 'id': 123}
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_existing_runner_for_workflow', return_value=existing_runner):
            result = ecs_runner_handler.launch_fargate_runner(
                123, ['test'], 'test/repo', run_id=456
            )
            assert result.get('reused') is True


@patch('boto3.client')
def test_launch_fargate_runner_returns_runner_name_on_reuse(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner returns runner name when reusing."""
    env = create_fargate_runner_env()
    mock_ssm = create_mock_ssm_with_token('test-token')
    mock_boto_client.side_effect = create_mock_client_factory(ssm_mock=mock_ssm)
    existing_runner = {'name': 'existing-runner-name', 'id': 123}
    with patch.dict('os.environ', env):
        with patch('fargate_ops.get_existing_runner_for_workflow', return_value=existing_runner):
            result = ecs_runner_handler.launch_fargate_runner(
                123, ['test'], 'test/repo', run_id=456
            )
            assert result.get('runner_name') == 'existing-runner-name'


def test_try_launch_in_subnet_handles_capacity_failure(ecs_runner_handler):
    """Test _try_launch_in_subnet handles capacity failure."""
    import fargate_ops
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {
        'tasks': [],
        'failures': [{'reason': 'Capacity not available'}]
    }
    env = create_fargate_runner_env()
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate',
                'github_token': 'gh-token'
            }
            result = fargate_ops._try_launch_in_subnet(cfg, 'subnet-1', 'test-cluster')
            assert result['retry'] is True


def test_try_launch_in_subnet_handles_non_capacity_failure(ecs_runner_handler):
    """Test _try_launch_in_subnet handles non-capacity failures."""
    import fargate_ops
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {
        'tasks': [],
        'failures': [{'reason': 'Some other error'}]
    }
    env = create_fargate_runner_env()
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate',
                'github_token': 'gh-token'
            }
            result = fargate_ops._try_launch_in_subnet(cfg, 'subnet-1', 'test-cluster')
            assert result['success'] is False


def test_try_launch_in_subnet_handles_spot_interruption(ecs_runner_handler):
    """Test _try_launch_in_subnet handles spot interruption."""
    import fargate_ops
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {
        'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123:task/test'}]
    }
    env = create_fargate_runner_env()
    interrupted_result = {'success': False, 'spot_interrupted': True, 'status': 'STOPPED'}
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', env):
            with patch('fargate_ops.wait_for_fargate_task_provisioned', return_value=interrupted_result):
                cfg = {
                    'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                    'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate',
                    'github_token': 'gh-token'
                }
                result = fargate_ops._try_launch_in_subnet(cfg, 'subnet-1', 'test-cluster')
                assert result['spot_interrupted'] is True


def test_try_launch_in_subnet_handles_client_error(ecs_runner_handler):
    """Test _try_launch_in_subnet handles ClientError."""
    import fargate_ops
    mock_ecs = MagicMock()
    mock_ecs.run_task.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test'}}, 'run_task'
    )
    env = create_fargate_runner_env()
    with patch('fargate_ops.get_ecs_client', return_value=mock_ecs):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate',
                'github_token': 'gh-token'
            }
            result = fargate_ops._try_launch_in_subnet(cfg, 'subnet-1', 'test-cluster')
            assert result['success'] is False


def test_try_launch_fargate_task_no_subnets_remaining(ecs_runner_handler):
    """Test _try_launch_fargate_task when no subnets remaining."""
    import fargate_ops
    env = create_fargate_runner_env()
    env['SUBNETS'] = 'subnet-1'
    interrupted_result = {'success': False, 'spot_interrupted': True, 'retry': True}
    with patch('fargate_ops._try_launch_in_subnet', return_value=interrupted_result):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate'
            }
            result = fargate_ops._try_launch_fargate_task(cfg)
            assert result['success'] is False


def test_try_launch_fargate_task_retries_on_spot_interruption(ecs_runner_handler):
    """Test _try_launch_fargate_task retries after spot interruption."""
    import fargate_ops
    env = create_fargate_runner_env()
    env['SUBNETS'] = 'subnet-1,subnet-2'
    call_count = [0]
    def mock_launch(cfg, subnet, cluster):
        call_count[0] += 1
        if call_count[0] == 1:
            return {'success': False, 'spot_interrupted': True, 'retry': True}
        return {'success': True, 'task_arn': 'arn:test'}
    with patch('fargate_ops._try_launch_in_subnet', side_effect=mock_launch):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate'
            }
            result = fargate_ops._try_launch_fargate_task(cfg)
            assert result['success'] is True


def test_try_launch_fargate_task_exhausts_retries(ecs_runner_handler):
    """Test _try_launch_fargate_task exhausts retries on repeated failures."""
    import fargate_ops
    env = create_fargate_runner_env()
    env['SUBNETS'] = 'subnet-1,subnet-2,subnet-3'
    retry_result = {'success': False, 'retry': True, 'error': 'Capacity unavailable'}
    with patch('fargate_ops._try_launch_in_subnet', return_value=retry_result):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate'
            }
            result = fargate_ops._try_launch_fargate_task(cfg)
            assert result['success'] is False


def test_handle_sqs_event_processes_records(ecs_runner_handler, lambda_context):
    """Test _handle_sqs_event processes SQS records."""
    event = {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'msg-1',
            'body': json.dumps({
                'job_id': 123,
                'job_labels': ['test'],
                'github_repo': 'test/repo'
            })
        }]
    }
    with patch.object(ecs_runner_handler, 'get_latest_ecr_image') as mock_ecr:
        mock_ecr.return_value = {'success': True}
        with patch.object(ecs_runner_handler, 'launch_fargate_runner') as mock_launch:
            mock_launch.return_value = {'success': True, 'task_arn': 'arn:test'}
            response = ecs_runner_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 200


def test_handle_sqs_event_missing_fields(ecs_runner_handler, lambda_context):
    """Test _handle_sqs_event handles missing required fields."""
    event = {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'msg-1',
            'body': json.dumps({'job_id': 123})  # Missing github_repo
        }]
    }
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    body = json.loads(response['body'])
    assert body['results'][0]['error'] == 'Missing required fields'


def test_handle_sqs_event_no_stable_image(ecs_runner_handler, lambda_context):
    """Test _handle_sqs_event handles no stable image."""
    event = {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'msg-1',
            'body': json.dumps({
                'job_id': 123,
                'job_labels': ['test'],
                'github_repo': 'test/repo'
            })
        }]
    }
    with patch.object(ecs_runner_handler, 'get_latest_ecr_image') as mock_ecr:
        mock_ecr.return_value = {'success': False}
        with patch.object(ecs_runner_handler, 'trigger_image_creation') as mock_trigger:
            mock_trigger.return_value = {'success': True}
            response = ecs_runner_handler.lambda_handler(event, lambda_context)
            body = json.loads(response['body'])
            assert body['results'][0]['error'] == 'No stable image available'


def test_handle_sqs_event_json_decode_error(ecs_runner_handler, lambda_context):
    """Test _handle_sqs_event handles JSON decode error."""
    event = {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'msg-1',
            'body': 'invalid json'
        }]
    }
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    body = json.loads(response['body'])
    assert 'error' in body['results'][0]


@patch('boto3.client')
def test_handle_ecs_runner_post_no_stable_image_triggers_build(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test handle_ecs_runner_post triggers image build when no stable image."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {'imageDetails': []}  # No stable image
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo', 'API_FQDN': 'api.test.com'}):
        with patch('fargate_ops.trigger_image_creation') as mock_trigger:
            mock_trigger.return_value = {'success': True}
            event = ecs_runner_post_event_factory(job_id=123, github_repo='test/repo')
            response = ecs_runner_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 202


@patch('boto3.client')
def test_handle_ecs_runner_post_returns_500_on_launch_failure(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test handle_ecs_runner_post returns 500 on launch failure."""
    mock_ecr = _create_ecr_mock_with_stable_image()
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        with patch.object(ecs_runner_handler, 'launch_fargate_runner') as mock_launch:
            mock_launch.return_value = {'success': False, 'error': 'Failed'}
            event = ecs_runner_post_event_factory(job_id=123, github_repo='test/repo')
            response = ecs_runner_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 500


def test_handle_ecs_runner_post_value_error(ecs_runner_handler, lambda_context):
    """Test handle_ecs_runner_post handles ValueError."""
    event = {
        'path': '/v1/runners/ecs',
        'httpMethod': 'POST',
        'body': '{"job_id": "not_an_int"}'  # Will cause issues downstream
    }
    with patch.object(ecs_runner_handler, 'parse_body', side_effect=ValueError('bad value')):
        response = ecs_runner_handler.lambda_handler(event, lambda_context)
        assert response['statusCode'] == 500


def test_get_header_case_insensitive_returns_empty_for_none_value(ecs_runner_handler):
    """Test get header case insensitive returns empty for None header value."""
    headers = {'X-Test-Mode': None}
    result = ecs_runner_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == ''


def test_get_header_case_insensitive_returns_empty_for_missing_header(ecs_runner_handler):
    """Test get header case insensitive returns empty when header not found."""
    headers = {'X-Other-Header': 'value'}
    result = ecs_runner_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == ''


def test_try_launch_fargate_task_logs_retry_on_spot_interruption(ecs_runner_handler):
    """Test _try_launch_fargate_task logs retry info after spot interruption."""
    import fargate_ops
    env = create_fargate_runner_env()
    env['SUBNETS'] = 'subnet-1,subnet-2'
    call_count = [0]
    def mock_launch(cfg, subnet, cluster):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call - spot interruption
            return {'success': False, 'spot_interrupted': True, 'retry': True}
        # Second call - also fails to test the break in retry loop
        return {'success': False, 'retry': False, 'error': 'Some error'}
    with patch('fargate_ops._try_launch_in_subnet', side_effect=mock_launch):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate'
            }
            result = fargate_ops._try_launch_fargate_task(cfg)
            assert result['success'] is False


def test_try_launch_fargate_task_returns_error_on_non_retryable_failure(ecs_runner_handler):
    """Test _try_launch_fargate_task returns error immediately on non-retryable failure."""
    import fargate_ops
    env = create_fargate_runner_env()
    env['SUBNETS'] = 'subnet-1,subnet-2'
    failure_result = {'success': False, 'retry': False, 'error': 'Permission denied'}
    with patch('fargate_ops._try_launch_in_subnet', return_value=failure_result):
        with patch.dict('os.environ', env):
            cfg = {
                'job_id': 123, 'job_labels': ['test'], 'github_repo': 'test/repo',
                'registration_token': 'token', 'run_id': None, 'runner_type': 'fargate'
            }
            result = fargate_ops._try_launch_fargate_task(cfg)
            assert result['error'] == 'Permission denied'
