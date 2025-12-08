"""Unit tests for test spot interruption handler."""
import os
import urllib.error
from unittest.mock import patch, MagicMock, Mock
from botocore.exceptions import ClientError


def test_get_ecs_client_returns_cached_client(spot_interruption_handler):
    """Test get ecs client returns cached client."""
    mock_client = MagicMock()
    clients_dict = getattr(spot_interruption_handler, "_clients")
    clients_dict['ecs'] = mock_client
    result = spot_interruption_handler.get_ecs_client()
    assert result is mock_client


def test_get_ecs_client_creates_new_client_when_not_cached(spot_interruption_handler):
    """Test get ecs client creates new client when not cached."""
    clients_dict = getattr(spot_interruption_handler, "_clients")
    clients_dict.clear()
    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        result = spot_interruption_handler.get_ecs_client()
    assert result is mock_client


def test_get_ecs_task_tags_returns_tags_from_describe_tasks(spot_interruption_handler):
    """Test get ecs task tags returns tags from describe tasks."""
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'GitHubJobId', 'value': '456'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['RunId'] == '123'


def test_get_ecs_task_tags_returns_job_id(spot_interruption_handler):
    """Test get ecs task tags returns job id."""
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'GitHubJobId', 'value': '456'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['GitHubJobId'] == '456'


def test_get_ecs_task_tags_returns_github_repo(spot_interruption_handler):
    """Test get ecs task tags returns github repo."""
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {
                'tasks': [{
                    'tags': [
                        {'key': 'RunId', 'value': '123'},
                        {'key': 'GitHubJobId', 'value': '456'},
                        {'key': 'GitHubRepo', 'value': 'test/repo'}
                    ]
                }]
            }
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result['GitHubRepo'] == 'test/repo'


def test_get_ecs_task_tags_calls_describe_tasks_with_include_tags(spot_interruption_handler):
    """Test get ecs task tags calls describe tasks with include tags."""
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
    """Test get ecs task tags returns empty dict on client error."""
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
    """Test get ecs task tags returns empty dict when no tasks."""
    with patch.dict(os.environ, {'ECS_CLUSTER': 'test-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {'tasks': []}
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            result = get_ecs_task_tags('arn:aws:ecs:test:task/123')
    assert result == {}


def test_get_ecs_task_tags_uses_ecs_cluster_env_var(spot_interruption_handler):
    """Test get ecs task tags uses ecs cluster env var."""
    with patch.dict(os.environ, {'ECS_CLUSTER': 'my-custom-cluster'}):
        with patch.object(spot_interruption_handler, 'get_ecs_client') as mock_get_client:
            mock_ecs = MagicMock()
            mock_ecs.describe_tasks.return_value = {'tasks': [{'tags': []}]}
            mock_get_client.return_value = mock_ecs
            get_ecs_task_tags = getattr(spot_interruption_handler, "_get_ecs_task_tags")
            get_ecs_task_tags('arn:aws:ecs:test:task/123')
            call_kwargs = mock_ecs.describe_tasks.call_args[1]
    assert call_kwargs['cluster'] == 'my-custom-cluster'


def test_rerun_github_job_returns_false_when_no_job_id(spot_interruption_handler):
    """Test rerun github job returns false when no job id."""
    result = spot_interruption_handler.rerun_github_job('token', 'test/repo', '')
    assert result is False


def test_rerun_github_job_calls_github_api(spot_interruption_handler):
    """Test rerun github job calls github api."""
    mock_response = Mock()
    mock_response.status = 201
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
        spot_interruption_handler.rerun_github_job('test-token', 'test/repo', '123')
        call_args = mock_urlopen.call_args[0][0]
    assert 'actions/jobs/123/rerun' in call_args.full_url


def test_rerun_github_job_returns_true_on_success(spot_interruption_handler):
    """Test rerun github job returns true on success."""
    mock_response = Mock()
    mock_response.status = 201
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = spot_interruption_handler.rerun_github_job('test-token', 'test/repo', '123')
    assert result is True


def test_rerun_github_job_returns_false_on_http_error(spot_interruption_handler):
    """Test rerun github job returns false on http error."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'http://test', 404, 'Not Found', {}, None
        )
        result = spot_interruption_handler.rerun_github_job('test-token', 'test/repo', '123')
    assert result is False


def test_rerun_github_job_returns_false_on_url_error(spot_interruption_handler):
    """Test rerun github job returns false on url error."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError('Connection refused')
        result = spot_interruption_handler.rerun_github_job('test-token', 'test/repo', '123')
    assert result is False


def test_handle_ecs_task_stopped_fetches_tags_from_api(spot_interruption_handler):
    """Test handle ecs task stopped fetches tags from api."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {}
        spot_interruption_handler.handle_ecs_task_stopped(event)
    assert mock_get_tags.called


def test_handle_ecs_task_stopped_passes_task_arn_to_get_tags(spot_interruption_handler):
    """Test handle ecs task stopped passes task arn to get tags."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/456',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {}
        spot_interruption_handler.handle_ecs_task_stopped(event)
        call_args = mock_get_tags.call_args[0]
    assert call_args[0] == 'arn:aws:ecs:test:task/456'


def test_handle_ecs_task_stopped_skips_when_no_run_id(spot_interruption_handler):
    """Test handle ecs task stopped skips when no run id."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Spot interrupted'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {'GitHubJobId': '456'}
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No run_id or job_id'


def test_handle_ecs_task_stopped_skips_when_no_job_id(spot_interruption_handler):
    """Test handle ecs task stopped skips when no job id."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Spot interrupted'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {'RunId': '123'}
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No run_id or job_id'


def test_handle_ecs_task_stopped_skips_non_spot_interruption(spot_interruption_handler):
    """Test handle ecs task stopped skips non spot interruption."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'UserInitiated',
            'stoppedReason': 'Workflow completed'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'GitHubJobId': '456',
            'GitHubRepo': 'test/repo'
        }
        result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'Not a spot interruption'


def test_handle_ecs_task_stopped_triggers_job_rerun_on_spot_interruption(spot_interruption_handler):
    """Test handle ecs task stopped triggers job rerun on spot interruption."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'GitHubJobId': '456',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = 'test-token'
            get_status_patch = patch.object(
                spot_interruption_handler, 'get_workflow_run_status'
            )
            with get_status_patch as mock_get_status:
                mock_get_status.return_value = 'in_progress'
                with patch.object(spot_interruption_handler, 'rerun_github_job') as mock_rerun:
                    mock_rerun.return_value = True
                    result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'Job re-run triggered'


def test_handle_ecs_task_stopped_passes_job_id_to_rerun(spot_interruption_handler):
    """Test handle ecs task stopped passes job id to rerun."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'GitHubJobId': '789',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = 'test-token'
            get_status_patch = patch.object(
                spot_interruption_handler, 'get_workflow_run_status'
            )
            with get_status_patch as mock_get_status:
                mock_get_status.return_value = 'in_progress'
                with patch.object(spot_interruption_handler, 'rerun_github_job') as mock_rerun:
                    mock_rerun.return_value = True
                    spot_interruption_handler.handle_ecs_task_stopped(event)
                    call_args = mock_rerun.call_args[0]
    assert call_args[2] == '789'


def test_handle_ecs_task_stopped_checks_workflow_status_before_rerun(spot_interruption_handler):
    """Test handle ecs task stopped checks workflow status before rerun."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'GitHubJobId': '456',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = 'test-token'
            get_status_patch = patch.object(
                spot_interruption_handler, 'get_workflow_run_status'
            )
            with get_status_patch as mock_get_status:
                mock_get_status.return_value = 'completed'
                result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert 'Workflow not active' in result['body']


def test_handle_ecs_task_stopped_fails_when_no_github_token(spot_interruption_handler):
    """Test handle ecs task stopped fails when no github token."""
    event = {
        'detail': {
            'taskArn': 'arn:aws:ecs:test:task/123',
            'stopCode': 'SpotInterruption',
            'stoppedReason': 'Your Spot Task was interrupted.'
        }
    }
    get_ecs_task_tags_fn = getattr(spot_interruption_handler, "_get_ecs_task_tags")
    with patch.object(
        spot_interruption_handler, '_get_ecs_task_tags', wraps=get_ecs_task_tags_fn
    ) as mock_get_tags:
        mock_get_tags.return_value = {
            'RunId': '123',
            'GitHubJobId': '456',
            'GitHubRepo': 'test/repo'
        }
        with patch.object(spot_interruption_handler, 'get_github_token') as mock_get_token:
            mock_get_token.return_value = ''
            result = spot_interruption_handler.handle_ecs_task_stopped(event)
    assert result['body'] == 'No GitHub token'
