"""Unit tests for ECS runner Lambda handler."""
import json
import urllib.error
from datetime import datetime
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from .conftest import parse_response_body, assert_response_status, assert_json_content_type


def test_lambda_handler_ecs_runner_post_with_missing_job_id_returns_400(
    ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post with missing job id returns 400."""
    event = ecs_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_ecs_runner_post_with_missing_repo_returns_400(
    ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post with missing repo returns 400."""
    event = ecs_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_ecs_runner_post_returns_json_content_type(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test lambda handler ecs runner post returns json content type."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': '2024-01-01'}]
    }
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-task'}]}
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        if service_name == 'ecs':
            return mock_ecs
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()
    mock_boto_client.side_effect = mock_client
    event = ecs_runner_post_event_factory(job_id=12345, github_repo='test-org/test-repo')
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_ecs_runner_does_not_specify_launch_type_and_capacity_provider(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test handler does not specify launch type and capacity provider together."""
    mock_ecr = MagicMock()
    image_detail = {
        'imageTags': ['stable'],
        'imagePushedAt': datetime(2024, 1, 1),
        'imageDigest': 'sha256:test',
        'imageSizeInBytes': 1000
    }
    mock_ecr.describe_images.return_value = {'imageDetails': [image_detail]}
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-task'}]}
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        if service_name == 'ecs':
            return mock_ecs
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()
    mock_boto_client.side_effect = mock_client
    with patch.object(
        ecs_runner_handler, 'get_runner_registration_token', return_value='test-token'
    ):
        event = ecs_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        ecs_runner_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    has_launch_type = 'launchType' in call_kwargs
    has_capacity_provider = 'capacityProviderStrategy' in call_kwargs
    assert not (has_launch_type and has_capacity_provider)


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_type(
    mock_boto_client, ecs_runner_handler, ecs_runner_post_event_factory, lambda_context
):
    """Test launch fargate runner tags use lowercase key for type."""
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{
            'imageTags': ['stable'],
            'imagePushedAt': datetime(2024, 1, 1),
            'imageDigest': 'sha256:test',
            'imageSizeInBytes': 1000
        }]
    }
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-task'}]}
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    def mock_client(service_name):
        if service_name == 'ecr':
            return mock_ecr
        if service_name == 'ecs':
            return mock_ecs
        if service_name == 'ssm':
            return mock_ssm
        return MagicMock()
    mock_boto_client.side_effect = mock_client
    with patch.object(
        ecs_runner_handler, 'get_runner_registration_token', return_value='test-token'
    ):
        event = ecs_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        ecs_runner_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
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
    event = {'path': '/v1/ecs-runner', 'httpMethod': 'GET'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_ecs_runner_unsupported_method_returns_404(
    ecs_runner_handler, lambda_context
):
    """Test lambda handler ecs runner unsupported method returns 404."""
    event = {'path': '/v1/ecs-runner', 'httpMethod': 'DELETE'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_get_ecs_runner_status_returns_success_with_no_tasks(ecs_runner_handler):
    """Test get ecs runner status returns success with no tasks."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(ecs_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['success'] is True


def test_get_ecs_runner_status_returns_zero_running_tasks_when_empty(ecs_runner_handler):
    """Test get ecs runner status returns zero running tasks when empty."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(ecs_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['running_tasks'] == 0


def test_get_ecs_runner_status_returns_empty_task_list_when_no_tasks(ecs_runner_handler):
    """Test get ecs runner status returns empty task list when no tasks."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(ecs_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['tasks'] == []


def test_get_ecs_runner_status_returns_cluster_name(ecs_runner_handler):
    """Test get ecs runner status returns cluster name."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(ecs_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['cluster'] == 'test-cluster'


def test_get_ecs_runner_status_handles_client_error(ecs_runner_handler):
    """Test get ecs runner status handles client error."""
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(ecs_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.side_effect = ClientError(
                {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
                'list_tasks'
            )
            mock_get_client.return_value = mock_ecs
            result = ecs_runner_handler.get_ecs_runner_status()
            assert result['success'] is False


def test_handle_ecs_runner_get_returns_200_status(ecs_runner_handler, lambda_context):
    """Test handle ecs runner get returns 200 status."""
    event = {'path': '/v1/ecs-runner', 'httpMethod': 'GET'}
    with patch.object(ecs_runner_handler, 'get_ecs_runner_status') as mock_status:
        mock_status.return_value = {
            'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'
        }
        response = ecs_runner_handler.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)


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
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(json_data={'success': True})
            mock_urlopen.return_value = mock_response
            result = ecs_runner_handler.trigger_image_creation()
            assert result['success'] is True


def test_trigger_image_creation_url_error(ecs_runner_handler):
    """Test trigger image creation url error."""
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
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
        with patch.object(ecs_runner_handler, 'get_github_token', return_value=''):
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


@patch('boto3.client')
def test_launch_fargate_runner_ecs_run_task_success(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner ecs run task success."""
    env = {
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'CONTAINER_NAME': 'test-container',
        'GITHUB_TOKEN_SECRET_NAME': '/test/token'
    }
    with patch.dict('os.environ', env):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        task_arn = 'arn:aws:ecs:us-east-1:123456789012:task/test'
        mock_ecs.run_task.return_value = {'tasks': [{'taskArn': task_arn}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        reg_token_patch = patch.object(
            ecs_runner_handler, 'get_runner_registration_token', return_value='test-reg-token'
        )
        with reg_token_patch:
            result = ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is True


@patch('boto3.client')
def test_launch_fargate_runner_uses_spot_when_configured(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner uses FARGATE_SPOT when USE_SPOT=true."""
    env = {
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'CONTAINER_NAME': 'test-container',
        'GITHUB_TOKEN_SECRET_NAME': '/test/token',
        'USE_SPOT': 'true'
    }
    with patch.dict('os.environ', env, clear=False):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-arn'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        reg_token_patch = patch.object(
            ecs_runner_handler, 'get_runner_registration_token', return_value='test-reg-token'
        )
        with reg_token_patch:
            ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            call_args = mock_ecs.run_task.call_args
            assert call_args[1]['capacityProviderStrategy'][0]['capacityProvider'] == 'FARGATE_SPOT'


@patch('boto3.client')
def test_launch_fargate_runner_uses_on_demand_when_configured(mock_boto_client, ecs_runner_handler):
    """Test launch fargate runner uses FARGATE when USE_SPOT=false."""
    env = {
        'ECS_CLUSTER': 'test-cluster',
        'TASK_DEFINITION': 'test-task',
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'CONTAINER_NAME': 'test-container',
        'GITHUB_TOKEN_SECRET_NAME': '/test/token',
        'USE_SPOT': 'false'
    }
    with patch.dict('os.environ', env, clear=False):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'test-arn'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        reg_token_patch = patch.object(
            ecs_runner_handler, 'get_runner_registration_token', return_value='test-reg-token'
        )
        with reg_token_patch:
            ecs_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            call_args = mock_ecs.run_task.call_args
            assert call_args[1]['capacityProviderStrategy'][0]['capacityProvider'] == 'FARGATE'


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
    event = {'path': '/v1/ecs-runner', 'httpMethod': 'OPTIONS'}
    response = ecs_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_options_request_returns_allow_origin_header(
    ecs_runner_handler, lambda_context
):
    """Test lambda handler options request returns allow origin header."""
    event = {'path': '/v1/ecs-runner', 'httpMethod': 'OPTIONS'}
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
        'path': '/v1/ecs-runner',
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
    with patch.object(ecs_runner_handler, 'get_ecs_client', return_value=mock_ecs):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.get_fargate_task_status('test-cluster', task_arn)
        assert result['status'] == 'RUNNING'


def test_get_fargate_task_status_returns_unknown_on_empty_response(ecs_runner_handler):
    """Test get fargate task status returns unknown on empty response."""
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {'tasks': []}
    with patch.object(ecs_runner_handler, 'get_ecs_client', return_value=mock_ecs):
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
    with patch.object(ecs_runner_handler, 'get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['success'] is True


def test_wait_for_fargate_task_provisioned_not_spot_interrupted_when_running(ecs_runner_handler):
    """Test wait for fargate task provisioned is not spot interrupted when running."""
    task_status = {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
    with patch.object(ecs_runner_handler, 'get_fargate_task_status', return_value=task_status):
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
    with patch.object(ecs_runner_handler, 'get_fargate_task_status', return_value=task_status):
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
    with patch.object(ecs_runner_handler, 'get_fargate_task_status', return_value=task_status):
        task_arn = 'arn:aws:ecs:us-east-1:123:task/test'
        result = ecs_runner_handler.wait_for_fargate_task_provisioned('test-cluster', task_arn)
        assert result['spot_interrupted'] is True


def test_store_workflow_runner_stores_state_field(ecs_runner_handler):
    """Test store workflow runner stores state field."""
    mock_dynamodb = MagicMock()
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        with patch.object(ecs_runner_handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            runner = ecs_runner_handler.WorkflowRunner(
                run_id=123, runner_type='fargate', resource_id='arn:task',
                runner_name='runner-123', github_repo='test/repo', state='requested'
            )
            ecs_runner_handler.store_workflow_runner(runner)
            call_args = mock_dynamodb.put_item.call_args[1]
            item = call_args['Item']
            assert item['state']['S'] == 'requested'


def test_store_workflow_runner_defaults_state_to_requested(ecs_runner_handler):
    """Test store workflow runner defaults state to requested."""
    mock_dynamodb = MagicMock()
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        with patch.object(ecs_runner_handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            runner = ecs_runner_handler.WorkflowRunner(
                run_id=123, runner_type='fargate', resource_id='arn:task',
                runner_name='runner-123', github_repo='test/repo'
            )
            ecs_runner_handler.store_workflow_runner(runner)
            call_args = mock_dynamodb.put_item.call_args[1]
            item = call_args['Item']
            assert item['state']['S'] == 'requested'


def test_store_workflow_runner_returns_false_when_table_not_set(ecs_runner_handler):
    """Test store workflow runner returns false when table not set."""
    with patch.dict('os.environ', {}, clear=True):
        runner = ecs_runner_handler.WorkflowRunner(
            run_id=123, runner_type='fargate', resource_id='arn:task',
            runner_name='runner-123', github_repo='test/repo'
        )
        result = ecs_runner_handler.store_workflow_runner(runner)
        assert result is False


def test_store_workflow_runner_returns_false_when_run_id_not_provided(ecs_runner_handler):
    """Test store workflow runner returns false when run id not provided."""
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        runner = ecs_runner_handler.WorkflowRunner(
            run_id=None, runner_type='fargate', resource_id='arn:task',
            runner_name='runner-123', github_repo='test/repo'
        )
        result = ecs_runner_handler.store_workflow_runner(runner)
        assert result is False


def test_store_workflow_runner_returns_true_on_success(ecs_runner_handler):
    """Test store workflow runner returns true on success."""
    mock_dynamodb = MagicMock()
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        with patch.object(ecs_runner_handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            runner = ecs_runner_handler.WorkflowRunner(
                run_id=123, runner_type='fargate', resource_id='arn:task',
                runner_name='runner-123', github_repo='test/repo'
            )
            result = ecs_runner_handler.store_workflow_runner(runner)
            assert result is True


def test_store_workflow_runner_returns_false_on_client_error(ecs_runner_handler):
    """Test store workflow runner returns false on client error."""
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'put_item'
    )
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        with patch.object(ecs_runner_handler, 'get_dynamodb_client', return_value=mock_dynamodb):
            runner = ecs_runner_handler.WorkflowRunner(
                run_id=123, runner_type='fargate', resource_id='arn:task',
                runner_name='runner-123', github_repo='test/repo'
            )
            result = ecs_runner_handler.store_workflow_runner(runner)
            assert result is False
