"""Unit tests for EC2 runner fleet_ops module."""
import os
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from terraform_config import TEST_AWS_REGION


@pytest.fixture(name='fleet_ops_module')
def fixture_fleet_ops(ec2_runner_handler) -> ModuleType:
    """Get fleet_ops module after handler has loaded it into sys.modules."""
    _ = ec2_runner_handler
    return sys.modules['fleet_ops']


def test_create_ec2_user_data_formatting(fleet_ops_module):
    """Test that user data formatting includes token."""
    with patch.dict('os.environ', {'AWS_REGION': TEST_AWS_REGION}):
        result = fleet_ops_module.create_ec2_user_data(
            'test-token', ['label1', 'label2'], 'test/repo', 'test-runner'
        )
        contains_token = 'test-token' in result
        assert contains_token


@patch('fleet_ops.get_ec2_client')
def test_get_latest_ami_multiple_amis(mock_get_client, fleet_ops_module):
    """Test that latest AMI is selected when multiple exist."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {
        'Images': [
            {'ImageId': 'ami-old', 'CreationDate': '2024-01-01T00:00:00'},
            {'ImageId': 'ami-new', 'CreationDate': '2024-01-05T00:00:00'}
        ]
    }
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.get_latest_ami()
    is_newest_ami = result == 'ami-new'
    assert is_newest_ami


@patch('fleet_ops.get_ec2_client')
def test_get_latest_ami_no_amis(mock_get_client, fleet_ops_module):
    """Test that empty string is returned when no AMIs exist."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.return_value = {'Images': []}
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.get_latest_ami()
    is_empty = result == ''
    assert is_empty


@patch('fleet_ops.get_ec2_client')
def test_get_latest_ami_client_error(mock_get_client, fleet_ops_module):
    """Test that client error returns empty string."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_images.side_effect = ClientError(
        {'Error': {'Code': 'TestError'}}, 'DescribeImages'
    )
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.get_latest_ami()
    is_empty = result == ''
    assert is_empty


def test_get_ec2_config_parsing(fleet_ops_module):
    """Test that EC2 config is parsed correctly from environment."""
    with patch.dict('os.environ', {
        'SUBNETS': 'subnet-1,subnet-2',
        'SECURITY_GROUPS': 'sg-1',
        'EC2_INSTANCE_TYPES': 't3.small,t3.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'test-profile'
    }):
        result = fleet_ops_module.get_ec2_config()
        has_correct_profile = result['iam_instance_profile'] == 'test-profile'
        assert has_correct_profile


def test_create_ec2_user_data_includes_region(fleet_ops_module):
    """Test that user data includes AWS region."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    region = os.environ.get('AWS_REGION', TEST_AWS_REGION)
    contains_region = region in result
    assert contains_region


def test_create_ec2_user_data_includes_nvme_format(fleet_ops_module):
    """Test that user data includes NVMe formatting commands."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_mkfs = 'mkfs.ext4' in result
    assert contains_mkfs


def test_create_ec2_user_data_includes_nvme_mount(fleet_ops_module):
    """Test that user data includes NVMe mount commands."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_mount = 'mount' in result
    assert contains_mount


def test_create_ec2_user_data_detects_instance_store_dynamically(fleet_ops_module):
    """Test that user data includes dynamic instance store detection."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_lsblk = 'lsblk' in result
    assert contains_lsblk


def test_create_ec2_user_data_uses_mountpoint_detection(fleet_ops_module):
    """Test that user data detects instance store by checking unmounted disks."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    uses_mountpoint = 'MOUNTPOINT' in result
    assert uses_mountpoint


def test_create_ec2_user_data_starts_cloudwatch_agent(fleet_ops_module):
    """Test that user data starts CloudWatch agent."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_agent_ctl = 'amazon-cloudwatch-agent-ctl' in result
    assert contains_agent_ctl


def test_create_ec2_user_data_cloudwatch_uses_config_file(fleet_ops_module):
    """Test that user data starts CloudWatch agent with config file."""
    result = fleet_ops_module.create_ec2_user_data('token', ['label'], 'repo', 'runner')
    contains_config_path = 'amazon-cloudwatch-agent.json' in result
    assert contains_config_path


@patch('fleet_ops.get_api_key')
@patch('fleet_ops.urllib.request.urlopen')
def test_trigger_ami_creation_success(mock_urlopen, mock_get_api_key, fleet_ops_module):
    """Test that trigger_ami_creation returns success on valid response."""
    mock_get_api_key.return_value = 'test-api-key'
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"success": true}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response

    with patch.dict('os.environ', {'API_FQDN': 'api.test.com'}):
        result = fleet_ops_module.trigger_ami_creation()
        assert result['success'] is True


@patch('fleet_ops.get_api_key')
@patch('fleet_ops.urllib.request.urlopen')
def test_trigger_ami_creation_failure(mock_urlopen, mock_get_api_key, fleet_ops_module):
    """Test that trigger_ami_creation returns failure on error."""
    mock_get_api_key.return_value = 'test-api-key'
    import urllib.error
    mock_urlopen.side_effect = urllib.error.URLError('Connection failed')

    with patch.dict('os.environ', {'API_FQDN': 'api.test.com'}):
        result = fleet_ops_module.trigger_ami_creation()
        assert result['success'] is False


@patch('fleet_ops.get_ec2_client')
def test_wait_for_instance_describable_success(mock_get_client, fleet_ops_module):
    """Test that wait_for_instance_describable returns instance on success."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{'Instances': [{'InstanceId': 'i-test123'}]}]
    }
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.wait_for_instance_describable('i-test123')
    assert result['InstanceId'] == 'i-test123'


@patch('fleet_ops.time.sleep')
@patch('fleet_ops.get_ec2_client')
def test_wait_for_instance_describable_retry(mock_get_client, mock_sleep, fleet_ops_module):
    """Test that wait_for_instance_describable retries on NotFound."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.side_effect = [
        ClientError({'Error': {'Code': 'InvalidInstanceID.NotFound'}}, 'DescribeInstances'),
        {'Reservations': [{'Instances': [{'InstanceId': 'i-test123'}]}]}
    ]
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.wait_for_instance_describable('i-test123')
    assert result['InstanceId'] == 'i-test123'


@patch('fleet_ops.time.sleep')
@patch('fleet_ops.get_ec2_client')
def test_wait_for_instance_describable_max_attempts(mock_get_client, mock_sleep, fleet_ops_module):
    """Test that wait_for_instance_describable raises after max attempts."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.side_effect = ClientError(
        {'Error': {'Code': 'InvalidInstanceID.NotFound'}}, 'DescribeInstances'
    )
    mock_get_client.return_value = mock_ec2
    with pytest.raises(ClientError):
        fleet_ops_module.wait_for_instance_describable('i-test123', max_attempts=2)


@patch('fleet_ops.get_ec2_client')
def test_wait_for_instance_describable_other_error_raises(mock_get_client, fleet_ops_module):
    """Test that wait_for_instance_describable raises non-NotFound errors."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied'}}, 'DescribeInstances'
    )
    mock_get_client.return_value = mock_ec2
    with pytest.raises(ClientError):
        fleet_ops_module.wait_for_instance_describable('i-test123')


@patch('fleet_ops.get_existing_runner_for_workflow')
def test_check_existing_runner_found(mock_get_existing, fleet_ops_module):
    """Test that _check_existing_runner returns result when runner exists."""
    mock_get_existing.return_value = {'name': 'test-runner'}
    result = fleet_ops_module._check_existing_runner({
        'github_token': 'token',
        'github_repo': 'test/repo',
        'run_id': 123,
        'job_id': 456,
        'job_labels': ['ec2'],
        'runner_type': 'ec2'
    })
    assert result['reused'] is True


@patch('fleet_ops.get_existing_runner_for_workflow')
def test_check_existing_runner_not_found(mock_get_existing, fleet_ops_module):
    """Test that _check_existing_runner returns None when no runner exists."""
    mock_get_existing.return_value = None
    result = fleet_ops_module._check_existing_runner({
        'github_token': 'token',
        'github_repo': 'test/repo',
        'run_id': 123,
        'job_id': 456,
        'job_labels': ['ec2'],
        'runner_type': 'ec2'
    })
    assert result is None


@patch('fleet_ops.trigger_ami_creation')
def test_handle_missing_ami_trigger_success(mock_trigger, fleet_ops_module):
    """Test _handle_missing_ami when AMI creation triggers successfully."""
    mock_trigger.return_value = {'success': True}
    result = fleet_ops_module._handle_missing_ami()
    assert result['ami_creation_triggered'] is True


@patch('fleet_ops.trigger_ami_creation')
def test_handle_missing_ami_trigger_failure(mock_trigger, fleet_ops_module):
    """Test _handle_missing_ami when AMI creation fails to trigger."""
    mock_trigger.return_value = {'success': False, 'error': 'Connection failed'}
    result = fleet_ops_module._handle_missing_ami()
    assert result['ami_creation_triggered'] is False


@patch('fleet_ops.ensure_dependencies_valid')
def test_launch_ec2_runner_dependency_validation_fails(mock_ensure, fleet_ops_module):
    """Test launch_ec2_runner returns error when dependency validation fails."""
    mock_ensure.side_effect = RuntimeError('VPC validation failed')
    result = fleet_ops_module.launch_ec2_runner(123, ['ec2'], 'test/repo')
    assert result['success'] is False


@patch('fleet_ops.ensure_dependencies_valid')
@patch('fleet_ops.get_github_token')
@patch('fleet_ops._check_existing_runner')
@patch('fleet_ops.get_latest_ami')
@patch('fleet_ops._handle_missing_ami')
def test_launch_ec2_runner_no_ami_triggers_creation(
    mock_handle_missing, mock_get_ami, mock_check_existing,
    mock_get_token, mock_ensure, fleet_ops_module
):
    """Test launch_ec2_runner triggers AMI creation when no AMI exists."""
    mock_ensure.return_value = None
    mock_get_token.return_value = 'test-token'
    mock_check_existing.return_value = None
    mock_get_ami.return_value = ''
    mock_handle_missing.return_value = {
        'success': False,
        'ami_creation_triggered': True,
        'error': 'No AMI available'
    }
    result = fleet_ops_module.launch_ec2_runner(123, ['ec2'], 'test/repo', run_id=456)
    assert result.get('ami_creation_triggered') is True


@patch('fleet_ops.ensure_dependencies_valid')
@patch('fleet_ops.get_github_token')
@patch('fleet_ops._check_existing_runner')
def test_launch_ec2_runner_reuses_existing_runner(
    mock_check_existing, mock_get_token, mock_ensure, fleet_ops_module
):
    """Test launch_ec2_runner reuses existing runner when available."""
    mock_ensure.return_value = None
    mock_get_token.return_value = 'test-token'
    mock_check_existing.return_value = {
        'success': True,
        'reused': True,
        'runner_name': 'test-runner'
    }
    result = fleet_ops_module.launch_ec2_runner(123, ['ec2'], 'test/repo', run_id=456)
    assert result['reused'] is True


def test_handle_ec2_fleet_success_returns_instance_id(fleet_ops_module):
    """Test _handle_ec2_fleet_success returns correct instance_id."""
    cfg = {'run_id': 123, 'job_id': 456, 'runner_type': 'ec2', 'runner_name': 'test-runner'}
    instance = {'InstanceType': 't3.medium', 'Placement': {'AvailabilityZone': 'us-east-2a'}}
    result = fleet_ops_module._handle_ec2_fleet_success(cfg, instance, 'i-test123')
    assert result['instance_id'] == 'i-test123'


def test_handle_ec2_fleet_success_generates_runner_name(fleet_ops_module):
    """Test _handle_ec2_fleet_success generates runner name when not provided."""
    cfg = {'run_id': 123, 'job_id': 456, 'runner_type': 'ec2'}
    instance = {'InstanceType': 't3.medium', 'Placement': {'AvailabilityZone': 'us-east-2a'}}
    result = fleet_ops_module._handle_ec2_fleet_success(cfg, instance, 'i-test123')
    assert result['runner_name'] == 'ec2-runner-123'


def test_get_fleet_instance_config_uses_labels(fleet_ops_module):
    """Test _get_fleet_instance_config uses instance type from labels."""
    ec2_config = {'instance_types': ['t3.small', 't3.medium']}
    job_labels = ['ec2', 'general-purpose', 'intel', 'spot', 'runner-12345']
    instance_types, _, _ = fleet_ops_module._get_fleet_instance_config(job_labels, ec2_config)
    assert instance_types[0] != 't3.small'


def test_get_fleet_instance_config_uses_config_fallback(fleet_ops_module):
    """Test _get_fleet_instance_config uses config when labels don't specify type."""
    ec2_config = {'instance_types': ['t3.small', 't3.medium']}
    job_labels = ['ec2', 'ephemeral-ec2-instance']
    instance_types, _, _ = fleet_ops_module._get_fleet_instance_config(job_labels, ec2_config)
    assert instance_types == ['t3.small', 't3.medium']


def test_get_fleet_instance_config_spot_pricing(fleet_ops_module):
    """Test _get_fleet_instance_config uses spot pricing by default."""
    ec2_config = {'instance_types': ['t3.small']}
    job_labels = ['ec2', 'ephemeral-ec2-instance']
    _, use_spot, _ = fleet_ops_module._get_fleet_instance_config(job_labels, ec2_config)
    assert use_spot is True


def test_get_fleet_instance_config_on_demand_pricing(fleet_ops_module):
    """Test _get_fleet_instance_config uses on-demand when specified."""
    ec2_config = {'instance_types': ['t3.small']}
    job_labels = ['ec2', 'general-purpose', 'intel', 'on-demand', 'runner-12345']
    _, use_spot, _ = fleet_ops_module._get_fleet_instance_config(job_labels, ec2_config)
    assert use_spot is False


@patch('fleet_ops.get_ec2_client')
def test_create_fleet_request_spot_has_spot_options(mock_get_client, fleet_ops_module):
    """Test _create_fleet_request creates spot fleet request with SpotOptions."""
    mock_ec2 = MagicMock()
    mock_ec2.create_fleet.return_value = {'Instances': [{'InstanceIds': ['i-test']}]}
    mock_get_client.return_value = mock_ec2
    fleet_ops_module._create_fleet_request('lt-test', 'spot', True, ['t3.small'], ['subnet-1'])
    call_kwargs = mock_ec2.create_fleet.call_args[1]
    assert 'SpotOptions' in call_kwargs


@patch('fleet_ops.get_ec2_client')
def test_create_fleet_request_on_demand_has_on_demand_options(mock_get_client, fleet_ops_module):
    """Test _create_fleet_request creates on-demand fleet request with OnDemandOptions."""
    mock_ec2 = MagicMock()
    mock_ec2.create_fleet.return_value = {'Instances': [{'InstanceIds': ['i-test']}]}
    mock_get_client.return_value = mock_ec2
    fleet_ops_module._create_fleet_request('lt-test', 'on-demand', False, ['t3.small'], ['subnet-1'])
    call_kwargs = mock_ec2.create_fleet.call_args[1]
    assert 'OnDemandOptions' in call_kwargs


@patch('fleet_ops.get_ec2_client')
def test_get_ec2_runner_status_with_instances(mock_get_client, fleet_ops_module):
    """Test get_ec2_runner_status returns instances when present."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-test123',
                'InstanceType': 't3.medium',
                'State': {'Name': 'running'},
                'Placement': {'AvailabilityZone': 'us-east-2a'},
                'LaunchTime': MagicMock(isoformat=lambda: '2024-01-01T00:00:00Z'),
                'PublicIpAddress': '1.2.3.4',
                'Tags': [
                    {'Key': 'GitHubJobId', 'Value': '12345'},
                    {'Key': 'JobLabels', 'Value': 'ec2,test'},
                    {'Key': 'GitHubRepo', 'Value': 'test/repo'}
                ]
            }]
        }]
    }
    mock_get_client.return_value = mock_ec2
    result = fleet_ops_module.get_ec2_runner_status()
    assert result['running_instances'] == 1


@patch('fleet_ops.get_ec2_client')
def test_delete_launch_template_error_logged(mock_get_client, fleet_ops_module):
    """Test delete_launch_template handles errors gracefully."""
    mock_ec2 = MagicMock()
    mock_ec2.delete_launch_template.side_effect = ClientError(
        {'Error': {'Code': 'NotFound'}}, 'DeleteLaunchTemplate'
    )
    mock_get_client.return_value = mock_ec2
    fleet_ops_module.delete_launch_template('lt-test')


@patch('fleet_ops.get_ec2_client')
def test_create_fleet_launch_template_success(mock_get_client, fleet_ops_module):
    """Test create_fleet_launch_template returns template ID."""
    mock_ec2 = MagicMock()
    mock_ec2.create_launch_template.return_value = {
        'LaunchTemplate': {'LaunchTemplateId': 'lt-test123'}
    }
    mock_get_client.return_value = mock_ec2
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'api-ec2-runner'}):
        result = fleet_ops_module.create_fleet_launch_template({
            'ami_id': 'ami-test',
            'security_group_id': 'sg-test',
            'iam_instance_profile': 'test-profile',
            'user_data_base64': 'dGVzdA==',
            'job_id': 123,
            'job_labels': ['ec2'],
            'github_repo': 'test/repo',
            'run_id': 456,
            'runner_type': 'ec2'
        })
    assert result == 'lt-test123'


@patch('fleet_ops.get_ec2_client')
def test_create_fleet_launch_template_error_raises(mock_get_client, fleet_ops_module):
    """Test create_fleet_launch_template raises on error."""
    mock_ec2 = MagicMock()
    mock_ec2.create_launch_template.side_effect = ClientError(
        {'Error': {'Code': 'InvalidParameter'}}, 'CreateLaunchTemplate'
    )
    mock_get_client.return_value = mock_ec2
    with patch.dict('os.environ', {'EC2_MANAGED_BY_TAG': 'api-ec2-runner'}):
        with pytest.raises(ClientError):
            fleet_ops_module.create_fleet_launch_template({
                'ami_id': 'ami-test',
                'security_group_id': 'sg-test',
                'iam_instance_profile': 'test-profile',
                'user_data_base64': 'dGVzdA==',
                'job_id': 123,
                'job_labels': ['ec2'],
                'github_repo': 'test/repo',
                'run_id': 456,
                'runner_type': 'ec2'
            })


def test_build_ec2_template_config_has_runner_name(fleet_ops_module):
    """Test _build_ec2_template_config creates correct runner name."""
    cfg = {
        'run_id': 123, 'job_id': 456, 'registration_token': 'test-token',
        'job_labels': ['ec2'], 'github_repo': 'test/repo', 'ami_id': 'ami-test',
        'runner_type': 'ec2'
    }
    ec2_config = {'security_group_id': 'sg-test', 'iam_instance_profile': 'test-profile'}
    result = fleet_ops_module._build_ec2_template_config(cfg, ec2_config)
    assert result['runner_name'] == 'ec2-runner-123'


def test_build_ec2_template_config_no_run_id(fleet_ops_module):
    """Test _build_ec2_template_config uses job_id when no run_id."""
    cfg = {
        'run_id': None, 'job_id': 456, 'registration_token': 'test-token',
        'job_labels': ['ec2'], 'github_repo': 'test/repo', 'ami_id': 'ami-test',
        'runner_type': 'ec2'
    }
    ec2_config = {'security_group_id': 'sg-test', 'iam_instance_profile': 'test-profile'}
    result = fleet_ops_module._build_ec2_template_config(cfg, ec2_config)
    assert result['runner_name'] == 'ec2-runner-456'


def test_get_instance_type_from_labels_valid(fleet_ops_module):
    """Test _get_instance_type_from_labels extracts instance type."""
    result = fleet_ops_module._get_instance_type_from_labels(
        ['ec2', 'general-purpose', 'intel', 'spot', 'runner-12345']
    )
    assert result is not None


def test_get_instance_type_from_labels_invalid(fleet_ops_module):
    """Test _get_instance_type_from_labels returns None for invalid labels."""
    result = fleet_ops_module._get_instance_type_from_labels(['invalid-label'])
    assert result is None


def test_is_spot_from_labels_default_spot(fleet_ops_module):
    """Test _is_spot_from_labels returns True by default."""
    result = fleet_ops_module._is_spot_from_labels(['ec2', 'ephemeral-ec2-instance'])
    assert result is True


def test_is_spot_from_labels_on_demand(fleet_ops_module):
    """Test _is_spot_from_labels returns False for on-demand."""
    result = fleet_ops_module._is_spot_from_labels(
        ['ec2', 'general-purpose', 'intel', 'on-demand', 'runner-12345']
    )
    assert result is False


def test_is_spot_from_labels_invalid_returns_spot(fleet_ops_module):
    """Test _is_spot_from_labels defaults to spot for invalid labels."""
    result = fleet_ops_module._is_spot_from_labels(['invalid-label'])
    assert result is True


@pytest.fixture
def fleet_launch_mocks(fleet_ops_module):
    """Fixture providing common mocks for fleet launch tests."""
    with patch('fleet_ops.get_ec2_config') as mock_config, \
         patch('fleet_ops._build_ec2_template_config') as mock_build, \
         patch('fleet_ops._get_fleet_instance_config') as mock_fleet_config, \
         patch('fleet_ops.create_fleet_launch_template') as mock_create_template, \
         patch('fleet_ops._create_fleet_request') as mock_create_fleet, \
         patch('fleet_ops.delete_launch_template') as mock_delete:
        mock_config.return_value = {
            'subnet_ids': ['subnet-1'], 'security_group_id': 'sg-1',
            'instance_types': ['t3.small'], 'iam_instance_profile': 'profile'
        }
        mock_build.return_value = {'ami_id': 'ami-test'}
        mock_fleet_config.return_value = (['t3.small'], True, 'spot')
        mock_create_template.return_value = 'lt-test'
        yield {
            'config': mock_config, 'build': mock_build, 'fleet_config': mock_fleet_config,
            'create_template': mock_create_template, 'create_fleet': mock_create_fleet,
            'delete': mock_delete
        }


def test_try_launch_ec2_fleet_success(fleet_ops_module, fleet_launch_mocks):
    """Test _try_launch_ec2_fleet returns success when fleet launches."""
    fleet_launch_mocks['create_fleet'].return_value = {'Instances': [{'InstanceIds': ['i-test']}]}
    with patch('fleet_ops.wait_for_instance_describable') as mock_wait, \
         patch('fleet_ops._handle_ec2_fleet_success') as mock_success:
        mock_wait.return_value = {'InstanceId': 'i-test', 'InstanceType': 't3.small',
                                   'Placement': {'AvailabilityZone': 'us-east-2a'}}
        mock_success.return_value = {'success': True, 'instance_id': 'i-test'}
        result = fleet_ops_module._try_launch_ec2_fleet({'job_id': 123, 'job_labels': []})
        assert result['success'] is True


def test_try_launch_ec2_fleet_client_error(fleet_ops_module, fleet_launch_mocks):
    """Test _try_launch_ec2_fleet handles ClientError."""
    fleet_launch_mocks['create_fleet'].side_effect = ClientError(
        {'Error': {'Code': 'InsufficientCapacity', 'Message': 'No capacity'}}, 'CreateFleet'
    )
    result = fleet_ops_module._try_launch_ec2_fleet({'job_id': 123, 'job_labels': []})
    assert result['success'] is False


def test_try_launch_ec2_fleet_empty_instances(fleet_ops_module, fleet_launch_mocks):
    """Test _try_launch_ec2_fleet handles empty instances response."""
    fleet_launch_mocks['create_fleet'].return_value = {
        'Instances': [], 'Errors': [{'ErrorMessage': 'No capacity available'}]
    }
    result = fleet_ops_module._try_launch_ec2_fleet({'job_id': 123, 'job_labels': []})
    assert 'No capacity available' in result['error']


def test_try_launch_ec2_fleet_no_instance_ids(fleet_ops_module, fleet_launch_mocks):
    """Test _try_launch_ec2_fleet handles empty InstanceIds."""
    fleet_launch_mocks['create_fleet'].return_value = {'Instances': [{'InstanceIds': []}]}
    result = fleet_ops_module._try_launch_ec2_fleet({'job_id': 123, 'job_labels': []})
    assert 'No instances launched' in result['error']
