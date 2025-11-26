from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
import pytest


def _find_tag_value(tags, key):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return None


@pytest.mark.usefixtures("mock_env_vars")
class TestLaunchEc2SpotRunner:

    def test_successful_launch_returns_success(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, 'create_ec2_user_data', return_value='#!/bin/bash'), \
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

    def test_successful_launch_returns_instance_id(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, 'create_ec2_user_data', return_value='#!/bin/bash'), \
             patch.object(v1_handler, 'create_fleet_launch_template', return_value='lt-123'), \
             patch.object(v1_handler, 'delete_launch_template'), \
             patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2

            mock_ec2.create_fleet.return_value = {
                'Instances': [{'InstanceIds': ['i-123']}]
            }

            with patch.object(v1_handler, 'wait_for_instance_describable', return_value={
                'InstanceId': 'i-123',
                'InstanceType': 't4g.large',
                'Placement': {'AvailabilityZone': 'us-east-1a'}
            }):
                result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['instance_id'] == 'i-123'

    def test_no_ami_returns_failure(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value=''), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'trigger_ami_creation', return_value={'success': True}):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False

    def test_no_ami_triggers_creation(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value=''), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'trigger_ami_creation', return_value={'success': True}):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert 'ami_creation_triggered' in result

    def test_no_github_token_returns_failure(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False

    def test_no_github_token_returns_error_message(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert 'GITHUB_TOKEN' in result['error']

    def test_registration_token_failure_returns_failure(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert result['success'] is False

    def test_registration_token_failure_returns_error_message(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value=''):

            result = v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert 'registration token' in result['error']

    def test_subnet_iteration_on_capacity_error_returns_success(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, 'create_ec2_user_data', return_value='#!/bin/bash'), \
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

    def test_subnet_iteration_on_capacity_error_retries(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami', return_value='ami-123'), \
             patch.object(v1_handler, 'get_github_token', return_value='ghp_token'), \
             patch.object(v1_handler, 'get_runner_registration_token', return_value='reg-token'), \
             patch.object(v1_handler, 'create_ec2_user_data', return_value='#!/bin/bash'), \
             patch.object(v1_handler, 'create_fleet_launch_template', return_value='lt-123'), \
             patch.object(v1_handler, 'delete_launch_template'), \
             patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2

            mock_ec2.create_fleet.return_value = {
                'Instances': [{'InstanceIds': ['i-456']}]
            }

            with patch.object(v1_handler, 'wait_for_instance_describable', return_value={
                'InstanceId': 'i-456',
                'InstanceType': 't4g.large',
                'Placement': {'AvailabilityZone': 'us-east-1b'}
            }):
                v1_handler.launch_ec2_spot_runner(123, ['self-hosted'], 'owner/repo')

            assert mock_ec2.create_fleet.call_count == 1

    def test_applies_name_tag(self, v1_handler):
        with patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2
            mock_ec2.create_launch_template.return_value = {
                'LaunchTemplate': {'LaunchTemplateId': 'lt-123'}
            }

            template_config = {
                'ami_id': 'ami-123',
                'security_group_id': 'sg-123',
                'iam_instance_profile': 'profile',
                'user_data_base64': 'dXNlcmRhdGE=',
                'job_id': 456,
                'job_labels': ['self-hosted'],
                'github_repo': 'owner/repo'
            }

            v1_handler.create_fleet_launch_template(template_config)

            call_args = mock_ec2.create_launch_template.call_args
            tag_specs = call_args[1]['LaunchTemplateData']['TagSpecifications'][0]['Tags']
            name_tag_value = _find_tag_value(tag_specs, 'Name')

            assert name_tag_value == 'github-runner-ec2-456'

    def test_applies_github_job_id_tag(self, v1_handler):
        with patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2
            mock_ec2.create_launch_template.return_value = {
                'LaunchTemplate': {'LaunchTemplateId': 'lt-123'}
            }

            template_config = {
                'ami_id': 'ami-123',
                'security_group_id': 'sg-123',
                'iam_instance_profile': 'profile',
                'user_data_base64': 'dXNlcmRhdGE=',
                'job_id': 456,
                'job_labels': ['self-hosted'],
                'github_repo': 'owner/repo'
            }

            v1_handler.create_fleet_launch_template(template_config)

            call_args = mock_ec2.create_launch_template.call_args
            tag_specs = call_args[1]['LaunchTemplateData']['TagSpecifications'][0]['Tags']
            job_id_tag_value = _find_tag_value(tag_specs, 'GitHubJobId')

            assert job_id_tag_value == '456'

    def test_enforces_imdsv2(self, v1_handler):
        with patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2
            mock_ec2.create_launch_template.return_value = {
                'LaunchTemplate': {'LaunchTemplateId': 'lt-123'}
            }

            template_config = {
                'ami_id': 'ami-123',
                'security_group_id': 'sg-123',
                'iam_instance_profile': 'profile',
                'user_data_base64': 'dXNlcmRhdGE=',
                'job_id': 123,
                'job_labels': ['self-hosted'],
                'github_repo': 'owner/repo'
            }

            v1_handler.create_fleet_launch_template(template_config)

            call_args = mock_ec2.create_launch_template.call_args
            metadata_options = call_args[1]['LaunchTemplateData']['MetadataOptions']

            assert metadata_options['HttpTokens'] == 'required'

    def test_enables_metadata_endpoint(self, v1_handler):
        with patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2
            mock_ec2.create_launch_template.return_value = {
                'LaunchTemplate': {'LaunchTemplateId': 'lt-123'}
            }

            template_config = {
                'ami_id': 'ami-123',
                'security_group_id': 'sg-123',
                'iam_instance_profile': 'profile',
                'user_data_base64': 'dXNlcmRhdGE=',
                'job_id': 123,
                'job_labels': ['self-hosted'],
                'github_repo': 'owner/repo'
            }

            v1_handler.create_fleet_launch_template(template_config)

            call_args = mock_ec2.create_launch_template.call_args
            metadata_options = call_args[1]['LaunchTemplateData']['MetadataOptions']

            assert metadata_options['HttpEndpoint'] == 'enabled'

    def test_applies_managed_by_tag_from_env_var(self, v1_handler, mock_env_vars):
        with patch.object(v1_handler, 'get_ec2_client') as mock_get_ec2:

            mock_ec2 = MagicMock()
            mock_get_ec2.return_value = mock_ec2
            mock_ec2.create_launch_template.return_value = {
                'LaunchTemplate': {'LaunchTemplateId': 'lt-123'}
            }

            template_config = {
                'ami_id': 'ami-123',
                'security_group_id': 'sg-123',
                'iam_instance_profile': 'profile',
                'user_data_base64': 'dXNlcmRhdGE=',
                'job_id': 456,
                'job_labels': ['self-hosted'],
                'github_repo': 'owner/repo'
            }

            v1_handler.create_fleet_launch_template(template_config)

            call_args = mock_ec2.create_launch_template.call_args
            tag_specs = call_args[1]['LaunchTemplateData']['TagSpecifications'][0]['Tags']
            managed_by_tag_value = _find_tag_value(tag_specs, 'ManagedBy')

            assert managed_by_tag_value == mock_env_vars['EC2_MANAGED_BY_TAG']
