"""Unit tests for EC2 runner Lambda handler."""
import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from terraform_config import TEST_AWS_REGION
from .conftest import (
    assert_json_content_type,
    assert_response_status,
    create_multi_client_mock,
    parse_response_body,
)


def test_lambda_handler_ec2_runner_post_with_missing_job_id_returns_400(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST without job_id returns 400."""
    event = ec2_runner_post_event_factory()
    body = json.loads(event['body'])
    del body['job_id']
    event['body'] = json.dumps(body)
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_lambda_handler_ec2_runner_post_with_missing_repo_returns_400(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST without github_repo returns 400."""
    event = ec2_runner_post_event_factory()
    body = json.loads(event['body'])
    del body['github_repo']
    event['body'] = json.dumps(body)
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


@pytest.mark.usefixtures('mock_boto_client')
def test_lambda_handler_ec2_runner_post_returns_json_content_type(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that POST returns JSON content type."""
    event = ec2_runner_post_event_factory(job_id=12345, github_repo='test-org/test-repo')
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert_json_content_type(response)


def test_get_ec2_runner_status_returns_success_with_no_instances(ec2_runner_handler):
    """Test that status returns success with no instances."""
    with patch.object(ec2_runner_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_success = result['success']
        assert is_success


def test_get_ec2_runner_status_returns_zero_running_instances_when_empty(ec2_runner_handler):
    """Test that status returns zero running instances when empty."""
    with patch.object(ec2_runner_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        has_zero_instances = result['running_instances'] == 0
        assert has_zero_instances


def test_get_ec2_runner_status_returns_empty_instance_list_when_none_running(ec2_runner_handler):
    """Test that status returns empty instance list when none running."""
    with patch.object(ec2_runner_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_empty_list = result['instances'] == []
        assert is_empty_list


def test_get_ec2_runner_status_handles_client_error(ec2_runner_handler):
    """Test that status handles client errors gracefully."""
    with patch.object(ec2_runner_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'describe_instances'
        )
        mock_get_client.return_value = mock_ec2
        result = ec2_runner_handler.get_ec2_runner_status()
        is_failure = not result['success']
        assert is_failure


def test_get_ec2_runner_status_filters_by_managed_by_tag_from_env(ec2_runner_handler):
    """Test that status filters by ManagedBy tag."""
    with patch.object(ec2_runner_handler, 'get_ec2_client') as mock_get_client:
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_get_client.return_value = mock_ec2
        ec2_runner_handler.get_ec2_runner_status()
        call_args = mock_ec2.describe_instances.call_args
        filters = call_args[1]['Filters']
        managed_by_filter = next(f for f in filters if f['Name'] == 'tag:ManagedBy')
        has_correct_tag = managed_by_filter['Values'] == ['api-ec2-runner']
        assert has_correct_tag


def test_handle_ec2_runner_get_returns_200_status(
    ec2_runner_handler, ec2_runner_get_event, lambda_context
):
    """Test that GET handler returns 200 status."""
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = ec2_runner_handler.lambda_handler(ec2_runner_get_event, lambda_context)
        assert_response_status(response, 200)


def test_handle_ec2_runner_get_returns_json_content_type(
    ec2_runner_handler, ec2_runner_get_event, lambda_context
):
    """Test that GET handler returns JSON content type."""
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        response = ec2_runner_handler.lambda_handler(ec2_runner_get_event, lambda_context)
        assert_json_content_type(response)


def test_create_ec2_user_data_formatting(ec2_runner_handler):
    """Test that user data formatting includes token."""
    with patch.dict('os.environ', {'AWS_REGION': TEST_AWS_REGION}):
        create_ec2_user_data = getattr(ec2_runner_handler, 'create_ec2_user_data')
        result = create_ec2_user_data(
            'test-token', ['label1', 'label2'], 'test/repo', 'test-runner'
        )
        contains_token = 'test-token' in result
        assert contains_token


@patch('boto3.client')
def test_get_latest_ami_multiple_amis(mock_boto_client, ec2_runner_handler):
    """Test that latest AMI is selected when multiple exist."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [
            {'ImageId': 'ami-old', 'CreationDate': '2024-01-01T00:00:00'},
            {'ImageId': 'ami-new', 'CreationDate': '2024-01-05T00:00:00'}
        ]
    }
    mock_boto_client.return_value = mock_ec2
    result = ec2_runner_handler.get_latest_ami()
    is_newest_ami = result == 'ami-new'
    assert is_newest_ami


@patch('boto3.client')
def test_get_latest_ami_no_amis(mock_boto_client, ec2_runner_handler):
    """Test that empty string is returned when no AMIs exist."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {'Images': []}
    mock_boto_client.return_value = mock_ec2
    result = ec2_runner_handler.get_latest_ami()
    is_empty = result == ''
    assert is_empty


@patch('boto3.client')
def test_get_latest_ami_client_error(mock_boto_client, ec2_runner_handler):
    """Test that client error returns empty string."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'TestError'}}, 'DescribeImages'
    )
    mock_boto_client.return_value = mock_ec2
    result = ec2_runner_handler.get_latest_ami()
    is_empty = result == ''
    assert is_empty


def test_get_ec2_config_parsing(ec2_runner_handler):
    """Test that EC2 config is parsed correctly from environment."""
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1,subnet-2',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small,t3.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile'
    }):
        result = getattr(ec2_runner_handler, "get_ec2_config")()
        has_correct_profile = result['iam_instance_profile'] == 'test-profile'
        assert has_correct_profile


@patch('boto3.client')
def test_launch_ec2_runner_no_ami(mock_boto_client, ec2_runner_handler):
    """Test that launch fails gracefully when no AMI is available."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {'Images': []}
    mock_boto_client.return_value = mock_ec2
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile',
        'API_DOMAIN': 'api.test.com'
    }):
        with patch.object(
            ec2_runner_handler, 'trigger_ami_creation', return_value={'success': True}
        ):
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_insufficient_capacity_all_azs(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when all AZs have insufficient capacity."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test', 'CreationDate': '2024-01-01T00:00:00'}]
    }
    mock_ec2.create_launch_template.return_value = {
        'LaunchTemplate': {'LaunchTemplateId': 'lt-12345'}
    }
    mock_ec2.create_fleet.return_value = {
        'Instances': [],
        'Errors': [{'ErrorCode': 'InsufficientInstanceCapacity', 'ErrorMessage': 'No capacity'}]
    }
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-token'}}

    mock_boto_client.side_effect = create_multi_client_mock(mock_ec2, mock_ssm)

    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1,subnet-2',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile',
        'GITHUB_TOKEN_SECRET_NAME': '/token'
    }):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({'token': 'reg-token'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_no_github_token(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when GitHub token is not available."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test', 'CreationDate': '2024-01-01T00:00:00'}]
    }
    mock_boto_client.return_value = mock_ec2
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile'
    }):
        with patch.object(ec2_runner_handler, 'get_github_token', return_value=''):
            result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
            is_failure = not result['success']
            assert is_failure


@patch('boto3.client')
def test_launch_ec2_runner_failed_registration(mock_boto_client, ec2_runner_handler):
    """Test that launch fails when runner registration fails."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [{'ImageId': 'ami-test', 'CreationDate': '2024-01-01T00:00:00'}]
    }
    mock_boto_client.return_value = mock_ec2
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small',
        'EC2_IAM_INSTANCE_PROFILE': 'profile'
    }):
        with patch.object(ec2_runner_handler, 'get_github_token', return_value='token'):
            with patch.object(
                ec2_runner_handler, 'get_runner_registration_token', return_value=''
            ):
                result = ec2_runner_handler.launch_ec2_runner(123, ['test'], 'test/repo')
                is_failure = not result['success']
                assert is_failure


def test_create_ec2_user_data_includes_region(ec2_runner_handler):
    """Test that user data includes AWS region."""
    result = ec2_runner_handler.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    region = os.environ.get('AWS_REGION', TEST_AWS_REGION)
    contains_region = region in result
    assert contains_region


def test_create_ec2_user_data_includes_nvme_format(ec2_runner_handler):
    """Test that user data includes NVMe formatting commands."""
    result = ec2_runner_handler.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_mkfs = 'mkfs.ext4' in result
    assert contains_mkfs


def test_create_ec2_user_data_includes_nvme_mount(ec2_runner_handler):
    """Test that user data includes NVMe mount commands."""
    result = ec2_runner_handler.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_mount = 'mount' in result
    assert contains_mount


def test_create_ec2_user_data_detects_instance_store_dynamically(ec2_runner_handler):
    """Test that user data includes dynamic instance store detection."""
    result = ec2_runner_handler.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_lsblk = 'lsblk' in result
    assert contains_lsblk


def test_lambda_handler_options_returns_200(ec2_runner_handler, lambda_context):
    """Test that OPTIONS request returns 200."""
    event = {'path': '/v1/ec2-runner', 'httpMethod': 'OPTIONS', 'headers': {}}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_lambda_handler_unknown_path_returns_404(ec2_runner_handler, lambda_context):
    """Test that unknown path returns 404."""
    event = {'path': '/v1/unknown', 'httpMethod': 'GET', 'headers': {}}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 404)


def test_test_mode_header_sets_test_mode(ec2_runner_handler, lambda_context):
    """Test that x-test-mode header enables test mode."""
    event = {
        'path': '/v1/ec2-runner',
        'httpMethod': 'GET',
        'headers': {'x-test-mode': 'true'}
    }
    with patch.object(ec2_runner_handler, 'get_ec2_runner_status') as mock_status:
        mock_status.return_value = {'success': True, 'running_instances': 0, 'instances': []}
        ec2_runner_handler.lambda_handler(event, lambda_context)
        is_test_mode = ec2_runner_handler.is_test_mode()
        assert is_test_mode


def test_test_mode_post_returns_mock_response(
    ec2_runner_handler, ec2_runner_post_event_factory, lambda_context
):
    """Test that test mode POST returns mock response."""
    event = ec2_runner_post_event_factory(job_id=123, github_repo='test/repo')
    event['headers'] = {'x-test-mode': 'true'}
    response = ec2_runner_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    is_test_mode = body.get('test_mode')
    assert is_test_mode
