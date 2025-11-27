from botocore.exceptions import ClientError


class TestCleanupKeyPairsReturnsDeletedCount:

    def test_returns_zero_when_no_key_pairs(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {'KeyPairs': []}

        result = cleanup.cleanup_key_pairs(mock_ec2_client, False)

        assert result == 0

    def test_returns_count_of_deleted_key_pairs(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [
                {'KeyName': 'ami-builder-abc123'},
                {'KeyName': 'ami-builder-def456'}
            ]
        }

        result = cleanup.cleanup_key_pairs(mock_ec2_client, False)

        assert result == 2


class TestCleanupKeyPairsCallsDeleteKeyPair:

    def test_calls_delete_key_pair_for_each_name(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{'KeyName': 'ami-builder-abc123'}]
        }

        cleanup.cleanup_key_pairs(mock_ec2_client, False)

        mock_ec2_client.delete_key_pair.assert_called_once_with(KeyName='ami-builder-abc123')

    def test_calls_delete_for_multiple_key_pairs(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [
                {'KeyName': 'ami-builder-abc123'},
                {'KeyName': 'ami-builder-def456'}
            ]
        }

        cleanup.cleanup_key_pairs(mock_ec2_client, False)

        assert mock_ec2_client.delete_key_pair.call_count == 2


class TestCleanupKeyPairsDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [{'KeyName': 'ami-builder-abc123'}]
        }

        cleanup.cleanup_key_pairs(mock_ec2_client, True)

        mock_ec2_client.delete_key_pair.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [
                {'KeyName': 'ami-builder-abc123'},
                {'KeyName': 'ami-builder-def456'}
            ]
        }

        result = cleanup.cleanup_key_pairs(mock_ec2_client, True)

        assert result == 2


class TestCleanupKeyPairsClientError:

    def test_continues_on_client_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {
            'KeyPairs': [
                {'KeyName': 'ami-builder-abc123'},
                {'KeyName': 'ami-builder-def456'}
            ]
        }
        mock_ec2_client.delete_key_pair.side_effect = [
            ClientError({'Error': {'Code': 'InvalidKeyPair.NotFound'}}, 'delete_key_pair'),
            None
        ]

        result = cleanup.cleanup_key_pairs(mock_ec2_client, False)

        assert result == 1
