"""Unit tests for get_existing_ami_ids functionality."""
from botocore.exceptions import ClientError


class TestGetExistingAmiIdsSuccess:
    """Tests for get_existing_ami_ids when successfully retrieving AMI IDs."""

    def test_returns_set_of_ami_ids(self, cleanup, mock_ec2_client):
        """Test that multiple AMI IDs are returned as a set."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-123'},
                {'ImageId': 'ami-456'}
            ]
        }

        result = cleanup.get_existing_ami_ids(mock_ec2_client)

        assert result == {'ami-123', 'ami-456'}

    def test_returns_single_ami_id(self, cleanup, mock_ec2_client):
        """Test that a single AMI ID is returned as a set."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [{'ImageId': 'ami-123'}]
        }

        result = cleanup.get_existing_ami_ids(mock_ec2_client)

        assert result == {'ami-123'}

    def test_calls_describe_images_with_self_owner(self, cleanup, mock_ec2_client):
        """Test that describe_images is called with 'self' as owner."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        cleanup.get_existing_ami_ids(mock_ec2_client)

        mock_ec2_client.describe_images.assert_called_once_with(Owners=['self'])
        assert True  # Explicit pass

    def test_returns_empty_set_when_no_amis(self, cleanup, mock_ec2_client):
        """Test that an empty set is returned when no AMIs are found."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        result = cleanup.get_existing_ami_ids(mock_ec2_client)

        assert result == set()

    def test_returns_empty_set_on_client_error(self, cleanup, mock_ec2_client):
        """Test that an empty set is returned when a client error occurs."""
        mock_ec2_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation'}}, 'describe_images'
        )

        result = cleanup.get_existing_ami_ids(mock_ec2_client)

        assert result == set()
