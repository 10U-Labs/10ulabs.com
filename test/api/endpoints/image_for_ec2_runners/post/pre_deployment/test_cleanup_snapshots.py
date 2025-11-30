class TestCleanupSnapshotsReturnsDeletedCount:

    def test_returns_zero_when_no_snapshots(self, cleanup, mock_ec2_client):
        result = cleanup.cleanup_snapshots(mock_ec2_client, set(), False)

        assert result == 0

    def test_returns_count_of_deleted_snapshots(self, cleanup, mock_ec2_client):
        result = cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, False)

        assert result == 2


class TestCleanupSnapshotsCallsDeleteSnapshot:

    def test_calls_delete_snapshot_for_each_id(self, cleanup, mock_ec2_client):
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123'}, False)

        mock_ec2_client.delete_snapshot.assert_called_once_with(SnapshotId='snap-123')

    def test_calls_delete_snapshot_for_multiple_ids(self, cleanup, mock_ec2_client):
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, False)

        assert mock_ec2_client.delete_snapshot.call_count == 2


class TestCleanupSnapshotsDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123'}, True)

        mock_ec2_client.delete_snapshot.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        result = cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, True)

        assert result == 2
