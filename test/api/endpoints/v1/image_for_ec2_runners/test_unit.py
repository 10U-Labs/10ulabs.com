from unittest.mock import Mock, MagicMock, patch, call
import urllib.error
import json
import pytest
from botocore.exceptions import ClientError


class TestWaitForStatusChecks:

    def test_get_imds_token_success(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'test-token-123'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = wait_for_status_checks.get_imds_token()

            assert token == 'test-token-123'
            mock_urlopen.assert_called_once()

    def test_get_imds_token_timeout(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            with pytest.raises(urllib.error.URLError):
                wait_for_status_checks.get_imds_token()

    def test_get_imds_token_http_error(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)

            with pytest.raises(urllib.error.HTTPError):
                wait_for_status_checks.get_imds_token()

    def test_get_metadata_success(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'i-1234567890'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = wait_for_status_checks.get_metadata('test-token', 'instance-id')

            assert result == 'i-1234567890'

    def test_get_metadata_different_paths(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'us-east-1a'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = wait_for_status_checks.get_metadata('test-token', 'placement/region')

            assert result == 'us-east-1a'

    def test_get_metadata_timeout(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            with pytest.raises(urllib.error.URLError):
                wait_for_status_checks.get_metadata('test-token', 'instance-id')

    def test_main_successful_completion(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch('subprocess.run') as mock_run:

            mock_token_response = Mock()
            mock_token_response.read.return_value = b'test-token'
            mock_token_response.__enter__ = Mock(return_value=mock_token_response)
            mock_token_response.__exit__ = Mock(return_value=False)

            mock_instance_response = Mock()
            mock_instance_response.read.return_value = b'i-123456'
            mock_instance_response.__enter__ = Mock(return_value=mock_instance_response)
            mock_instance_response.__exit__ = Mock(return_value=False)

            mock_region_response = Mock()
            mock_region_response.read.return_value = b'us-east-1'
            mock_region_response.__enter__ = Mock(return_value=mock_region_response)
            mock_region_response.__exit__ = Mock(return_value=False)

            mock_urlopen.side_effect = [mock_token_response, mock_instance_response, mock_region_response]

            mock_run_result = Mock()
            mock_run_result.returncode = 0
            mock_run_result.stdout = 'ok\tok'
            mock_run.return_value = mock_run_result

            result = wait_for_status_checks.main()

            assert result == 0

    def test_main_imds_token_failure(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('Connection failed')

            with pytest.raises(SystemExit) as exc_info:
                wait_for_status_checks.main()

            assert exc_info.value.code == 1

    def test_main_max_attempts_reached(self, wait_for_status_checks):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):

            mock_token_response = Mock()
            mock_token_response.read.return_value = b'test-token'
            mock_token_response.__enter__ = Mock(return_value=mock_token_response)
            mock_token_response.__exit__ = Mock(return_value=False)

            mock_instance_response = Mock()
            mock_instance_response.read.return_value = b'i-123456'
            mock_instance_response.__enter__ = Mock(return_value=mock_instance_response)
            mock_instance_response.__exit__ = Mock(return_value=False)

            mock_region_response = Mock()
            mock_region_response.read.return_value = b'us-east-1'
            mock_region_response.__enter__ = Mock(return_value=mock_region_response)
            mock_region_response.__exit__ = Mock(return_value=False)

            mock_urlopen.side_effect = [mock_token_response, mock_instance_response, mock_region_response]

            mock_run_result = Mock()
            mock_run_result.returncode = 0
            mock_run_result.stdout = 'initializing\tinitializing'
            mock_run.return_value = mock_run_result

            with pytest.raises(SystemExit) as exc_info:
                wait_for_status_checks.main()

            assert exc_info.value.code == 1


class TestGetEcConfig:

    def test_returns_correct_config_dict(self, v1_handler, mock_env_vars):
        config = v1_handler._get_ec2_config()

        assert 'subnet_ids' in config
        assert 'security_group_id' in config
        assert 'instance_types' in config
        assert 'iam_instance_profile' in config
        assert 'max_price' in config

    def test_subnet_ids_parsed_from_env(self, v1_handler, mock_env_vars):
        config = v1_handler._get_ec2_config()

        assert config['subnet_ids'] == ['subnet-123', 'subnet-456', 'subnet-789']

    def test_security_group_id_from_env(self, v1_handler, mock_env_vars):
        config = v1_handler._get_ec2_config()

        assert config['security_group_id'] == 'sg-12345'

    def test_instance_types_with_default(self, v1_handler):
        with patch.dict('os.environ', {'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1'}, clear=True):
            config = v1_handler._get_ec2_config()

            assert config['instance_types'] == ['t4g.large', 't4g.medium', 't4g.small']

    def test_iam_instance_profile_default(self, v1_handler, mock_env_vars):
        config = v1_handler._get_ec2_config()

        assert config['iam_instance_profile'] == 'TestInstanceProfile'

    def test_max_price_default(self, v1_handler, mock_env_vars):
        config = v1_handler._get_ec2_config()

        assert config['max_price'] == '0.10'


class TestGetRunnerRegistrationToken:

    def test_successful_token_retrieval(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'token': 'test-registration-token'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == 'test-registration-token'

    def test_http_error_401(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 401, 'Unauthorized', {}, None)

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_http_error_403(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 403, 'Forbidden', {}, None)

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_url_error_timeout(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_malformed_json_response(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'not-json'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''

    def test_missing_token_in_response(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'expires_at': '2024-01-01'}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            token = v1_handler.get_runner_registration_token('ghp_test', 'owner/repo')

            assert token == ''


class TestCreateEc2UserData:

    def test_user_data_generation_with_valid_inputs(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert '#!/bin/bash' in user_data
        assert 'set -e' in user_data
        assert './config.sh' in user_data
        assert './run.sh' in user_data
        assert 'token123' in user_data
        assert 'owner/repo' in user_data

    def test_single_label(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['self-hosted'], 'owner/repo')

        assert '--labels "self-hosted"' in user_data

    def test_multiple_labels(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['self-hosted', 'linux', 'x64'], 'owner/repo')

        assert '--labels "self-hosted,linux,x64"' in user_data

    def test_empty_labels_list(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', [], 'owner/repo')

        assert '--labels ""' in user_data

    def test_special_characters_in_repo_name(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['label1'], 'org-name/repo_name')

        assert 'org-name/repo_name' in user_data

    def test_aws_region_from_env(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'us-east-1' in user_data

    def test_contains_self_termination_logic(self, v1_handler, mock_env_vars):
        user_data = v1_handler._create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'aws ec2 terminate-instances' in user_data
        assert 'shutdown -h now' in user_data


class TestGetLatestAmi:

    def test_returns_latest_ami_when_available(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {
                'Images': [
                    {'ImageId': 'ami-older', 'CreationDate': '2024-01-01T00:00:00.000Z'},
                    {'ImageId': 'ami-newer', 'CreationDate': '2024-01-02T00:00:00.000Z'}
                ]
            }

            ami_id = v1_handler.get_latest_ami()

            assert ami_id == 'ami-newer'

    def test_filters_by_purpose_tag(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {'Images': []}

            v1_handler.get_latest_ami()

            call_args = mock_ec2.describe_images.call_args
            filters = call_args[1]['Filters']
            assert {'Name': 'tag:Purpose', 'Values': ['Github self-hosted EC2 runner']} in filters

    def test_filters_by_stable_tag(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {'Images': []}

            v1_handler.get_latest_ami()

            call_args = mock_ec2.describe_images.call_args
            filters = call_args[1]['Filters']
            assert {'Name': 'tag:stable', 'Values': ['true']} in filters

    def test_returns_empty_string_when_no_amis(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {'Images': []}

            ami_id = v1_handler.get_latest_ami()

            assert ami_id == ''

    def test_handles_client_error(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.side_effect = ClientError(
                {'Error': {'Code': 'InvalidParameterValue'}}, 'describe_images'
            )

            ami_id = v1_handler.get_latest_ami()

            assert ami_id == ''


class TestTriggerAmiCreation:

    def test_successful_api_call(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.test.com'}):

            mock_response = Mock()
            mock_response.read.return_value = json.dumps({'success': True}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is True

    def test_uses_correct_api_domain(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen, \
             patch.dict('os.environ', {'API_DOMAIN': 'api.custom.com'}):

            mock_response = Mock()
            mock_response.read.return_value = json.dumps({}).encode()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            v1_handler.trigger_ami_creation()

            call_args = mock_urlopen.call_args[0][0]
            assert 'api.custom.com' in call_args.full_url

    def test_timeout_handling(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError('timeout')

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is False
            assert 'error' in result

    def test_http_error_handling(self, v1_handler):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Internal Error', {}, None)

            result = v1_handler.trigger_ami_creation()

            assert result['success'] is False


class TestLaunchEc2SpotRunner:

    def test_successful_launch(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, '_create_ec2_user_data', return_value='#!/bin/bash'), \
             patch('boto3.client') as mock_boto_client:

            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.run_instances.return_value = {
                'Instances': [{
                    'InstanceId': 'i-123',
                    'PrivateIpAddress': '10.0.0.1',
                    'InstanceType': 't4g.large',
                    'Placement': {'AvailabilityZone': 'us-east-1a'}
                }]
            }

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is True
            assert result['instance_id'] == 'i-123'

    def test_no_ami_triggers_creation(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value=''), \
             patch.object(v1_handler, 'trigger_ami_creation', return_value={'success': True}):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False
            assert 'ami_creation_triggered' in result

    def test_no_github_token_returns_error(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False
            assert 'GITHUB_TOKEN' in result['error']

    def test_registration_token_failure(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False
            assert 'registration token' in result['error']

    def test_subnet_iteration_on_capacity_error(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, '_create_ec2_user_data', return_value='#!/bin/bash'), \
             patch('boto3.client') as mock_boto_client:

            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.run_instances.side_effect = [
                ClientError({'Error': {'Code': 'InsufficientInstanceCapacity'}}, 'run_instances'),
                {
                    'Instances': [{
                        'InstanceId': 'i-456',
                        'PrivateIpAddress': '10.0.0.2',
                        'InstanceType': 't4g.large',
                        'Placement': {'AvailabilityZone': 'us-east-1b'}
                    }]
                }
            ]

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is True
            assert mock_ec2.run_instances.call_count == 2

    def test_applies_correct_tags(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, '_create_ec2_user_data', return_value='#!/bin/bash'), \
             patch('boto3.client') as mock_boto_client:

            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.run_instances.return_value = {
                'Instances': [{
                    'InstanceId': 'i-123',
                    'PrivateIpAddress': '10.0.0.1',
                    'InstanceType': 't4g.large',
                    'Placement': {'AvailabilityZone': 'us-east-1a'}
                }]
            }

            v1_handler.launch_ec2_spot_runner(456, ['self-hosted'], 'owner/repo')

            call_args = mock_ec2.run_instances.call_args
            tag_specs = call_args[1]['TagSpecifications'][0]['Tags']

            tags_dict = {tag['Key']: tag['Value'] for tag in tag_specs}
            assert tags_dict['Name'] == 'github-runner-ec2-456'
            assert tags_dict['GitHubJobId'] == '456'


class TestLaunchPackerBuilder:

    def test_successful_workflow_trigger(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': True}):
            result = v1_handler.launch_packer_builder({})

            assert result['success'] is True

    def test_calls_with_correct_workflow_file(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': True}) as mock_trigger:
            v1_handler.launch_packer_builder({})

            mock_trigger.assert_called_once()
            assert mock_trigger.call_args[0][0] == 'image_for_ec2_runners_post.yml'

    def test_error_handling(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': False, 'error': 'failed'}):
            result = v1_handler.launch_packer_builder({})

            assert result['success'] is False


class TestListAmis:

    def test_returns_list_with_details(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {
                'Images': [{
                    'ImageId': 'ami-123',
                    'Name': 'github-runner-ami',
                    'CreationDate': '2024-01-01T00:00:00.000Z',
                    'State': 'available',
                    'Architecture': 'arm64',
                    'Tags': [{'Key': 'stable', 'Value': 'true'}]
                }]
            }

            result = v1_handler.list_amis()

            assert result['success'] is True
            assert len(result['amis']) == 1
            assert result['amis'][0]['ami_id'] == 'ami-123'

    def test_handles_empty_ami_list(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {'Images': []}

            result = v1_handler.list_amis()

            assert result['success'] is True
            assert result['amis'] == []

    def test_handles_missing_stable_tag(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.describe_images.return_value = {
                'Images': [{
                    'ImageId': 'ami-123',
                    'Name': 'github-runner-ami',
                    'CreationDate': '2024-01-01T00:00:00.000Z',
                    'State': 'available',
                    'Architecture': 'arm64',
                    'Tags': []
                }]
            }

            result = v1_handler.list_amis()

            assert result['success'] is True
            assert result['amis'][0]['tags'].get('stable', 'false') == 'false'


class TestGetLatestAmiDetails:

    def test_returns_full_details(self, v1_handler):
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
            assert result['ami_id'] == 'ami-123'

    def test_returns_error_when_no_ami(self, v1_handler):
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
            assert 'No available AMI found' in result['error']


class TestDeregisterAmi:

    def test_successful_deregistration(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.deregister_image.return_value = {}

            result = v1_handler.deregister_ami('ami-123')

            assert result['success'] is True
            mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-123')

    def test_handles_invalid_ami_id(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.deregister_image.side_effect = ClientError(
                {'Error': {'Code': 'InvalidAMIID.Malformed'}}, 'deregister_image'
            )

            result = v1_handler.deregister_ami('invalid-ami')

            assert result['success'] is False

    def test_handles_ami_not_found(self, v1_handler):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_boto_client.return_value = mock_ec2
            v1_handler.ec2 = mock_ec2

            mock_ec2.deregister_image.side_effect = ClientError(
                {'Error': {'Code': 'InvalidAMIID.NotFound'}}, 'deregister_image'
            )

            result = v1_handler.deregister_ami('ami-notfound')

            assert result['success'] is False


class TestHandleEc2ImageGet:

    def test_calls_get_latest_ami_details(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami_details', return_value={'success': True, 'ami_id': 'ami-123'}):
            result = v1_handler.handle_ec2_image_get({'path': '/latest'})

            assert result['statusCode'] == 200

    def test_returns_success_response(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami_details', return_value={'success': True, 'ami_id': 'ami-123'}):
            result = v1_handler.handle_ec2_image_get({'path': '/latest'})

            body = json.loads(result['body'])
            assert 'ami_id' in body


class TestHandleEc2ImageDelete:

    def test_extracts_ami_id_from_path(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': True}) as mock_deregister:
            v1_handler.handle_ec2_image_delete(event)

            mock_deregister.assert_called_once_with('ami-123')

    def test_returns_success_response(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': True}):
            result = v1_handler.handle_ec2_image_delete(event)

            assert result['statusCode'] == 200

    def test_returns_error_on_failure(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': False, 'error': 'test error'}):
            result = v1_handler.handle_ec2_image_delete(event)

            assert result['statusCode'] == 500


class TestPromoteAmi:

    def test_successful_ami_promotion(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456')

            mock_ec2.create_tags.assert_called_once_with(
                Resources=['ami-123'],
                Tags=[{'Key': 'stable', 'Value': 'true'}]
            )
            mock_ssm.put_parameter.assert_called_once_with(
                Name='/github-runner/ami/latest',
                Value='ami-123',
                Type='String',
                Overwrite=True,
                Description='Latest stable GitHub runner AMI (updated by workflow run run-456)'
            )
            assert result == 0

    def test_ec2_tag_failure(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            mock_ec2.create_tags.side_effect = Exception('EC2 error')

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456')

            assert result == 1

    def test_ssm_parameter_failure(self, promote_ami):
        with patch('boto3.client') as mock_boto_client:
            mock_ec2 = MagicMock()
            mock_ssm = MagicMock()
            mock_boto_client.side_effect = lambda service, **kwargs: mock_ssm if service == 'ssm' else mock_ec2

            mock_ssm.put_parameter.side_effect = Exception('SSM error')

            result = promote_ami.promote_ami('ami-123', 'us-east-1', 'run-456')

            assert result == 1
