from unittest.mock import patch
import pytest


@pytest.mark.usefixtures("mock_env_vars")
class TestGetEc2Config:

    def test_config_contains_subnet_ids(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert 'subnet_ids' in config

    def test_config_contains_security_group_id(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert 'security_group_id' in config

    def test_config_contains_instance_types(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert 'instance_types' in config

    def test_config_contains_iam_instance_profile(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert 'iam_instance_profile' in config

    def test_config_contains_max_price(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert 'max_price' in config

    def test_subnet_ids_parsed_from_env(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert config['subnet_ids'] == ['subnet-123', 'subnet-456', 'subnet-789']

    def test_security_group_id_from_env(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert config['security_group_id'] == 'sg-12345'

    def test_instance_types_from_env(self, v1_handler):
        with patch.dict('os.environ', {'SUBNETS': 'subnet-1', 'SECURITY_GROUPS': 'sg-1', 'EC2_INSTANCE_TYPES': 't4g.large,t4g.medium,t4g.small', 'EC2_IAM_INSTANCE_PROFILE': 'TestProfile', 'EC2_MAX_PRICE': '0.10'}, clear=True):
            config = v1_handler.get_ec2_config()

            assert config['instance_types'] == ['t4g.large', 't4g.medium', 't4g.small']

    def test_iam_instance_profile_default(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert config['iam_instance_profile'] == 'TestInstanceProfile'

    def test_max_price_default(self, v1_handler):
        config = v1_handler.get_ec2_config()

        assert config['max_price'] == '0.10'
