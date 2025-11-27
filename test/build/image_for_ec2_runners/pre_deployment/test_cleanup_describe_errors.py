from botocore.exceptions import ClientError

TAGS = {'Purpose': 'test'}
EXCLUDE_TAGS = {}


class TestCleanupAmisDescribeError:

    def test_returns_zero_count_on_describe_error(self, cleanup, mock_ec2_client, make_ami_cleanup_params):
        mock_ec2_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeImages'
        )

        count, _ = cleanup.cleanup_amis(mock_ec2_client, make_ami_cleanup_params(cleanup, tags=TAGS))

        assert count == 0

    def test_returns_empty_snapshots_on_describe_error(self, cleanup, mock_ec2_client, make_ami_cleanup_params):
        mock_ec2_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeImages'
        )

        _, snapshots = cleanup.cleanup_amis(mock_ec2_client, make_ami_cleanup_params(cleanup, tags=TAGS))

        assert snapshots == set()


class TestCleanupResourcesDescribeErrors:

    def test_instances_returns_zero_on_describe_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeInstances'
        )

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_security_groups_returns_zero_on_describe_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeSecurityGroups'
        )

        result = cleanup.cleanup_security_groups(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_key_pairs_returns_zero_on_describe_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeKeyPairs'
        )

        result = cleanup.cleanup_key_pairs(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_launch_templates_returns_zero_on_describe_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeLaunchTemplates'
        )

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_snapshots_continues_on_delete_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.delete_snapshot.side_effect = [
            ClientError({'Error': {'Code': 'InvalidSnapshot.InUse', 'Message': 'In use'}}, 'DeleteSnapshot'),
            None
        ]

        result = cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, False)

        assert result == 1
