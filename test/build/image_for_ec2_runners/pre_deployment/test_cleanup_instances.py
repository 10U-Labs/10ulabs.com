from botocore.exceptions import ClientError


class TestCleanupInstancesReturnsDeletedCount:

    def test_returns_zero_when_no_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}

        result = cleanup.cleanup_instances(mock_ec2_client, False)

        assert result == 0

    def test_returns_count_of_terminated_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, False)

        assert result == 2


class TestCleanupInstancesCallsTerminateInstances:

    def test_calls_terminate_instances_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]
        }

        cleanup.cleanup_instances(mock_ec2_client, False)

        mock_ec2_client.terminate_instances.assert_called_once_with(InstanceIds=['i-123'])

    def test_calls_terminate_for_multiple_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        cleanup.cleanup_instances(mock_ec2_client, False)

        assert mock_ec2_client.terminate_instances.call_count == 2


class TestCleanupInstancesMultipleReservations:

    def test_handles_multiple_reservations(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-123'}]},
                {'Instances': [{'InstanceId': 'i-456'}]}
            ]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, False)

        assert result == 2


class TestCleanupInstancesDryRun:

    def test_dry_run_does_not_terminate(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]
        }

        cleanup.cleanup_instances(mock_ec2_client, True)

        mock_ec2_client.terminate_instances.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, True)

        assert result == 2


class TestCleanupInstancesClientError:

    def test_continues_on_client_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }
        mock_ec2_client.terminate_instances.side_effect = [
            ClientError({'Error': {'Code': 'InvalidInstanceID.NotFound'}}, 'terminate_instances'),
            None
        ]

        result = cleanup.cleanup_instances(mock_ec2_client, False)

        assert result == 1
