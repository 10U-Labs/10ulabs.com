from unittest.mock import MagicMock
from test.api.post_deployment.conftest import get_ecs_task_tags


def test_get_ecs_task_tags_calls_describe_tasks_with_include_tags():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{'tags': []}]
    }
    get_ecs_task_tags(mock_ecs_client, 'test-cluster', 'test-task-arn')
    call_kwargs = mock_ecs_client.describe_tasks.call_args[1]
    assert call_kwargs.get('include') == ['TAGS']


def test_get_ecs_task_tags_passes_correct_cluster():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{'tags': []}]
    }
    get_ecs_task_tags(mock_ecs_client, 'my-cluster', 'test-task-arn')
    call_kwargs = mock_ecs_client.describe_tasks.call_args[1]
    assert call_kwargs.get('cluster') == 'my-cluster'


def test_get_ecs_task_tags_passes_correct_task_arn():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{'tags': []}]
    }
    get_ecs_task_tags(mock_ecs_client, 'test-cluster', 'arn:aws:ecs:us-east-1:123:task/abc')
    call_kwargs = mock_ecs_client.describe_tasks.call_args[1]
    assert call_kwargs.get('tasks') == ['arn:aws:ecs:us-east-1:123:task/abc']


def test_get_ecs_task_tags_returns_dict_with_tag_key_and_value():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{
            'tags': [
                {'key': 'Type', 'value': 'ephemeral-runner'}
            ]
        }]
    }
    result = get_ecs_task_tags(mock_ecs_client, 'test-cluster', 'test-task-arn')
    assert result.get('Type') == 'ephemeral-runner'


def test_get_ecs_task_tags_returns_empty_dict_when_no_tags():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{'tags': []}]
    }
    result = get_ecs_task_tags(mock_ecs_client, 'test-cluster', 'test-task-arn')
    assert result == {}


def test_get_ecs_task_tags_handles_missing_tags_key():
    mock_ecs_client = MagicMock()
    mock_ecs_client.describe_tasks.return_value = {
        'tasks': [{}]
    }
    result = get_ecs_task_tags(mock_ecs_client, 'test-cluster', 'test-task-arn')
    assert result == {}
