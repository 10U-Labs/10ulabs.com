"""Unit tests for ec2_utils module."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import load_lambda_module


@pytest.fixture(name="ec2_utils_module")
def ec2_utils_module_fixture():
    """Load ec2_utils module for testing."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        module = load_lambda_module("common/ec2_utils.py", "ec2_utils")
        yield module


class TestTerminateEc2Instance:
    """Tests for terminate_ec2_instance function."""

    def test_terminates_instance_successfully(self, ec2_utils_module):
        """Test successful instance termination."""
        mock_ec2 = MagicMock()
        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.terminate_ec2_instance("i-1234567890abcdef0")
            assert result is True
            mock_ec2.terminate_instances.assert_called_once_with(
                InstanceIds=["i-1234567890abcdef0"]
            )

    def test_returns_true_when_instance_not_found(self, ec2_utils_module):
        """Test returns True when instance not found."""
        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Not found"}},
            "TerminateInstances"
        )
        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.terminate_ec2_instance("i-nonexistent")
            assert result is True

    def test_returns_true_when_instance_id_malformed(self, ec2_utils_module):
        """Test returns True when instance ID is malformed."""
        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.Malformed", "Message": "Malformed"}},
            "TerminateInstances"
        )
        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.terminate_ec2_instance("invalid-id")
            assert result is True

    def test_returns_false_on_other_client_error(self, ec2_utils_module):
        """Test returns False on other ClientError."""
        mock_ec2 = MagicMock()
        mock_ec2.terminate_instances.side_effect = ClientError(
            {"Error": {"Code": "UnauthorizedOperation", "Message": "Unauthorized"}},
            "TerminateInstances"
        )
        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.terminate_ec2_instance("i-1234567890abcdef0")
            assert result is False


class TestFindInstancesByTags:
    """Tests for find_instances_by_tags function."""

    def test_finds_instances_successfully(self, ec2_utils_module):
        """Test successful instance lookup."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-123"}, {"InstanceId": "i-456"}]},
                {"Instances": [{"InstanceId": "i-789"}]}
            ]
        }
        filters = [{"Name": "tag:Environment", "Values": ["test"]}]

        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.find_instances_by_tags(filters)
            assert len(result) == 3
            assert result[0]["InstanceId"] == "i-123"
            assert result[1]["InstanceId"] == "i-456"
            assert result[2]["InstanceId"] == "i-789"
            mock_ec2.describe_instances.assert_called_once_with(Filters=filters)

    def test_returns_empty_list_when_no_instances(self, ec2_utils_module):
        """Test returns empty list when no instances found."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}
        filters = [{"Name": "tag:Name", "Values": ["nonexistent"]}]

        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.find_instances_by_tags(filters)
            assert result == []

    def test_returns_empty_list_on_client_error(self, ec2_utils_module):
        """Test returns empty list on ClientError."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidFilter", "Message": "Invalid filter"}},
            "DescribeInstances"
        )
        filters = [{"Name": "invalid", "Values": ["test"]}]

        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.find_instances_by_tags(filters)
            assert result == []

    def test_handles_empty_instances_in_reservation(self, ec2_utils_module):
        """Test handling when reservation has empty Instances list."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {"Instances": []},
                {"Instances": [{"InstanceId": "i-123"}]}
            ]
        }
        filters = [{"Name": "tag:Name", "Values": ["test"]}]

        with patch.object(ec2_utils_module, 'get_ec2_client', return_value=mock_ec2):
            result = ec2_utils_module.find_instances_by_tags(filters)
            assert len(result) == 1
            assert result[0]["InstanceId"] == "i-123"
