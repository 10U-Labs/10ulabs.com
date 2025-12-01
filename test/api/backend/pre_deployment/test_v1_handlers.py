import json
import os
import urllib.error
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock

from botocore.exceptions import ClientError

from .conftest import parse_response_body, assert_response_status, assert_json_content_type, create_multi_client_mock


def test_lambda_handler_docker_runner_post_with_missing_job_id_returns_400(v1_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['job_id']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_docker_runner_post_with_missing_repo_returns_400(v1_handler, docker_runner_post_event_factory, lambda_context):
    event = docker_runner_post_event_factory()
    body = parse_response_body({'body': event['body']})
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@patch('boto3.client')
def test_lambda_handler_docker_runner_post_returns_json_content_type(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


@patch('boto3.client')
def test_lambda_handler_docker_runner_does_not_specify_launch_type_and_capacity_provider(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        v1_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    has_launch_type = 'launchType' in call_kwargs
    has_capacity_provider = 'capacityProviderStrategy' in call_kwargs
    assert not (has_launch_type and has_capacity_provider)


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_type(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        v1_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    tags = call_kwargs.get('tags', [])
    type_tag = next((t for t in tags if t.get('key') == 'Type'), None)
    assert type_tag is not None


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_managed_by(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        v1_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    tags = call_kwargs.get('tags', [])
    managed_by_tag = next((t for t in tags if t.get('key') == 'ManagedBy'), None)
    assert managed_by_tag is not None


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_job_id(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        v1_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    tags = call_kwargs.get('tags', [])
    job_id_tag = next((t for t in tags if t.get('key') == 'GitHubJobId'), None)
    assert job_id_tag is not None


@patch('boto3.client')
def test_launch_fargate_runner_tags_use_lowercase_key_for_repo(mock_boto_client, v1_handler, docker_runner_post_event_factory, lambda_context):
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
    with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-registration-token'):
        event = docker_runner_post_event_factory(job_id=12346, github_repo='test-org/test-repo')
        v1_handler.lambda_handler(event, lambda_context)
    call_kwargs = mock_ecs.run_task.call_args[1]
    tags = call_kwargs.get('tags', [])
    repo_tag = next((t for t in tags if t.get('key') == 'GitHubRepo'), None)
    assert repo_tag is not None


@patch('boto3.client')
def test_lambda_handler_docker_runner_get_returns_json_content_type(mock_boto_client, v1_handler, lambda_context):
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.return_value = {'taskArns': []}

    def mock_client(service_name):
        if service_name == 'ecs':
            return mock_ecs
        return MagicMock()

    mock_boto_client.side_effect = mock_client
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_docker_runner_unsupported_method_returns_404(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'DELETE'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_get_docker_runner_status_returns_success_with_no_tasks(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['success'] is True


def test_get_docker_runner_status_returns_zero_running_tasks_when_empty(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['running_tasks'] == 0


def test_get_docker_runner_status_returns_empty_task_list_when_no_tasks(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['tasks'] == []


def test_get_docker_runner_status_returns_cluster_name(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.return_value = {'taskArns': []}
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['cluster'] == 'test-cluster'


def test_get_docker_runner_status_handles_client_error(v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(v1_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.list_tasks.side_effect = ClientError(
                {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
                'list_tasks'
            )
            mock_get_client.return_value = mock_ecs

            result = v1_handler.get_docker_runner_status()

            assert result['success'] is False


def test_handle_docker_runner_get_returns_200_status(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_docker_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_response_status(response, 200)


def test_handle_docker_runner_get_returns_json_content_type(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_docker_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}
        response = v1_handler.lambda_handler(event, lambda_context)

        assert_json_content_type(response)


def test_trigger_github_workflow_success(v1_handler, mock_urllib_response_factory):
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_REPO': 'test/repo'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(status=204)
            mock_urlopen.return_value = mock_response
            result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
            assert result['success'] is True


def test_trigger_github_workflow_missing_token(v1_handler):
    with patch.dict('os.environ', {'GITHUB_REPO': 'test/repo'}, clear=True):
        result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
        assert result['success'] is False


def test_trigger_github_workflow_http_204_response(v1_handler, mock_urllib_response_factory):
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_REPO': 'test/repo'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(status=204)
            mock_urlopen.return_value = mock_response
            result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
            assert 'workflow triggered via GitHub Actions' in result['message']


def test_trigger_github_workflow_unexpected_status(v1_handler, mock_urllib_response_factory):
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_REPO': 'test/repo'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(status=500)
            mock_urlopen.return_value = mock_response
            result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
            assert result['success'] is False


def test_trigger_github_workflow_url_error(v1_handler):
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_REPO': 'test/repo'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
            result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
            assert result['success'] is False


def test_trigger_github_workflow_http_error(v1_handler):
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_REPO': 'test/repo'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)
            result = v1_handler.trigger_github_workflow('test.yml', {'ref': 'main'})
            assert result['success'] is False


def test_handle_post_request_success(v1_handler):
    event = {'body': '{"test": "data"}'}
    def handler_func(body):
        return {'success': True, 'data': body}
    result = v1_handler.handle_post_request(event, handler_func)
    assert result['statusCode'] == 200


def test_handle_post_request_value_error(v1_handler):
    event = {'body': '{"test": "data"}'}
    def handler_func(body):
        raise ValueError('Test error')
    result = v1_handler.handle_post_request(event, handler_func)
    assert result['statusCode'] == 500


@patch('boto3.client')
def test_get_latest_ecr_image_multiple_stable(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:old', 'imageSizeInBytes': 1024},
            {'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 5), 'imageDigest': 'sha256:new', 'imageSizeInBytes': 2048}
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = v1_handler.get_latest_ecr_image()
        assert result['digest'] == 'sha256:new'


@patch('boto3.client')
def test_get_latest_ecr_image_no_stable(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {'imageTags': ['dev'], 'imagePushedAt': datetime(2024, 1, 1), 'imageDigest': 'sha256:dev', 'imageSizeInBytes': 1024}
        ]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
        result = v1_handler.get_latest_ecr_image()
        assert result['success'] is False


@patch('boto3.client')
def test_get_github_token_cached(_mock_boto_client, v1_handler):
    with patch.dict(v1_handler.__dict__['_github_token_cache'], {'value': 'cached-token'}):
        result = v1_handler.get_github_token()
        assert result == 'cached-token'


@patch('boto3.client')
def test_get_github_token_ssm_retrieval(mock_boto_client, v1_handler):
    with patch.dict(v1_handler.__dict__['_github_token_cache'], {'value': None}):
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'new-token'}}
        mock_boto_client.return_value = mock_ssm
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/github/token'}):
            result = v1_handler.get_github_token()
            assert result == 'new-token'


@patch('boto3.client')
def test_get_github_token_ssm_error(mock_boto_client, v1_handler):
    with patch.dict(v1_handler.__dict__['_github_token_cache'], {'value': None}):
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError({'Error': {'Code': 'TestError'}}, 'GetParameter')
        mock_boto_client.return_value = mock_ssm
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/github/token'}):
            result = v1_handler.get_github_token()
            assert result == ''


def test_trigger_image_creation_success(v1_handler, mock_urllib_response_factory):
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urllib_response_factory(json_data={'success': True})
            mock_urlopen.return_value = mock_response
            result = v1_handler.trigger_image_creation()
            assert result['success'] is True


def test_trigger_image_creation_url_error(v1_handler):
    with patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'}):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
            result = v1_handler.trigger_image_creation()
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_no_github_token(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1)}]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo', 'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'runner'}):
        with patch.object(v1_handler, 'get_github_token', return_value=''):
            result = v1_handler.launch_fargate_runner(123, ['test'], 'test/repo')
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_failed_registration(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [{'imageTags': ['stable'], 'imagePushedAt': datetime(2024, 1, 1)}]
    }
    mock_boto_client.return_value = mock_ecr
    with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo', 'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'runner'}):
        with patch.object(v1_handler, 'get_github_token', return_value='token'):
            with patch.object(v1_handler, 'get_runner_registration_token', return_value=''):
                result = v1_handler.launch_fargate_runner(123, ['test'], 'test/repo')
                assert result['success'] is False


def test_get_runner_registration_token_success(v1_handler, mock_urllib_response_factory):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = mock_urllib_response_factory(json_data={'token': 'test-token'})
        mock_urlopen.return_value = mock_response
        result = v1_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == 'test-token'


def test_get_runner_registration_token_http_error(v1_handler):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)
        result = v1_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == ''


def test_get_runner_registration_token_url_error(v1_handler):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
        result = v1_handler.get_runner_registration_token('github-token', 'test/repo')
        assert result == ''


@patch('boto3.client')
def test_launch_fargate_runner_ecs_run_task_success(mock_boto_client, v1_handler):
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
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            result = v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is True


@patch('boto3.client')
def test_launch_fargate_runner_uses_fargate_spot(mock_boto_client, v1_handler):
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
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            call_args = mock_ecs.run_task.call_args
            assert call_args[1]['capacityProviderStrategy'][0]['capacityProvider'] == 'FARGATE_SPOT'


@patch('boto3.client')
def test_launch_fargate_runner_includes_tags(mock_boto_client, v1_handler):
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
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            v1_handler.launch_fargate_runner(456, ['fargate-label'], 'owner/repository')
            call_args = mock_ecs.run_task.call_args
            tags = call_args[1]['tags']
            tag_dict = {tag['key']: tag['value'] for tag in tags}
            assert tag_dict['GitHubJobId'] == '456'


@patch('boto3.client')
def test_launch_fargate_runner_enables_ecs_managed_tags(mock_boto_client, v1_handler):
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
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            v1_handler.launch_fargate_runner(789, ['test-label'], 'test/repo')
            call_args = mock_ecs.run_task.call_args
            assert call_args[1]['enableECSManagedTags'] is True


@patch('boto3.client')
def test_launch_fargate_runner_ecs_failure_no_tasks(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecs.run_task.return_value = {'tasks': [], 'failures': [{'reason': 'Resource limit exceeded'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            result = v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is False


@patch('boto3.client')
def test_launch_fargate_runner_retries_on_capacity_error(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1,subnet-2,subnet-3', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        capacity_failure = {'tasks': [], 'failures': [{'reason': 'Capacity is unavailable at this time'}]}
        success_response = {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id'}], 'failures': []}
        mock_ecs.run_task.side_effect = [capacity_failure, capacity_failure, success_response]
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            result = v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
            assert result['success'] is True
            assert mock_ecs.run_task.call_count == 3


def test_is_capacity_error_with_capacity_string(v1_handler):
    result = {'success': False, 'error': 'No capacity in any availability zone'}
    assert v1_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_capacity_list(v1_handler):
    result = {'success': False, 'error': [{'reason': 'Capacity is unavailable'}]}
    assert v1_handler.is_capacity_error(result) is True


def test_is_capacity_error_with_non_capacity_error(v1_handler):
    result = {'success': False, 'error': 'Connection timeout'}
    assert v1_handler.is_capacity_error(result) is False


@patch('boto3.client')
def test_handle_docker_runner_post_returns_503_on_capacity_error(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token', 'ECR_REPOSITORY': 'test-repo'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ecr = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecr.describe_images.return_value = {'imageDetails': [{'imageDigest': 'sha256:abc', 'imageTags': ['stable'], 'imagePushedAt': MagicMock(isoformat=lambda: '2024-01-01'), 'imageSizeInBytes': 100}]}
        mock_ecs.run_task.return_value = {'tasks': [], 'failures': [{'reason': 'Capacity is unavailable at this time'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            if service == 'ecr':
                return mock_ecr
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            event = {'httpMethod': 'POST', 'path': '/v1/docker-runner', 'body': '{"job_id": 123, "job_labels": ["test"], "github_repo": "test/repo"}'}
            response = v1_handler.lambda_handler(event, None)
            assert response['statusCode'] == 503


@patch('boto3.client')
def test_handle_docker_runner_post_returns_500_on_non_capacity_error(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token', 'ECR_REPOSITORY': 'test-repo'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ecr = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        mock_ecr.describe_images.return_value = {'imageDetails': [{'imageDigest': 'sha256:abc', 'imageTags': ['stable'], 'imagePushedAt': MagicMock(isoformat=lambda: '2024-01-01'), 'imageSizeInBytes': 100}]}
        mock_ecs.run_task.return_value = {'tasks': [], 'failures': [{'reason': 'Resource limit exceeded'}]}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            if service == 'ecr':
                return mock_ecr
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            event = {'httpMethod': 'POST', 'path': '/v1/docker-runner', 'body': '{"job_id": 123, "job_labels": ["test"], "github_repo": "test/repo"}'}
            response = v1_handler.lambda_handler(event, None)
            assert response['statusCode'] == 500


@patch('boto3.client')
def test_get_docker_runner_status_with_tasks(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        mock_ecs = MagicMock()
        mock_ecs.list_tasks.return_value = {'taskArns': ['arn1']}
        mock_ecs.describe_tasks.return_value = {
            'tasks': [{
                'taskArn': 'arn1',
                'lastStatus': 'RUNNING',
                'desiredStatus': 'RUNNING',
                'startedAt': datetime(2024, 1, 1),
                'cpu': '1024',
                'memory': '2048',
                'tags': [
                    {'key': 'GitHubJobId', 'value': '123'},
                    {'key': 'JobLabels', 'value': 'test'},
                    {'key': 'GitHubRepo', 'value': 'test/repo'}
                ]
            }]
        }
        mock_boto_client.return_value = mock_ecs
        result = v1_handler.get_docker_runner_status()
        assert result['running_tasks'] == 1


@patch('boto3.client')
def test_get_docker_runner_status_extracts_metadata(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        mock_ecs = MagicMock()
        mock_ecs.list_tasks.return_value = {'taskArns': ['arn1']}
        mock_ecs.describe_tasks.return_value = {
            'tasks': [{
                'taskArn': 'arn1',
                'lastStatus': 'RUNNING',
                'desiredStatus': 'RUNNING',
                'cpu': '1024',
                'memory': '2048',
                'tags': [{'key': 'GitHubJobId', 'value': '456'}]
            }]
        }
        mock_boto_client.return_value = mock_ecs
        result = v1_handler.get_docker_runner_status()
        assert result['tasks'][0]['job_id'] == '456'


def test_lambda_handler_routes_to_docker_runner_get(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET'}
    with patch.object(v1_handler, 'get_docker_runner_status', return_value={'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}):
        response = v1_handler.lambda_handler(event, lambda_context)
        assert response['statusCode'] == 200


def test_lambda_handler_unknown_route_returns_404(v1_handler, lambda_context):
    event = {'path': '/v1/unknown', 'httpMethod': 'GET'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 404


@patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'})
@patch('boto3.client')
def test_v1_get_github_token_failure(mock_boto_client, v1_handler):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError({'Error': {'Code': 'ParameterNotFound', 'Message': 'Not found'}}, 'GetParameter')
    mock_boto_client.return_value = mock_ssm
    token = v1_handler.get_github_token()
    assert token == ''


@patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'})
@patch('boto3.client')
def test_v1_get_github_token_success_returns_token(mock_boto_client, v1_handler):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    mock_boto_client.return_value = mock_ssm
    token1 = v1_handler.get_github_token()
    assert token1 == 'test-token'


@patch('boto3.client')
def test_v1_get_github_token_success_caches_value(mock_boto_client, v1_handler):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
    mock_boto_client.return_value = mock_ssm
    v1_handler.get_github_token()
    v1_handler.get_github_token()
    assert mock_ssm.get_parameter.call_count == 1


@patch('urllib.request.urlopen')
def test_v1_get_runner_registration_token_failure(mock_urlopen, v1_handler):
    mock_urlopen.side_effect = urllib.error.HTTPError('https://test.com', 500, 'Internal Server Error', {}, None)
    token = v1_handler.get_runner_registration_token('test-token', 'test/repo')
    assert token == ''


@patch('urllib.request.urlopen')
def test_v1_get_runner_registration_token_invalid_json(mock_urlopen, v1_handler):
    mock_response = MagicMock()
    mock_response.read.return_value = b'invalid json'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response
    token = v1_handler.get_runner_registration_token('test-token', 'test/repo')
    assert token == ''


@patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'})
def test_v1_trigger_image_creation_http_error(v1_handler):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('https://test.com', 500, 'Error', {}, None)
        result = v1_handler.trigger_image_creation()
        assert result['success'] is False


@patch.dict('os.environ', {'IMAGE_API_ENDPOINT': 'https://api.test.com'})
def test_v1_trigger_image_creation_url_error(v1_handler):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError('Connection failed')
        result = v1_handler.trigger_image_creation()
        assert result['success'] is False


@patch('boto3.client')
@patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'})
def test_v1_get_latest_ecr_image_no_stable_images(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.return_value = {
        'imageDetails': [
            {'imageTags': ['latest'], 'imageDigest': 'sha256:abc', 'imagePushedAt': datetime(2024, 1, 1), 'imageSizeInBytes': 1000}
        ]
    }
    mock_boto_client.return_value = mock_ecr
    result = v1_handler.get_latest_ecr_image()
    assert result['success'] is False


@patch('boto3.client')
@patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'})
def test_v1_get_latest_ecr_image_ecr_error(mock_boto_client, v1_handler):
    mock_ecr = MagicMock()
    mock_ecr.describe_images.side_effect = ClientError({'Error': {'Code': 'RepositoryNotFoundException', 'Message': 'Not found'}}, 'DescribeImages')
    mock_boto_client.return_value = mock_ecr
    result = v1_handler.get_latest_ecr_image()
    assert result['success'] is False


@patch('boto3.client')
@patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'})
def test_v1_get_docker_runner_status_ecs_error(mock_boto_client, v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.list_tasks.side_effect = ClientError({'Error': {'Code': 'ClusterNotFoundException', 'Message': 'Not found'}}, 'ListTasks')
    mock_boto_client.return_value = mock_ecs
    result = v1_handler.get_docker_runner_status()
    assert result['success'] is False


@patch('boto3.client')
@patch.dict('os.environ', {'ECS_CLUSTER': 'test', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'})
def test_v1_launch_fargate_runner_ecs_error(mock_boto_client, v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.run_task.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable', 'Message': 'Error'}}, 'RunTask')
    mock_boto_client.return_value = mock_ecs
    with patch.object(v1_handler, 'get_github_token', return_value='test-token'):
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'):
            result = v1_handler.launch_fargate_runner(123, ['label'], 'test/repo')
            assert result['success'] is False


@patch('boto3.client')
@patch.dict('os.environ', {'ECS_CLUSTER': 'test', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'})
def test_v1_launch_fargate_runner_no_tasks_in_response(mock_boto_client, v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.run_task.return_value = {'tasks': [], 'failures': [{'reason': 'RESOURCE:CPU', 'arn': 'arn:task'}]}
    mock_boto_client.return_value = mock_ecs
    with patch.object(v1_handler, 'get_github_token', return_value='test-token'):
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'):
            result = v1_handler.launch_fargate_runner(123, ['label'], 'test/repo')
            assert result['success'] is False


def test_lambda_handler_options_request_returns_200(v1_handler, lambda_context):
    event = {'path': '/v1/echo', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_options_request_returns_allow_origin_header(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Origin' in headers


def test_lambda_handler_options_request_returns_allow_methods_header(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Methods' in headers


def test_lambda_handler_options_request_returns_allow_headers_header(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert 'Access-Control-Allow-Headers' in headers


def test_lambda_handler_options_request_allows_wildcard_origin(v1_handler, lambda_context):
    event = {'path': '/v1/ec2-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    assert headers['Access-Control-Allow-Origin'] == '*'


def test_lambda_handler_options_request_allows_get_method(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'GET' in allowed_methods


def test_lambda_handler_options_request_allows_post_method(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'POST' in allowed_methods


def test_lambda_handler_options_request_allows_options_method(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_methods = headers['Access-Control-Allow-Methods']
    assert 'OPTIONS' in allowed_methods


def test_is_test_mode_returns_false_by_default(v1_handler):
    v1_handler.set_test_mode(False)
    result = v1_handler.is_test_mode()
    assert result is False


def test_is_test_mode_returns_true_when_enabled(v1_handler):
    v1_handler.set_test_mode(True)
    result = v1_handler.is_test_mode()
    assert result is True


def test_set_test_mode_enables_test_mode(v1_handler):
    v1_handler.set_test_mode(False)
    v1_handler.set_test_mode(True)
    assert v1_handler.is_test_mode() is True


def test_set_test_mode_disables_test_mode(v1_handler):
    v1_handler.set_test_mode(True)
    v1_handler.set_test_mode(False)
    assert v1_handler.is_test_mode() is False


def test_get_header_case_insensitive_returns_empty_for_none_headers(v1_handler):
    result = v1_handler.get_header_case_insensitive(None, 'X-Test')
    assert result == ''


def test_get_header_case_insensitive_returns_empty_for_empty_headers(v1_handler):
    result = v1_handler.get_header_case_insensitive({}, 'X-Test')
    assert result == ''


def test_get_header_case_insensitive_returns_value_for_exact_match(v1_handler):
    headers = {'X-Test-Mode': 'true'}
    result = v1_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == 'true'


def test_get_header_case_insensitive_returns_value_for_lowercase_match(v1_handler):
    headers = {'x-test-mode': 'true'}
    result = v1_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == 'true'


def test_get_header_case_insensitive_returns_value_for_uppercase_match(v1_handler):
    headers = {'X-TEST-MODE': 'true'}
    result = v1_handler.get_header_case_insensitive(headers, 'x-test-mode')
    assert result == 'true'


def test_get_header_case_insensitive_returns_empty_for_missing_header(v1_handler):
    headers = {'X-Other': 'value'}
    result = v1_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == ''


def test_get_header_case_insensitive_returns_empty_for_none_value(v1_handler):
    headers = {'X-Test-Mode': None}
    result = v1_handler.get_header_case_insensitive(headers, 'X-Test-Mode')
    assert result == ''


def test_lambda_handler_detects_test_mode_header(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/echo', 'httpMethod': 'POST', 'headers': {'x-test-mode': 'true'}, 'body': '{}'}
    v1_handler.lambda_handler(event, lambda_context)
    assert v1_handler.is_test_mode() is True


def test_lambda_handler_test_mode_not_enabled_without_header(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/echo', 'httpMethod': 'POST', 'headers': {}, 'body': '{}'}
    v1_handler.lambda_handler(event, lambda_context)
    assert v1_handler.is_test_mode() is False


def test_lambda_handler_test_mode_returns_mock_for_docker_runner_post(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/docker-runner', 'httpMethod': 'POST', 'headers': {'x-test-mode': 'true'}, 'body': '{"job_id": 123, "github_repo": "test/repo"}'}
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['test_mode'] is True


def test_lambda_handler_test_mode_returns_mock_task_arn_for_docker(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/docker-runner', 'httpMethod': 'POST', 'headers': {'x-test-mode': 'true'}, 'body': '{"job_id": 123, "github_repo": "test/repo"}'}
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['task_arn'] == 'arn:aws:ecs:test-mode-mock'


def test_lambda_handler_test_mode_does_not_affect_get_requests(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/docker-runner', 'httpMethod': 'GET', 'headers': {'x-test-mode': 'true'}}
    with patch.object(v1_handler, 'get_docker_runner_status', return_value={'success': True, 'running_tasks': 0, 'tasks': [], 'cluster': 'test'}):
        response = v1_handler.lambda_handler(event, lambda_context)
        body = parse_response_body(response)
        assert 'test_mode' not in body


def test_lambda_handler_test_mode_returns_success_true(v1_handler, lambda_context):
    v1_handler.set_test_mode(False)
    event = {'path': '/v1/docker-runner', 'httpMethod': 'POST', 'headers': {'x-test-mode': 'true'}, 'body': '{"job_id": 123, "github_repo": "test/repo"}'}
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['success'] is True


def test_lambda_handler_options_allows_x_test_mode_header(v1_handler, lambda_context):
    event = {'path': '/v1/docker-runner', 'httpMethod': 'OPTIONS'}
    response = v1_handler.lambda_handler(event, lambda_context)
    headers = response.get('headers', {})
    allowed_headers = headers['Access-Control-Allow-Headers']
    assert 'x-test-mode' in allowed_headers


def test_get_fargate_task_status_returns_status_from_describe_tasks(v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'lastStatus': 'RUNNING',
            'stoppedReason': '',
            'startedAt': '2024-01-01T00:00:00Z'
        }]
    }
    with patch.object(v1_handler, 'get_ecs_client', return_value=mock_ecs):
        result = v1_handler.get_fargate_task_status('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['status'] == 'RUNNING'


def test_get_fargate_task_status_returns_unknown_on_empty_response(v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {'tasks': []}
    with patch.object(v1_handler, 'get_ecs_client', return_value=mock_ecs):
        result = v1_handler.get_fargate_task_status('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['status'] == 'UNKNOWN'


def test_get_fargate_task_status_returns_unknown_on_client_error(v1_handler):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.side_effect = ClientError({'Error': {'Code': 'TestError'}}, 'DescribeTasks')
    with patch.object(v1_handler, 'get_ecs_client', return_value=mock_ecs):
        result = v1_handler.get_fargate_task_status('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['status'] == 'UNKNOWN'


def test_is_fargate_spot_interruption_returns_true_for_spot_interrupt_reason(v1_handler):
    task_status = {'stopped_reason': 'Your Spot Task was interrupted.'}
    assert v1_handler.is_fargate_spot_interruption(task_status) is True


def test_is_fargate_spot_interruption_returns_false_for_other_reasons(v1_handler):
    task_status = {'stopped_reason': 'Essential container exited'}
    assert v1_handler.is_fargate_spot_interruption(task_status) is False


def test_is_fargate_spot_interruption_returns_false_for_empty_reason(v1_handler):
    task_status = {'stopped_reason': ''}
    assert v1_handler.is_fargate_spot_interruption(task_status) is False


def test_wait_for_fargate_task_provisioned_returns_success_when_running(v1_handler):
    with patch.object(v1_handler, 'get_fargate_task_status', return_value={'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}):
        result = v1_handler.wait_for_fargate_task_provisioned('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['success'] is True
        assert result['spot_interrupted'] is False


def test_wait_for_fargate_task_provisioned_detects_spot_interruption(v1_handler):
    with patch.object(v1_handler, 'get_fargate_task_status', return_value={'status': 'STOPPED', 'stopped_reason': 'Your Spot Task was interrupted.', 'started_at': None}):
        result = v1_handler.wait_for_fargate_task_provisioned('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['success'] is False
        assert result['spot_interrupted'] is True


def test_wait_for_fargate_task_provisioned_returns_failure_for_non_spot_stop(v1_handler):
    with patch.object(v1_handler, 'get_fargate_task_status', return_value={'status': 'STOPPED', 'stopped_reason': 'Essential container exited', 'started_at': None}):
        result = v1_handler.wait_for_fargate_task_provisioned('test-cluster', 'arn:aws:ecs:us-east-1:123:task/test')
        assert result['success'] is False
        assert result['spot_interrupted'] is False


@patch('boto3.client')
def test_launch_fargate_runner_retries_on_spot_interruption(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1,subnet-2', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        success_response = {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id'}], 'failures': []}
        mock_ecs.run_task.return_value = success_response
        spot_interrupted_status = {'status': 'STOPPED', 'stopped_reason': 'Your Spot Task was interrupted.', 'started_at': None}
        running_status = {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            with patch.object(v1_handler, 'get_fargate_task_status', side_effect=[spot_interrupted_status, running_status]):
                result = v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
                assert result['success'] is True
                assert mock_ecs.run_task.call_count == 2


@patch('boto3.client')
def test_launch_fargate_runner_excludes_subnet_after_spot_interruption(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1,subnet-2', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        success_response = {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id'}], 'failures': []}
        mock_ecs.run_task.return_value = success_response
        spot_interrupted_status = {'status': 'STOPPED', 'stopped_reason': 'Your Spot Task was interrupted.', 'started_at': None}
        running_status = {'status': 'RUNNING', 'stopped_reason': '', 'started_at': '2024-01-01'}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            with patch.object(v1_handler, 'get_fargate_task_status', side_effect=[spot_interrupted_status, running_status]):
                v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
                run_task_calls = mock_ecs.run_task.call_args_list
                first_subnet = run_task_calls[0][1]['networkConfiguration']['awsvpcConfiguration']['subnets'][0]
                second_subnet = run_task_calls[1][1]['networkConfiguration']['awsvpcConfiguration']['subnets'][0]
                assert first_subnet != second_subnet


@patch('boto3.client')
def test_launch_fargate_runner_fails_after_max_retries(mock_boto_client, v1_handler):
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'TASK_DEFINITION': 'test-task', 'SUBNETS': 'subnet-1,subnet-2,subnet-3', 'SECURITY_GROUPS': 'sg-1', 'CONTAINER_NAME': 'test-container', 'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        mock_ecs = MagicMock()
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}
        success_response = {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:123:task/cluster/task-id'}], 'failures': []}
        mock_ecs.run_task.return_value = success_response
        spot_interrupted_status = {'status': 'STOPPED', 'stopped_reason': 'Your Spot Task was interrupted.', 'started_at': None}
        def mock_client(service):
            if service == 'ecs':
                return mock_ecs
            if service == 'ssm':
                return mock_ssm
            return MagicMock()
        mock_boto_client.side_effect = mock_client
        with patch.object(v1_handler, 'get_runner_registration_token', return_value='test-reg-token'):
            with patch.object(v1_handler, 'get_fargate_task_status', return_value=spot_interrupted_status):
                result = v1_handler.launch_fargate_runner(123, ['test-label'], 'test/repo')
                assert result['success'] is False
