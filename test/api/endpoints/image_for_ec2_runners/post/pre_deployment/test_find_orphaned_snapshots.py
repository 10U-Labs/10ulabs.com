class TestFindOrphanedSnapshotsReturnsOrphanedSet:

    def test_returns_empty_set_when_no_snapshots(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {'Snapshots': []}

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()

    def test_returns_orphaned_snapshot_when_ami_does_not_exist(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [
                {
                    'SnapshotId': 'snap-orphaned',
                    'Description': 'Created by CreateImage(i-xxx) for ami-deleted'
                }
            ]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == {'snap-orphaned'}

    def test_does_not_return_snapshot_when_ami_exists(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [{'ImageId': 'ami-0abc123def456789a'}]
        }
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [
                {
                    'SnapshotId': 'snap-inuse',
                    'Description': 'Created by CreateImage(i-xxx) for ami-0abc123def456789a'
                }
            ]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == set()

    def test_skips_protected_snapshots(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [
                {
                    'SnapshotId': 'snap-protected',
                    'Description': 'Created by CreateImage(i-xxx) for ami-deleted'
                }
            ]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, {'snap-protected'})

        assert result == set()

    def test_returns_only_orphaned_from_mixed_set(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [{'ImageId': 'ami-0abc123def456789a'}]
        }
        mock_ec2_client.describe_snapshots.return_value = {
            'Snapshots': [
                {
                    'SnapshotId': 'snap-inuse',
                    'Description': 'Created by CreateImage(i-xxx) for ami-0abc123def456789a'
                },
                {
                    'SnapshotId': 'snap-orphaned',
                    'Description': 'Created by CreateImage(i-yyy) for ami-1def456789abcdef0'
                }
            ]
        }

        result = cleanup.find_orphaned_snapshots(mock_ec2_client, set())

        assert result == {'snap-orphaned'}
