from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError


class TestGetLatestAmiDetails:

    def test_returns_full_details_with_success(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2
            v1_handler.ec2 = mock_ec2
            v1_handler.ssm = mock_ssm

            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
            )

            mock_ec2.describe_images.return_value = {
                'Images': [{
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'CreationDate': '2024-01-01T00:00:00.000Z',
                    'State': 'available',
                    'Architecture': 'arm64',
                    'Tags': [{'Key': 'stable', 'Value': 'true'}]
                }]
            }

            result = v1_handler.get_latest_ami_details()

            assert result['success'] is True

    def test_returns_full_details_with_ami_id(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2
            v1_handler.ec2 = mock_ec2
            v1_handler.ssm = mock_ssm

            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
            )

            mock_ec2.describe_images.return_value = {
                'Images': [{
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'CreationDate': '2024-01-01T00:00:00.000Z',
                    'State': 'available',
                    'Architecture': 'arm64',
                    'Tags': [{'Key': 'stable', 'Value': 'true'}]
                }]
            }

            result = v1_handler.get_latest_ami_details()

            assert result['ami_id'] == 'ami-123'

    def test_returns_error_when_no_ami_returns_failure(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2
            v1_handler.ec2 = mock_ec2
            v1_handler.ssm = mock_ssm

            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
            )

            mock_ec2.describe_images.return_value = {'Images': []}

            result = v1_handler.get_latest_ami_details()

            assert result['success'] is False

    def test_returns_error_when_no_ami_has_error_message(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2
            v1_handler.ec2 = mock_ec2
            v1_handler.ssm = mock_ssm

            mock_ssm.get_parameter.side_effect = ClientError(
                {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
            )

            mock_ec2.describe_images.return_value = {'Images': []}

            result = v1_handler.get_latest_ami_details()

            assert 'No available AMI found' in result['error']
