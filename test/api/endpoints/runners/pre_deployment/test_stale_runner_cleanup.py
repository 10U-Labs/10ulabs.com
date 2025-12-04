# pylint: disable=protected-access
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import urllib.error

from botocore.exceptions import ClientError

from .conftest import parse_response_body, assert_response_status


def test_get_github_token_returns_token_from_ssm(stale_runner_cleanup):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token-123'}}
    stale_runner_cleanup._clients = {'ssm': mock_ssm}
    with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/github/token'}):
        result = stale_runner_cleanup.get_github_token()
    assert result == 'test-token-123'


def test_get_github_token_returns_empty_when_no_parameter_name(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.get_github_token()
    assert result == ''


def test_get_github_token_returns_empty_on_client_error(stale_runner_cleanup):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError({'Error': {'Code': 'ParameterNotFound'}}, 'GetParameter')
    stale_runner_cleanup._clients = {'ssm': mock_ssm}
    with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/github/token'}):
        result = stale_runner_cleanup.get_github_token()
    assert result == ''


def test_get_workflow_run_status_returns_status(stale_runner_cleanup, mock_urllib_response_factory):
    mock_response = mock_urllib_response_factory(json_data={'status': 'completed'})
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = stale_runner_cleanup.get_workflow_run_status('token', 'owner/repo', '123')
    assert result == 'completed'


def test_get_workflow_run_status_returns_not_found_on_404(stale_runner_cleanup):
    error = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
    with patch('urllib.request.urlopen', side_effect=error):
        result = stale_runner_cleanup.get_workflow_run_status('token', 'owner/repo', '123')
    assert result == 'not_found'


def test_get_workflow_run_status_returns_unknown_on_other_http_error(stale_runner_cleanup):
    error = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
    with patch('urllib.request.urlopen', side_effect=error):
        result = stale_runner_cleanup.get_workflow_run_status('token', 'owner/repo', '123')
    assert result == 'unknown'


def test_get_workflow_run_status_returns_unknown_on_url_error(stale_runner_cleanup):
    error = urllib.error.URLError('Connection refused')
    with patch('urllib.request.urlopen', side_effect=error):
        result = stale_runner_cleanup.get_workflow_run_status('token', 'owner/repo', '123')
    assert result == 'unknown'


def test_delete_github_runner_returns_true_when_runner_not_found(stale_runner_cleanup, mock_urllib_response_factory):
    mock_response = mock_urllib_response_factory(json_data={'runners': []})
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = stale_runner_cleanup.delete_github_runner('token', 'owner/repo', 'runner-name')
    assert result is True


def test_delete_github_runner_deletes_existing_runner(stale_runner_cleanup, mock_urllib_response_factory):
    list_response = mock_urllib_response_factory(json_data={'runners': [{'id': 123, 'name': 'runner-name'}]})
    delete_response = mock_urllib_response_factory(json_data={})
    with patch('urllib.request.urlopen', side_effect=[list_response, delete_response]):
        result = stale_runner_cleanup.delete_github_runner('token', 'owner/repo', 'runner-name')
    assert result is True


def test_delete_github_runner_returns_true_on_204(stale_runner_cleanup, mock_urllib_response_factory):
    list_response = mock_urllib_response_factory(json_data={'runners': [{'id': 123, 'name': 'runner-name'}]})
    error = urllib.error.HTTPError('url', 204, 'No Content', {}, None)
    with patch('urllib.request.urlopen', side_effect=[list_response, error]):
        result = stale_runner_cleanup.delete_github_runner('token', 'owner/repo', 'runner-name')
    assert result is True


def test_delete_github_runner_returns_false_on_http_error(stale_runner_cleanup):
    error = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
    with patch('urllib.request.urlopen', side_effect=error):
        result = stale_runner_cleanup.delete_github_runner('token', 'owner/repo', 'runner-name')
    assert result is False


def test_delete_github_runner_returns_false_on_url_error(stale_runner_cleanup):
    error = urllib.error.URLError('Connection refused')
    with patch('urllib.request.urlopen', side_effect=error):
        result = stale_runner_cleanup.delete_github_runner('token', 'owner/repo', 'runner-name')
    assert result is False


def test_get_all_workflow_runners_returns_runners(stale_runner_cleanup):
    mock_dynamodb = MagicMock()
    mock_dynamodb.scan.return_value = {
        'Items': [
            {
                'run_id': {'S': '123'},
                'runner_type': {'S': 'fargate'},
                'resource_id': {'S': 'task-arn'},
                'runner_name': {'S': 'runner-1'},
                'github_repo': {'S': 'owner/repo'},
                'created_at': {'N': '1234567890'}
            }
        ]
    }
    stale_runner_cleanup._clients = {'dynamodb': mock_dynamodb}
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        result = stale_runner_cleanup.get_all_workflow_runners()
    assert len(result) == 1


def test_get_all_workflow_runners_returns_empty_when_no_table(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.get_all_workflow_runners()
    assert len(result) == 0


def test_get_all_workflow_runners_returns_empty_on_client_error(stale_runner_cleanup):
    mock_dynamodb = MagicMock()
    mock_dynamodb.scan.side_effect = ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, 'Scan')
    stale_runner_cleanup._clients = {'dynamodb': mock_dynamodb}
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        result = stale_runner_cleanup.get_all_workflow_runners()
    assert len(result) == 0


def test_delete_workflow_runner_returns_true_on_success(stale_runner_cleanup):
    mock_dynamodb = MagicMock()
    mock_dynamodb.delete_item.return_value = {}
    stale_runner_cleanup._clients = {'dynamodb': mock_dynamodb}
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        result = stale_runner_cleanup.delete_workflow_runner('123', 'fargate')
    assert result is True


def test_delete_workflow_runner_returns_false_when_no_table(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.delete_workflow_runner('123', 'fargate')
    assert result is False


def test_delete_workflow_runner_returns_false_on_client_error(stale_runner_cleanup):
    mock_dynamodb = MagicMock()
    mock_dynamodb.delete_item.side_effect = ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, 'DeleteItem')
    stale_runner_cleanup._clients = {'dynamodb': mock_dynamodb}
    with patch.dict('os.environ', {'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        result = stale_runner_cleanup.delete_workflow_runner('123', 'fargate')
    assert result is False


def test_terminate_ecs_task_returns_true_on_success(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.stop_task.return_value = {}
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup.terminate_ecs_task('task-arn')
    assert result is True


def test_terminate_ecs_task_returns_false_when_no_cluster(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.terminate_ecs_task('task-arn')
    assert result is False


def test_terminate_ecs_task_returns_true_on_task_not_found(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.stop_task.side_effect = ClientError({'Error': {'Code': 'TaskNotFound'}}, 'StopTask')
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup.terminate_ecs_task('task-arn')
    assert result is True


def test_terminate_ecs_task_returns_false_on_other_error(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.stop_task.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'StopTask')
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup.terminate_ecs_task('task-arn')
    assert result is False


def test_terminate_ec2_instance_returns_true_on_success(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.terminate_instances.return_value = {}
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    result = stale_runner_cleanup.terminate_ec2_instance('i-12345')
    assert result is True


def test_terminate_ec2_instance_returns_true_on_not_found(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.terminate_instances.side_effect = ClientError({'Error': {'Code': 'InvalidInstanceID.NotFound'}}, 'TerminateInstances')
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    result = stale_runner_cleanup.terminate_ec2_instance('i-12345')
    assert result is True


def test_terminate_ec2_instance_returns_false_on_other_error(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.terminate_instances.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'TerminateInstances')
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    result = stale_runner_cleanup.terminate_ec2_instance('i-12345')
    assert result is False


def test_is_runner_stale_returns_true_when_old(stale_runner_cleanup):
    current_time = int(time.time())
    created_at = current_time - 7200
    result = stale_runner_cleanup._is_runner_stale(created_at, current_time)
    assert result is True


def test_is_runner_stale_returns_false_when_recent(stale_runner_cleanup):
    current_time = int(time.time())
    created_at = current_time - 1800
    result = stale_runner_cleanup._is_runner_stale(created_at, current_time)
    assert result is False


def test_is_runner_stale_returns_true_when_no_created_at(stale_runner_cleanup):
    current_time = int(time.time())
    result = stale_runner_cleanup._is_runner_stale(0, current_time)
    assert result is True


def test_is_orphaned_ecs_task_returns_none_when_wrong_type(stale_runner_cleanup):
    task = {'tags': [{'key': 'Type', 'value': 'other'}], 'taskArn': 'arn'}
    current_time = datetime.now(timezone.utc)
    result = stale_runner_cleanup._is_orphaned_ecs_task(task, current_time)
    assert result is None


def test_is_orphaned_ecs_task_returns_none_when_wrong_managed_by(stale_runner_cleanup):
    task = {
        'tags': [
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'other'}
        ],
        'taskArn': 'arn'
    }
    current_time = datetime.now(timezone.utc)
    result = stale_runner_cleanup._is_orphaned_ecs_task(task, current_time)
    assert result is None


def test_is_orphaned_ecs_task_returns_none_when_no_start_time(stale_runner_cleanup):
    task = {
        'tags': [
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'ecs-runner-api'}
        ],
        'taskArn': 'arn'
    }
    current_time = datetime.now(timezone.utc)
    result = stale_runner_cleanup._is_orphaned_ecs_task(task, current_time)
    assert result is None


def test_is_orphaned_ecs_task_returns_none_when_recent(stale_runner_cleanup):
    current_time = datetime.now(timezone.utc)
    task = {
        'tags': [
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'ecs-runner-api'}
        ],
        'taskArn': 'arn',
        'startedAt': current_time - timedelta(minutes=30)
    }
    result = stale_runner_cleanup._is_orphaned_ecs_task(task, current_time)
    assert result is None


def test_is_orphaned_ecs_task_returns_task_when_stale(stale_runner_cleanup):
    current_time = datetime.now(timezone.utc)
    task = {
        'tags': [
            {'key': 'Type', 'value': 'workflow-runner'},
            {'key': 'ManagedBy', 'value': 'ecs-runner-api'},
            {'key': 'Name', 'value': 'runner-1'},
            {'key': 'GitHubRepo', 'value': 'owner/repo'}
        ],
        'taskArn': 'arn:aws:ecs:us-east-1:123:task/test',
        'startedAt': current_time - timedelta(hours=2)
    }
    result = stale_runner_cleanup._is_orphaned_ecs_task(task, current_time)
    assert result is not None


def test_get_orphaned_ecs_tasks_returns_empty_when_no_cluster(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.get_orphaned_ecs_tasks()
    assert len(result) == 0


def test_get_orphaned_ecs_tasks_returns_empty_when_no_tasks(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': []}]
    mock_ecs.get_paginator.return_value = mock_paginator
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup.get_orphaned_ecs_tasks()
    assert len(result) == 0


def test_get_orphaned_ecs_tasks_returns_empty_on_client_error(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.get_paginator.side_effect = ClientError({'Error': {'Code': 'ClusterNotFoundException'}}, 'GetPaginator')
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup.get_orphaned_ecs_tasks()
    assert len(result) == 0


def test_get_orphaned_ec2_instances_returns_empty_when_no_tag(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.get_orphaned_ec2_instances()
    assert len(result) == 0


def test_get_orphaned_ec2_instances_returns_stale_instances(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    launch_time = datetime.now(timezone.utc) - timedelta(hours=2)
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-12345',
                'LaunchTime': launch_time,
                'Tags': [
                    {'Key': 'Name', 'Value': 'runner-1'},
                    {'Key': 'GitHubRepo', 'Value': 'owner/repo'}
                ]
            }]
        }]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup.get_orphaned_ec2_instances()
    assert len(result) == 1


def test_get_orphaned_ec2_instances_filters_recent_instances(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    launch_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-12345',
                'LaunchTime': launch_time,
                'Tags': []
            }]
        }]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup.get_orphaned_ec2_instances()
    assert len(result) == 0


def test_get_orphaned_ec2_instances_returns_empty_on_client_error(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'DescribeInstances')
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup.get_orphaned_ec2_instances()
    assert len(result) == 0


def test_cleanup_orphaned_resources_cleans_ecs_tasks(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.stop_task.return_value = {}
    current_time = datetime.now(timezone.utc)
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': ['arn:aws:ecs:us-east-1:123:task/test']}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{
            'taskArn': 'arn:aws:ecs:us-east-1:123:task/test',
            'startedAt': current_time - timedelta(hours=2),
            'tags': [
                {'key': 'Type', 'value': 'workflow-runner'},
                {'key': 'ManagedBy', 'value': 'ecs-runner-api'}
            ]
        }]
    }
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    stale_runner_cleanup._clients = {'ecs': mock_ecs, 'ec2': mock_ec2}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster', 'EC2_MANAGED_BY_TAG': 'ec2-runner-api', 'GITHUB_REPO': 'owner/repo'}):
        result = stale_runner_cleanup.cleanup_orphaned_resources('token')
    assert result['ecs_cleaned'] == 1


def test_terminate_runner_calls_ec2_for_ec2_type(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.terminate_instances.return_value = {}
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    result = stale_runner_cleanup._terminate_runner('ec2', 'i-12345')
    assert result is True


def test_terminate_runner_calls_ecs_for_fargate_type(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.stop_task.return_value = {}
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup._terminate_runner('fargate-spot', 'task-arn')
    assert result is True


def test_terminate_runner_returns_false_for_unknown_type(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    result = stale_runner_cleanup._terminate_runner('unknown', 'resource-id')
    assert result is False


def test_cleanup_stale_runners_returns_error_without_token(stale_runner_cleanup):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError({'Error': {'Code': 'ParameterNotFound'}}, 'GetParameter')
    stale_runner_cleanup._clients = {'ssm': mock_ssm}
    with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
        result = stale_runner_cleanup.cleanup_stale_runners()
    assert result['errors'] == 1


def test_cleanup_stale_runners_skips_active_workflows(stale_runner_cleanup, mock_urllib_response_factory):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'token'}}
    mock_dynamodb = MagicMock()
    current_time = int(time.time())
    mock_dynamodb.scan.return_value = {
        'Items': [{
            'run_id': {'S': '123'},
            'runner_type': {'S': 'fargate'},
            'resource_id': {'S': 'task-arn'},
            'runner_name': {'S': 'runner-1'},
            'github_repo': {'S': 'owner/repo'},
            'created_at': {'N': str(current_time - 7200)}
        }]
    }
    stale_runner_cleanup._clients = {'ssm': mock_ssm, 'dynamodb': mock_dynamodb}
    mock_response = mock_urllib_response_factory(json_data={'status': 'in_progress'})
    with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token', 'WORKFLOW_RUNNERS_TABLE': 'test-table'}):
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = stale_runner_cleanup.cleanup_stale_runners()
    assert result['cleaned'] == 0


def test_lambda_handler_returns_200(stale_runner_cleanup, lambda_context):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'token'}}
    mock_dynamodb = MagicMock()
    mock_dynamodb.scan.return_value = {'Items': []}
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': []}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    stale_runner_cleanup._clients = {'ssm': mock_ssm, 'dynamodb': mock_dynamodb, 'ecs': mock_ecs, 'ec2': mock_ec2}
    with patch.dict('os.environ', {
        'GITHUB_TOKEN_SECRET_NAME': '/test/token',
        'WORKFLOW_RUNNERS_TABLE': 'test-table',
        'ECS_CLUSTER': 'test-cluster',
        'EC2_MANAGED_BY_TAG': 'ec2-runner-api'
    }):
        response = stale_runner_cleanup.lambda_handler({}, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_returns_cleanup_counts(stale_runner_cleanup, lambda_context):
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'token'}}
    mock_dynamodb = MagicMock()
    mock_dynamodb.scan.return_value = {'Items': []}
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': []}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    stale_runner_cleanup._clients = {'ssm': mock_ssm, 'dynamodb': mock_dynamodb, 'ecs': mock_ecs, 'ec2': mock_ec2}
    with patch.dict('os.environ', {
        'GITHUB_TOKEN_SECRET_NAME': '/test/token',
        'WORKFLOW_RUNNERS_TABLE': 'test-table',
        'ECS_CLUSTER': 'test-cluster',
        'EC2_MANAGED_BY_TAG': 'ec2-runner-api'
    }):
        response = stale_runner_cleanup.lambda_handler({}, lambda_context)
        body = parse_response_body(response)
    assert 'dynamodb_cleaned' in body


def test_extract_run_id_from_fargate_runner_name(stale_runner_cleanup):
    result = stale_runner_cleanup._extract_run_id_from_runner_name('fargate-runner-12345')
    assert result == '12345'


def test_extract_run_id_from_ec2_runner_name(stale_runner_cleanup):
    result = stale_runner_cleanup._extract_run_id_from_runner_name('ec2-runner-67890')
    assert result == '67890'


def test_extract_run_id_returns_empty_for_unknown_prefix(stale_runner_cleanup):
    result = stale_runner_cleanup._extract_run_id_from_runner_name('unknown-runner-123')
    assert result == ''


def test_extract_run_id_returns_empty_for_empty_string(stale_runner_cleanup):
    result = stale_runner_cleanup._extract_run_id_from_runner_name('')
    assert result == ''


def test_get_ecs_task_arns_returns_running_tasks(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': ['arn:aws:ecs:us-east-1:123:task/running']}]
    mock_ecs.get_paginator.return_value = mock_paginator
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    result = stale_runner_cleanup._get_ecs_task_arns('test-cluster')
    assert len(result) == 2


def test_get_ecs_task_arns_returns_pending_tasks(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.side_effect = [[{'taskArns': ['arn1']}], [{'taskArns': ['arn2']}]]
    mock_ecs.get_paginator.return_value = mock_paginator
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    result = stale_runner_cleanup._get_ecs_task_arns('test-cluster')
    assert 'arn1' in result


def test_check_tasks_for_run_id_returns_true_when_found(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{'taskArn': 'arn1', 'tags': [{'key': 'RunId', 'value': '12345'}]}]
    }
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    result = stale_runner_cleanup._check_tasks_for_run_id('cluster', ['arn1'], '12345')
    assert result is True


def test_check_tasks_for_run_id_returns_false_when_not_found(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{'taskArn': 'arn1', 'tags': [{'key': 'RunId', 'value': '99999'}]}]
    }
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    result = stale_runner_cleanup._check_tasks_for_run_id('cluster', ['arn1'], '12345')
    assert result is False


def test_check_tasks_for_run_id_returns_false_for_empty_task_list(stale_runner_cleanup):
    mock_ecs = MagicMock()
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    result = stale_runner_cleanup._check_tasks_for_run_id('cluster', [], '12345')
    assert result is False


def test_has_running_ecs_task_by_name_returns_true_when_found(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': ['arn1']}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{'taskArn': 'arn1', 'tags': [{'key': 'RunId', 'value': '12345'}]}]
    }
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup._has_running_ecs_task_by_name('fargate-runner-12345')
    assert result is True


def test_has_running_ecs_task_by_name_returns_false_when_not_found(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': ['arn1']}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{'taskArn': 'arn1', 'tags': [{'key': 'RunId', 'value': '99999'}]}]
    }
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup._has_running_ecs_task_by_name('fargate-runner-12345')
    assert result is False


def test_has_running_ecs_task_by_name_returns_false_without_cluster(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup._has_running_ecs_task_by_name('fargate-runner-12345')
    assert result is False


def test_has_running_ecs_task_by_name_returns_false_on_client_error(stale_runner_cleanup):
    mock_ecs = MagicMock()
    mock_ecs.get_paginator.side_effect = ClientError({'Error': {'Code': 'ClusterNotFoundException'}}, 'GetPaginator')
    stale_runner_cleanup._clients = {'ecs': mock_ecs}
    with patch.dict('os.environ', {'ECS_CLUSTER': 'test-cluster'}):
        result = stale_runner_cleanup._has_running_ecs_task_by_name('fargate-runner-12345')
    assert result is False


def test_has_running_ec2_by_name_returns_true_when_found(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{'Instances': [{'InstanceId': 'i-12345'}]}]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup._has_running_ec2_by_name('ec2-runner-12345')
    assert result is True


def test_has_running_ec2_by_name_returns_false_when_not_found(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup._has_running_ec2_by_name('ec2-runner-12345')
    assert result is False


def test_has_running_ec2_by_name_returns_false_without_tag(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup._has_running_ec2_by_name('ec2-runner-12345')
    assert result is False


def test_has_running_ec2_by_name_returns_false_on_client_error(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'DescribeInstances')
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api'}):
        result = stale_runner_cleanup._has_running_ec2_by_name('ec2-runner-12345')
    assert result is False


def test_runner_has_infrastructure_returns_true_for_ec2(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{'Instances': [{'InstanceId': 'i-12345'}]}]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api', 'ECS_CLUSTER': 'cluster'}):
        result = stale_runner_cleanup._runner_has_infrastructure('ec2-runner-12345')
    assert result is True


def test_runner_has_infrastructure_returns_true_for_ecs(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': ['arn1']}]
    mock_ecs.get_paginator.return_value = mock_paginator
    mock_ecs.describe_tasks.return_value = {
        'tasks': [{'taskArn': 'arn1', 'tags': [{'key': 'RunId', 'value': '12345'}]}]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2, 'ecs': mock_ecs}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api', 'ECS_CLUSTER': 'cluster'}):
        result = stale_runner_cleanup._runner_has_infrastructure('fargate-runner-12345')
    assert result is True


def test_runner_has_infrastructure_returns_false_when_none(stale_runner_cleanup):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': []}]
    mock_ecs.get_paginator.return_value = mock_paginator
    stale_runner_cleanup._clients = {'ec2': mock_ec2, 'ecs': mock_ecs}
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'ec2-runner-api', 'ECS_CLUSTER': 'cluster'}):
        result = stale_runner_cleanup._runner_has_infrastructure('fargate-runner-99999')
    assert result is False


def test_cleanup_orphaned_github_runners_returns_error_without_repo(stale_runner_cleanup):
    stale_runner_cleanup._clients = {}
    with patch.dict('os.environ', {}, clear=True):
        result = stale_runner_cleanup.cleanup_orphaned_github_runners('token')
    assert result['errors'] == 1


def test_cleanup_orphaned_github_runners_returns_error_without_token(stale_runner_cleanup):
    with patch.dict('os.environ', {'GITHUB_REPO': 'owner/repo'}):
        result = stale_runner_cleanup.cleanup_orphaned_github_runners('')
    assert result['errors'] == 1


def test_cleanup_orphaned_github_runners_returns_error_when_api_fails(stale_runner_cleanup, mock_urllib_response_factory):
    error = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
    with patch.dict('os.environ', {'GITHUB_REPO': 'owner/repo'}):
        with patch('urllib.request.urlopen', side_effect=error):
            result = stale_runner_cleanup.cleanup_orphaned_github_runners('token')
    assert result['errors'] == 1


def test_cleanup_orphaned_github_runners_skips_online_runners(stale_runner_cleanup, mock_urllib_response_factory):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    mock_response = mock_urllib_response_factory(json_data={
        'runners': [{'id': 123, 'name': 'runner-1', 'status': 'online'}]
    })
    with patch.dict('os.environ', {'GITHUB_REPO': 'owner/repo', 'EC2_MANAGED_BY_TAG': 'tag', 'ECS_CLUSTER': 'cluster'}):
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = stale_runner_cleanup.cleanup_orphaned_github_runners('token')
    assert result['github_cleaned'] == 0


def test_cleanup_orphaned_github_runners_skips_runners_with_infrastructure(stale_runner_cleanup, mock_urllib_response_factory):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]
    }
    stale_runner_cleanup._clients = {'ec2': mock_ec2}
    mock_response = mock_urllib_response_factory(json_data={
        'runners': [{'id': 123, 'name': 'ec2-runner-12345', 'status': 'offline'}]
    })
    with patch.dict('os.environ', {'GITHUB_REPO': 'owner/repo', 'EC2_MANAGED_BY_TAG': 'tag', 'ECS_CLUSTER': 'cluster'}):
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = stale_runner_cleanup.cleanup_orphaned_github_runners('token')
    assert result['github_cleaned'] == 0


def test_cleanup_orphaned_github_runners_deletes_orphaned_offline_runner(stale_runner_cleanup, mock_urllib_response_factory):
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {'Reservations': []}
    mock_ecs = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{'taskArns': []}]
    mock_ecs.get_paginator.return_value = mock_paginator
    stale_runner_cleanup._clients = {'ec2': mock_ec2, 'ecs': mock_ecs}
    list_response = mock_urllib_response_factory(json_data={
        'runners': [{'id': 123, 'name': 'fargate-runner-12345', 'status': 'offline'}]
    })
    delete_response = mock_urllib_response_factory(json_data={})
    with patch.dict('os.environ', {'GITHUB_REPO': 'owner/repo', 'EC2_MANAGED_BY_TAG': 'tag', 'ECS_CLUSTER': 'cluster'}):
        with patch('urllib.request.urlopen', side_effect=[list_response, delete_response]):
            result = stale_runner_cleanup.cleanup_orphaned_github_runners('token')
    assert result['github_cleaned'] == 1
