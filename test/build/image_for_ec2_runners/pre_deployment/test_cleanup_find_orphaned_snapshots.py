from botocore.exceptions import ClientError


class TestFindOrphanedSnapshotsNoOrphans:

    def test_returns_empty_set_when_no_snapshots(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {'Snapshots': []}

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()

    def test_returns_empty_when_ami_still_exists(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [{'ImageId': 'ami-abcd1234'}]
        }
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [{
                'SnapshotId': 'snap-123',
                'Description': 'Created by CreateImage(i-123) for ami-abcd1234'
            }]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()


class TestFindOrphanedSnapshotsFindsOrphans:

    def test_finds_orphaned_snapshot(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [{
                'SnapshotId': 'snap-123',
                'Description': 'Created by CreateImage(i-123) for ami-deleted'
            }]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == {'snap-123'}

    def test_finds_multiple_orphaned_snapshots(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [
                {'SnapshotId': 'snap-123', 'Description': 'Created by CreateImage(i-123) for ami-deleted1'},
                {'SnapshotId': 'snap-456', 'Description': 'Created by CreateImage(i-456) for ami-deleted2'}
            ]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == {'snap-123', 'snap-456'}

    def test_skips_snapshots_in_protected_set(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [{
                'SnapshotId': 'snap-protected',
                'Description': 'Created by CreateImage(i-123) for ami-deleted'
            }]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, {'snap-protected'})

        assert result == set()


class TestFindOrphanedSnapshotsEdgeCases:

    def test_skips_snapshot_without_ami_id_in_description(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [{
                'SnapshotId': 'snap-123',
                'Description': 'Manual snapshot'
            }]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()

    def test_skips_snapshot_with_empty_description(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [{
                'SnapshotId': 'snap-123',
                'Description': ''
            }]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()

    def test_returns_empty_set_on_describe_snapshots_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DescribeSnapshots'
        )

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()
