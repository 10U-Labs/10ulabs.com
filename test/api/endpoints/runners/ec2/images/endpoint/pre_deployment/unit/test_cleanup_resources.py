"""Unit tests for cleanup resource functions.

Tests for cleanup_security_groups, cleanup_key_pairs,
cleanup_instances, and cleanup_launch_templates.
"""
from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError


class TestCleanupSecurityGroups:
    """Tests for cleanup_security_groups function."""

    def test_deletes_matching_security_group(self, cleanup, mock_ec2_client):
        """Verify deletes security group matching tags."""
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test-sg'}]
        }
        mock_ec2_client.delete_security_group.return_value = {}

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_security_group.assert_called_once_with(GroupId='sg-123')

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        """Verify dry run doesn't actually delete."""
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test-sg'}]
        }

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=True,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_security_group.assert_not_called()

    def test_skips_excluded_security_groups(self, cleanup, mock_ec2_client):
        """Verify skips security groups with excluded tags."""
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{
                'GroupId': 'sg-123',
                'GroupName': 'protected-sg',
                'Tags': [{'Key': 'Protected', 'Value': 'true'}]
            }]
        }

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={'Protected': 'true'}
        )

        assert result == 0
        mock_ec2_client.delete_security_group.assert_not_called()

    def test_handles_dependency_violation(self, cleanup, mock_ec2_client):
        """Verify handles DependencyViolation error gracefully."""
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'in-use-sg'}]
        }
        mock_ec2_client.delete_security_group.side_effect = ClientError(
            {'Error': {'Code': 'DependencyViolation', 'Message': 'In use'}},
            'DeleteSecurityGroup'
        )

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_other_delete_errors(self, cleanup, mock_ec2_client):
        """Verify handles other delete errors gracefully."""
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test-sg'}]
        }
        mock_ec2_client.delete_security_group.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DeleteSecurityGroup'
        )

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_describe_error(self, cleanup, mock_ec2_client):
        """Verify handles describe_security_groups error gracefully."""
        mock_ec2_client.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeSecurityGroups'
        )

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_multiple_tags(self, cleanup, mock_ec2_client):
        """Verify handles multiple tag filters."""
        mock_ec2_client.describe_security_groups.side_effect = [
            {'SecurityGroups': [{'GroupId': 'sg-1', 'GroupName': 'sg1'}]},
            {'SecurityGroups': [{'GroupId': 'sg-2', 'GroupName': 'sg2'}]},
        ]
        mock_ec2_client.delete_security_group.return_value = {}

        result = cleanup.cleanup_security_groups(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test', 'Env': 'dev'}, exclude_tags={}
        )

        assert result == 2


class TestCleanupKeyPairs:
    """Tests for cleanup_key_pairs function."""

    def test_deletes_matching_key_pair(self, cleanup, mock_ec2_client):
        """Verify deletes key pair matching tags."""
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{'KeyName': 'test-key'}]
        }
        mock_ec2_client.delete_key_pair.return_value = {}

        result = cleanup.cleanup_key_pairs(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_key_pair.assert_called_once_with(KeyName='test-key')

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        """Verify dry run doesn't actually delete."""
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{'KeyName': 'test-key'}]
        }

        result = cleanup.cleanup_key_pairs(
            mock_ec2_client, dry_run=True,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_key_pair.assert_not_called()

    def test_skips_excluded_key_pairs(self, cleanup, mock_ec2_client):
        """Verify skips key pairs with excluded tags."""
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{
                'KeyName': 'protected-key',
                'Tags': [{'Key': 'Protected', 'Value': 'true'}]
            }]
        }

        result = cleanup.cleanup_key_pairs(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={'Protected': 'true'}
        )

        assert result == 0
        mock_ec2_client.delete_key_pair.assert_not_called()

    def test_handles_delete_error(self, cleanup, mock_ec2_client):
        """Verify handles delete error gracefully."""
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{'KeyName': 'test-key'}]
        }
        mock_ec2_client.delete_key_pair.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DeleteKeyPair'
        )

        result = cleanup.cleanup_key_pairs(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_describe_error(self, cleanup, mock_ec2_client):
        """Verify handles describe_key_pairs error gracefully."""
        mock_ec2_client.describe_key_pairs.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeKeyPairs'
        )

        result = cleanup.cleanup_key_pairs(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0


class TestCleanupInstances:
    """Tests for cleanup_instances function."""

    def test_terminates_matching_instance(self, cleanup, mock_ec2_client):
        """Verify terminates instance matching tags."""
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{'InstanceId': 'i-123'}]
            }]
        }
        mock_ec2_client.terminate_instances.return_value = {}

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.terminate_instances.assert_called_once_with(InstanceIds=['i-123'])

    def test_dry_run_does_not_terminate(self, cleanup, mock_ec2_client):
        """Verify dry run doesn't actually terminate."""
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{'InstanceId': 'i-123'}]
            }]
        }

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=True,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.terminate_instances.assert_not_called()

    def test_skips_excluded_instances(self, cleanup, mock_ec2_client):
        """Verify skips instances with excluded tags."""
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-123',
                    'Tags': [{'Key': 'Protected', 'Value': 'true'}]
                }]
            }]
        }

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={'Protected': 'true'}
        )

        assert result == 0
        mock_ec2_client.terminate_instances.assert_not_called()

    def test_handles_terminate_error(self, cleanup, mock_ec2_client):
        """Verify handles terminate error gracefully."""
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{'InstanceId': 'i-123'}]
            }]
        }
        mock_ec2_client.terminate_instances.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'TerminateInstances'
        )

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_describe_error(self, cleanup, mock_ec2_client):
        """Verify handles describe_instances error gracefully."""
        mock_ec2_client.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeInstances'
        )

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_multiple_reservations(self, cleanup, mock_ec2_client):
        """Verify handles multiple reservations."""
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-1'}]},
                {'Instances': [{'InstanceId': 'i-2'}, {'InstanceId': 'i-3'}]},
            ]
        }
        mock_ec2_client.terminate_instances.return_value = {}

        result = cleanup.cleanup_instances(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 3


class TestCleanupLaunchTemplates:
    """Tests for cleanup_launch_templates function."""

    def test_deletes_matching_launch_template(self, cleanup, mock_ec2_client):
        """Verify deletes launch template matching tags."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'test-template'
            }]
        }
        mock_ec2_client.delete_launch_template.return_value = {}

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_launch_template.assert_called_once_with(
            LaunchTemplateId='lt-123'
        )

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        """Verify dry run doesn't actually delete."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'test-template'
            }]
        }

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=True,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 1
        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_skips_excluded_launch_templates(self, cleanup, mock_ec2_client):
        """Verify skips launch templates with excluded tags."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'protected-template',
                'Tags': [{'Key': 'Protected', 'Value': 'true'}]
            }]
        }

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={'Protected': 'true'}
        )

        assert result == 0
        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_handles_delete_error(self, cleanup, mock_ec2_client):
        """Verify handles delete error gracefully."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'test-template'
            }]
        }
        mock_ec2_client.delete_launch_template.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DeleteLaunchTemplate'
        )

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_describe_error(self, cleanup, mock_ec2_client):
        """Verify handles describe_launch_templates error gracefully."""
        mock_ec2_client.describe_launch_templates.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeLaunchTemplates'
        )

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 0

    def test_handles_multiple_templates(self, cleanup, mock_ec2_client):
        """Verify handles multiple launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-1', 'LaunchTemplateName': 'template-1'},
                {'LaunchTemplateId': 'lt-2', 'LaunchTemplateName': 'template-2'},
            ]
        }
        mock_ec2_client.delete_launch_template.return_value = {}

        result = cleanup.cleanup_launch_templates(
            mock_ec2_client, dry_run=False,
            tags={'Purpose': 'test'}, exclude_tags={}
        )

        assert result == 2
