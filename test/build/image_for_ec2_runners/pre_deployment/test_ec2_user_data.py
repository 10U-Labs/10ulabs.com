import pytest


@pytest.mark.usefixtures("mock_env_vars")
class TestCreateEc2UserData:

    def test_user_data_contains_bash_shebang(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert '#!/bin/bash' in user_data

    def test_user_data_contains_set_e(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'set -e' in user_data

    def test_user_data_contains_config_sh(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert './config.sh' in user_data

    def test_user_data_contains_run_sh(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert './run.sh' in user_data

    def test_user_data_contains_token(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'token123' in user_data

    def test_user_data_contains_repo_name(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'owner/repo' in user_data

    def test_single_label(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['self-hosted'], 'owner/repo')

        assert '--labels "self-hosted"' in user_data

    def test_multiple_labels(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['self-hosted', 'linux', 'x64'], 'owner/repo')

        assert '--labels "self-hosted,linux,x64"' in user_data

    def test_empty_labels_list(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', [], 'owner/repo')

        assert '--labels ""' in user_data

    def test_special_characters_in_repo_name(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'org-name/repo_name')

        assert 'org-name/repo_name' in user_data

    def test_aws_region_from_env(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'us-east-1' in user_data

    def test_contains_self_termination_logic(self, v1_handler):
        user_data = v1_handler.create_ec2_user_data('token123', ['label1'], 'owner/repo')

        assert 'aws ec2 terminate-instances' in user_data
