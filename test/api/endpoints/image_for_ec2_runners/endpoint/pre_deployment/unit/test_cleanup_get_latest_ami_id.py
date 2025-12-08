"""Unit tests for get_latest_ami_id functionality."""

from unittest.mock import MagicMock
from botocore.exceptions import ClientError


class TestGetLatestAmiIdSuccess:
    """Tests for get_latest_ami_id when successful."""

    def test_returns_ami_id_from_ssm(self, cleanup):
        """Test that AMI ID is returned from SSM parameter."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'ami-12345678'}
        }

        result = cleanup.get_latest_ami_id(mock_ssm, '/ec2/runner/ami-id')

        assert result == 'ami-12345678'

    def test_calls_ssm_with_correct_parameter_name(self, cleanup):
        """Test that SSM is called with correct parameter name."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'ami-12345678'}
        }

        cleanup.get_latest_ami_id(mock_ssm, '/my/custom/param')

        mock_ssm.get_parameter.assert_called_once_with(
            Name='/my/custom/param'
        )


class TestGetLatestAmiIdClientErrors:
    """Tests for get_latest_ami_id when client errors occur."""

    def test_returns_none_when_parameter_not_found(self, cleanup):
        """Test that None is returned when parameter not found."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'ParameterNotFound',
                    'Message': 'Parameter not found',
                }
            },
            'GetParameter',
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/missing/param')

        assert result is None

    def test_returns_none_on_access_denied_error(self, cleanup):
        """Test that None is returned on access denied error."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied',
                }
            },
            'GetParameter',
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/secure/param')

        assert result is None
