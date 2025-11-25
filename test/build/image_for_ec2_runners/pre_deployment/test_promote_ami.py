import inspect
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError


class TestPromoteAmiFunction:

    def test_function_exists(self, promote_ami):
        assert hasattr(promote_ami, "promote_ami")

    def test_signature_has_ami_id(self, promote_ami):
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "ami_id" in params

    def test_signature_has_region(self, promote_ami):
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "region" in params

    def test_signature_has_ssm_parameter_name(self, promote_ami):
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "ssm_parameter_name" in params

    def test_signature_has_tag_key(self, promote_ami):
        sig = inspect.signature(promote_ami.promote_ami)
        params = list(sig.parameters.keys())

        assert "tag_key" in params


class TestPromoteAmi:

    def test_successful_ami_promotion_calls_create_tags(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456', '/github-runner/ami/latest', 'stable')

            mock_ec2.create_tags.assert_called_once_with(
                Resources=['ami-123'],
                Tags=[{'Key': 'stable', 'Value': 'true'}]
            )

    def test_successful_ami_promotion_calls_put_parameter(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456', '/github-runner/ami/latest', 'stable')

            mock_ssm.put_parameter.assert_called_once_with(
                Name='/github-runner/ami/latest',
                Value='ami-123',
                Type='String',
                Overwrite=True,
                Description='Latest stable GitHub runner AMI (updated by workflow run run-456)'
            )

    def test_successful_ami_promotion_returns_zero(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456', '/github-runner/ami/latest', 'stable')

            assert result == 0

    def test_ec2_tag_failure(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            mock_ec2.create_tags.side_effect = ClientError(
                {'Error': {'Code': 'InvalidParameterValue'}}, 'create_tags'
            )

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456', '/github-runner/ami/latest', 'stable')

            assert result == 1

    def test_ssm_parameter_failure(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            mock_ssm.put_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterAlreadyExists'}}, 'put_parameter'
            )

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456', '/github-runner/ami/latest', 'stable')

            assert result == 1
