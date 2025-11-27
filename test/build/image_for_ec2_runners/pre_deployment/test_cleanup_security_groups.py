from botocore.exceptions import ClientError


class TestCleanupSecurityGroupsReturnsDeletedCount:

    def test_returns_zero_when_no_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}

        result = cleanup.cleanup_security_groups(mock_ec2_client, False)

        assert result == 0

    def test_returns_count_of_deleted_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_security_groups(mock_ec2_client, False)

        assert result == 2


class TestCleanupSecurityGroupsCallsDeleteSecurityGroup:

    def test_calls_delete_security_group_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'ami-builder-test'}]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, False)

        mock_ec2_client.delete_security_group.assert_called_once_with(GroupId='sg-123')

    def test_calls_delete_for_multiple_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, False)

        assert mock_ec2_client.delete_security_group.call_count == 2


class TestCleanupSecurityGroupsDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'ami-builder-test'}]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, True)

        mock_ec2_client.delete_security_group.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_security_groups(mock_ec2_client, True)

        assert result == 2


class TestCleanupSecurityGroupsDependencyViolation:

    def test_continues_on_dependency_violation(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }
        mock_ec2_client.delete_security_group.side_effect = [
            ClientError({'Error': {'Code': 'DependencyViolation'}}, 'delete_security_group'),
            None
        ]

        result = cleanup.cleanup_security_groups(mock_ec2_client, False)

        assert result == 1
