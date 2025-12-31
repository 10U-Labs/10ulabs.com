"""Unit tests for promote_ami functionality."""
import inspect
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError


class TestPromoteAmiFunction:
    """Tests for promote_ami function signature and existence."""

    def test_function_exists(self, promote_ami):
        """Test that promote_ami function exists."""
        assert hasattr(promote_ami, "promote_ami")

    def test_signature_has_ami_id(self, promote_ami):
        """Test that function signature includes ami_id parameter."""
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "ami_id" in params

    def test_signature_has_region(self, promote_ami):
        """Test that function signature includes region parameter."""
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "region" in params

    def test_signature_has_tag_key(self, promote_ami):
        """Test that function signature includes tag_key parameter."""
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "tag_key" in params


class TestPromoteAmi:
    """Tests for promote_ami when promoting AMIs to stable."""

    def test_successful_ami_promotion_calls_create_tags(self, promote_ami):
        """Test that create_tags is called when promoting AMI."""
        mock_ec2 = MagicMock()

        def client_side_effect(service, **_kwargs):
            return mock_ec2

        with patch('boto3.client', side_effect=client_side_effect):
            promote_ami.promote_ami('ami-123', 'us-east-1', 'stable')

            mock_ec2.create_tags.assert_called_once_with(
                Resources=['ami-123'],
                Tags=[{'Key': 'stable', 'Value': 'true'}]
            )

    def test_successful_ami_promotion_returns_zero(self, promote_ami):
        """Test that successful AMI promotion returns exit code 0."""
        mock_ec2 = MagicMock()

        def client_side_effect(service, **_kwargs):
            return mock_ec2

        with patch('boto3.client', side_effect=client_side_effect):
            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'stable')

            assert result == 0

    def test_ec2_tag_failure(self, promote_ami):
        """Test that EC2 tag failure returns exit code 1."""
        mock_ec2 = MagicMock()
        mock_ec2.create_tags.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterValue'}}, 'create_tags'
        )

        def client_side_effect(service, **_kwargs):
            return mock_ec2

        with patch('boto3.client', side_effect=client_side_effect):
            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'stable')

            assert result == 1
