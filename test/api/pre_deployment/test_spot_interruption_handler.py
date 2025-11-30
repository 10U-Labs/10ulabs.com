import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError


def test_get_ecs_client_returns_cached_client(spot_interruption_handler):
    mock_client = MagicMock()
    clients_dict = getattr(spot_interruption_handler, "_clients")
    clients_dict['ecs'] = mock_client
    result = spot_interruption_handler.get_ecs_client()
    assert result is mock_client


def test_get_ecs_client_creates_new_client_when_not_cached(spot_interruption_handler):
    clients_dict = getattr(spot_interruption_handler, "_clients")
    clients_dict.clear()
    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        result = spot_interruption_handler.get_ecs_client()
    assert result is mock_client


def test_get_ecs_task_tags_returns_tags_from_describe_tasks(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'RunnerType', 'value': 'fargate'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['RunId'] == '123'


def test_get_ecs_task_tags_returns_runner_type(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'RunnerType', 'value': 'fargate'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['RunnerType'] == 'fargate'


def test_get_ecs_task_tags_returns_github_repo(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'RunnerType', 'value': 'fargate'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['GitHubRepo'] == 'test/repo'


def test_get_ecs_task_tags_calls_describe_tasks_with_include_tags(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {'tasks': [{'tags': []}]}
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            get_ecs_task_tags('arn:aws:ecs:test:task/123')
            call_kwargs = mock_ecs.describe_tasks.call_args[1]
    assert call_kwargs['include'] == ['TAGS']


def test_get_ecs_task_tags_returns_empty_dict_on_client_error(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable'}},
                'DescribeTasks'
            )
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result == {}


def test_get_ecs_task_tags_returns_empty_dict_when_no_tasks(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {'tasks': []}
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result == {}


def test_get_ecs_task_tags_uses_ecs_cluster_env_var(spot_interruption_handler):
    with patch.dict(os.environ, {'ECS_CLUSTER': 'my-custom-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {'tasks': [{'tags': []}]}
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            get_ecs_task_tags('arn:aws:ecs:test:task/123')
            call_kwargs = mock_ecs.describe_tasks.call_args[1]
    assert call_kwargs['cluster'] == 'my-custom-cluster'


def test_handle_ecs_task_stopped_fetches_tags_from_api(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {}
        spot_interruption_handler.handle_ecs_task_stopped(event)
    assert mock_get_tags.called


def test_handle_ecs_task_stopped_passes_task_arn_to_get_tags(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/456',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {}
        spot_interruption_handler.handle_ecs_task_stopped(event)
        call_args = mock_get_tags.call_args[0]
    assert call_args[0] == 'arn:aws:ecs:test:task/456'


def test_handle_ecs_task_stopped_skips_when_no_run_id(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Spot interrupted'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {'RunnerType': 'fargate'}
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No run_id or runner_type'


def test_handle_ecs_task_stopped_skips_when_no_runner_type(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Spot interrupted'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {'RunId': '123'}
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No run_id or runner_type'


def test_handle_ecs_task_stopped_skips_non_spot_interruption(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'RunnerType': 'fargate',
            'GitHubRepo': 'test/repo'
        }
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'Not a spot interruption'


def test_handle_ecs_task_stopped_triggers_replacement_on_spot_interruption(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'RunnerType': 'fargate',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = 'test-token'
            with patch.object(spot_interruption_handler, 'get_workflow_run_status') as mock_get_status:
                mock_get_status.return_value = 'in_progress'
                with patch.object(spot_interruption_handler, 'trigger_runner_replacement') as mock_trigger:
                    mock_trigger.return_value = True
                    result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'Replacement runner triggered'


def test_handle_ecs_task_stopped_checks_workflow_status_before_replacement(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'RunnerType': 'fargate',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = 'test-token'
            with patch.object(spot_interruption_handler, 'get_workflow_run_status') as mock_get_status:
                mock_get_status.return_value = 'completed'
                result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert 'Workflow not active' in result['body']


def test_handle_ecs_task_stopped_fails_when_no_github_token(spot_interruption_handler):
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'RunnerType': 'fargate',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = ''
            result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No GitHub token'
