from botocore.exceptions import ClientError

TAGS = {'Purpose': 'GitHub self-hosted EC2 runner'}
EXCLUDE_TAGS = {}


class TestCleanupSecurityGroupsReturnsDeletedCount:

    def test_returns_zero_when_no_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_returns_count_of_deleted_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 2


class TestCleanupSecurityGroupsCallsDeleteSecurityGroup:

    def test_calls_delete_security_group_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'ami-builder-test'}]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.delete_security_group.assert_called_once_with(GroupId='sg-123')

    def test_calls_delete_for_multiple_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert mock_ec2_client.delete_security_group.call_count == 2


class TestCleanupSecurityGroupsDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'ami-builder-test'}]
        }

        cleanup.cleanup_security_groups(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.delete_security_group.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {'GroupId': 'sg-123', 'GroupName': 'ami-builder-test1'},
                {'GroupId': 'sg-456', 'GroupName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_security_groups(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        assert result == 2

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

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 1


class TestCleanupSecurityGroupsFiltersByTag:

    def test_filters_by_tag_key_and_value(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}

        cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.describe_security_groups.assert_called_once()
        call_args = mock_ec2_client.describe_security_groups.call_args
        filters = call_args[1]['Filters']
        tag_filter = filters[0]
        assert tag_filter['Name'] == 'tag:Purpose'
        assert tag_filter['Values'] == ['GitHub self-hosted EC2 runner']

    def test_uses_filters_keyword_argument(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}

        cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        call_args = mock_ec2_client.describe_security_groups.call_args
        assert 'Filters' in call_args[1]


class TestCleanupSecurityGroupsExcludeTags:

    def test_skips_security_group_with_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{
                'GroupId': 'sg-123',
                'GroupName': 'protected-sg',
                'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 0

    def test_does_not_delete_security_group_with_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{
                'GroupId': 'sg-123',
                'GroupName': 'protected-sg',
                'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, exclude_tags)

        mock_ec2_client.delete_security_group.assert_not_called()

    def test_deletes_security_group_without_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [{
                'GroupId': 'sg-123',
                'GroupName': 'ephemeral-sg',
                'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1

    def test_deletes_only_non_protected_security_groups(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'GroupId': 'sg-123',
                    'GroupName': 'protected-sg',
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
                },
                {
                    'GroupId': 'sg-456',
                    'GroupName': 'ephemeral-sg',
                    'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
                }
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1
