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
