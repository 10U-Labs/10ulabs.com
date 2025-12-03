import json
import urllib.error
from datetime import datetime
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from .conftest import parse_response_body, assert_response_status, assert_json_content_type


def test_lambda_handler_docker_runner_post_with_missing_job_id_returns_400(docker_runner_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_docker_runner_post_with_missing_repo_returns_400(docker_runner_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_docker_runner_post_returns_json_content_type(mock_boto_client, docker_runner_handler, docker_runner_post_event_factory, lambda_context):
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
    event = docker_runner_post_event_factory(job_id=12345, github_repo='test-org/test-repo')
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_docker_runner_does_not_specify_launch_type_and_capacity_provider(mock_boto_client, docker_runner_handler, docker_runner_post_event_factory, lambda_context):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:test', 'imageSizeInBytes': 1000}]
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
    with patch.object(docker_runner_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        docker_runner_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    has_launch_type = 'launchType' in call_kwargs
    has_capacity_provider = 'capacityProviderStrategy' in call_kwargs
    assert not (has_launch_type and has_capacity_provider)


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_type(mock_boto_client, docker_runner_handler, docker_runner_post_event_factory, lambda_context):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:test', 'imageSizeInBytes': 1000}]
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
    with patch.object(docker_runner_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        docker_runner_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    tags = call_kwargs.get('tags', [])
    type_tag = next((t for t in tags if t.get('key') == 'Type'), None)
    assert type_tag is not None


@patch('boto3.client')
def test_lambda_handler_docker_runner_get_returns_json_content_type(mock_boto_client, docker_runner_handler, lambda_context):
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {'taskArns': []}
    def mock_client(service_name):
        if service_name == 'ecs':
            return mock_ecs
        return MagicMock()
    mock_boto_client.side_effect = mock_client
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_docker_runner_unsupported_method_returns_404(docker_runner_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'DELETE'}
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_get_docker_runner_status_returns_success_with_no_tasks(docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(docker_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = docker_runner_handler.get_docker_runner_status()
            assert result['success'] is True


def test_get_docker_runner_status_returns_zero_running_tasks_when_empty(docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(docker_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = docker_runner_handler.get_docker_runner_status()
            assert result['running_tasks'] == 0


def test_get_docker_runner_status_returns_empty_task_list_when_no_tasks(docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(docker_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = docker_runner_handler.get_docker_runner_status()
            assert result['tasks'] == []


def test_get_docker_runner_status_returns_cluster_name(docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(docker_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs
            result = docker_runner_handler.get_docker_runner_status()
            assert result['cluster'] == 'test-cluster'


def test_get_docker_runner_status_handles_client_error(docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(docker_runner_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.side_effect = ClientError(
                {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
                'list_tasks'
            )
            mock_get_client.return_value = mock_ecs
            result = docker_runner_handler.get_docker_runner_status()
            assert result['success'] is False


def test_handle_docker_runner_get_returns_200_status(docker_runner_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(docker_runner_handler, 'get_docker_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}
        response = docker_runner_handler.lambda_handler(event, lambda_context)
        assert_response_status(response, 200)


@patch('boto3.client')
def test_get_latest_ecr_image_multiple_stable(mock_boto_client, docker_runner_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:old', 'imageSizeInBytes': 1024},
            {'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 5), 'imageDigest': 'sha256:new', 'imageSizeInBytes': 2048}
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = docker_runner_handler.get_latest_ecr_image()
        assert result['digest'] == 'sha256:new'


@patch('boto3.client')
def test_get_latest_ecr_image_no_stable(mock_boto_client, docker_runner_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {'imageTags': ['dev'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:dev', 'imageSizeInBytes': 1024}
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = docker_runner_handler.get_latest_ecr_image()
        assert result['success'] is False


def test_trigger_image_creation_success(docker_runner_handler, mock_urllib_response_factory):
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(json_data={'success': True})
            mock_urlopen.return_value = mock_response
            result = docker_runner_handler.trigger_image_creation()
            assert result['success'] is True


def test_trigger_image_creation_url_error(docker_runner_handler):
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
            result = docker_runner_handler.trigger_image_creation()
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_no_github_token(mock_boto_client, docker_runner_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1)}]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo', 'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'runner'}):
        with patch.object(docker_runner_handler, 'get_github_token', return_value=''):
            result = docker_runner_handler.launch_fargate_runner(123, ['test'], 'test/repo')
            assert result['success'] is False


def test_get_runner_registration_token_success(docker_runner_handler, mock_urllib_response_factory):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = mock_urllib_response_factory(json_data={'token': 'test-token'})
        mock_urlopen.return_value = mock_response
        result = docker_runner_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == 'test-token'


def test_get_runner_registration_token_http_error(docker_runner_handler):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)
        result = docker_runner_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == ''


@patch('boto3.client')
def test_launch_fargate_runner_ecs_run_task_success(mock_boto_client, docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecs.run_task.return_value = {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123456789012:task/test'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(docker_runner_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            result = docker_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is True


@patch('boto3.client')
def test_launch_fargate_runner_uses_fargate(mock_boto_client, docker_runner_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
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
        with patch.object(docker_runner_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            docker_runner_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            call_args = mock_ecs.run_task.call_args
            assert call_args[1]['capacityProviderStrategy'][0]['capacityProvider'] == 'FARGATE'


def test_is_capacity_error_with_capacity_string(docker_runner_handler):
    result = {'success': False, 'error': 'No capacity in any availability zone'}
    assert docker_runner_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_capacity_list(docker_runner_handler):
    result = {'success': False, 'error': [{'reason': 'Capacity is unavailable'}]}
    assert docker_runner_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_non_capacity_error(docker_runner_handler):
    result = {'success': False, 'error': 'Connection timeout'}
    assert docker_runner_handler.is_capacity_error(result) is False


def test_lambda_handler_options_request_returns_200(docker_runner_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_options_request_returns_allow_origin_header(docker_runner_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Origin' in headers


def test_is_test_mode_returns_false_by_default(docker_runner_handler):
    docker_runner_handler.set_test_mode(False)
    result = docker_runner_handler.is_test_mode()
    assert result is False


def test_is_test_mode_returns_true_when_enabled(docker_runner_handler):
    docker_runner_handler.set_test_mode(True)
    result = docker_runner_handler.is_test_mode()
    assert result is True


def test_get_header_case_insensitive_returns_empty_for_none_headers(docker_runner_handler):
    result = docker_runner_handler.get_header_case_insensitive(None, 'X-Test')
    assert result == ''


def test_get_header_case_insensitive_returns_value_for_exact_match(docker_runner_handler):
    headers = {'X-Test-Mode': 'true'}
    result = docker_runner_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == 'true'


def test_lambda_handler_test_mode_returns_mock_for_docker_runner_post(docker_runner_handler, lambda_context):
    docker_runner_handler.set_test_mode(False)
    event = {'path': '/v1/docker-runner', 'httpMethod': 'POST', 'headers': {'x-test-mode': 'true'}, 'body': '{"job_id": 123, "github_repo": "test/repo"}'}
    response = docker_runner_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['test_mode'] is True


def test_get_fargate_task_status_returns_status_from_describe_tasks(docker_runner_handler):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'lastStatus': 'RUNNING',
            'stoppedReason': '',
            'startedAt': '2024-01-01T00:00:00Z'
        }]
    }
    with patch.object(docker_runner_handler, 'get_ecs_client', return_value=mock_ecs):
        result = docker_runner_handler.get_fargate_task_status('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['status'] == 'RUNNING'


def test_get_fargate_task_status_returns_unknown_on_empty_response(docker_runner_handler):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {'tasks': []}
    with patch.object(docker_runner_handler, 'get_ecs_client', return_value=mock_ecs):
        result = docker_runner_handler.get_fargate_task_status('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['status'] == 'UNKNOWN'


def test_is_fargate_spot_interruption_returns_true_for_spot_interrupt_reason(docker_runner_handler):
    task_status = {'stopped_reason': 'Your Spot Task was interrupted.'}
    assert docker_runner_handler.is_fargate_spot_interruption(task_status) is True


def test_is_fargate_spot_interruption_returns_false_for_other_reasons(docker_runner_handler):
    task_status = {'stopped_reason': 'Essential container exited'}
    assert docker_runner_handler.is_fargate_spot_interruption(task_status) is False


def test_wait_for_fargate_task_provisioned_returns_success_when_running(docker_runner_handler):
    with patch.object(docker_runner_handler, 'get_fargate_task_status', return_value={'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}):
        result = docker_runner_handler.wait_for_fargate_task_provisioned('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['success'] is True
        assert result['spot_interrupted'] is False


def test_wait_for_fargate_task_provisioned_detects_spot_interruption(docker_runner_handler):
    with patch.object(docker_runner_handler, 'get_fargate_task_status', return_value={'status': 'STOPPED', 'stopped_reason': 'Your Spot Task was interrupted.', 'started_at': None}):
        result = docker_runner_handler.wait_for_fargate_task_provisioned('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['success'] is False
        assert result['spot_interrupted'] is True
