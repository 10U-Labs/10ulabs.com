"""Unit tests for get_latest_ami_details functionality."""


class TestGetLatestAmiDetails:
    """Tests for get_latest_ami_details when retrieving AMI information."""

    def test_returns_full_details_with_success(
        self, handler_module, mock_ec2_with_ami
    ):
        """Test that full AMI details are returned with success status."""
        _ = mock_ec2_with_ami  # Fixture sets up mocks
        result = handler_module.get_latest_ami_details()

        assert result['success'] is True

    def test_returns_full_details_with_ami_id(
        self, handler_module, mock_ec2_with_ami
    ):
        """Test that AMI ID is included in returned details."""
        _ = mock_ec2_with_ami  # Fixture sets up mocks
        result = handler_module.get_latest_ami_details()

        assert result['ami_id'] == 'ami-123'

    def test_returns_error_when_no_ami_returns_failure(
        self, handler_module, mock_ec2
    ):
        """Test that failure status is returned when no AMI is found."""
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler_module.get_latest_ami_details()

        assert result['success'] is False

    def test_returns_error_when_no_ami_has_error_message(
        self, handler_module, mock_ec2
    ):
        """Test that error message is included when no AMI is found."""
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler_module.get_latest_ami_details()

        assert 'No available AMI found' in result['error']
