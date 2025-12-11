"""Unit tests for get_latest_ami_id functionality."""
from botocore.exceptions import ClientError


class TestGetLatestAmiIdSuccess:
    """Tests for get_latest_ami_id when successfully retrieving AMI ID from SSM."""

    def test_returns_ami_id_when_parameter_exists(self, cleanup, mock_ec2_client):
        """Test that AMI ID is returned when SSM parameter exists."""
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'ami-123456789'}}

        result = cleanup.get_latest_ami_id(mock_ssm, '/ami/ec2-runner/latest')

        assert result == 'ami-123456789'

    def test_calls_get_parameter_with_correct_name(self, cleanup, mock_ec2_client):
        """Test that get_parameter is called with the correct parameter name."""
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'ami-123'}}

        cleanup.get_latest_ami_id(mock_ssm, '/my/parameter/name')

        mock_ssm.get_parameter.assert_called_once_with(Name='/my/parameter/name')

    def test_returns_none_when_parameter_not_found(self, cleanup, mock_ec2_client):
        """Test that None is returned when SSM parameter is not found."""
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/ami/ec2-runner/latest')

        assert result is None

    def test_returns_none_on_other_client_error(self, cleanup, mock_ec2_client):
        """Test that None is returned on other client errors."""
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'get_parameter'
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/ami/ec2-runner/latest')

        assert result is None
