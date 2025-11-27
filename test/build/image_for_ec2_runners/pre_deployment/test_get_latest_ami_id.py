from botocore.exceptions import ClientError


class TestGetLatestAmiIdSuccess:

    def test_returns_ami_id_when_parameter_exists(self, cleanup, mock_ec2_client):
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'ami-123456789'}}

        result = cleanup.get_latest_ami_id(mock_ssm, '/github-runner/ami/latest')

        assert result == 'ami-123456789'

    def test_calls_get_parameter_with_correct_name(self, cleanup, mock_ec2_client):
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'ami-123'}}

        cleanup.get_latest_ami_id(mock_ssm, '/my/parameter/name')

        mock_ssm.get_parameter.assert_called_once_with(Name='/my/parameter/name')


class TestGetLatestAmiIdParameterNotFound:

    def test_returns_none_when_parameter_not_found(self, cleanup, mock_ec2_client):
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'ParameterNotFound'}}, 'get_parameter'
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/github-runner/ami/latest')

        assert result is None


class TestGetLatestAmiIdClientError:

    def test_returns_none_on_other_client_error(self, cleanup, mock_ec2_client):
        mock_ssm = mock_ec2_client
        mock_ssm.get_parameter.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'get_parameter'
        )

        result = cleanup.get_latest_ami_id(mock_ssm, '/github-runner/ami/latest')

        assert result is None
