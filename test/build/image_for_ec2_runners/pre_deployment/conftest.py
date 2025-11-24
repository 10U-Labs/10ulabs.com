from unittest.mock import patch
import pytest


@pytest.fixture
def mock_env_vars():
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'SUBNETS': 'subnet-123,subnet-456,subnet-789',
        'VPC_ID': 'vpc-test123',
        'SECURITY_GROUPS': 'sg-12345',
        'EC2_INSTANCE_TYPES': 't4g.large,t4g.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'TestInstanceProfile',
        'EC2_MAX_PRICE': '0.10',
        'GITHUB_TOKEN': 'ghp_test_token',
        'API_DOMAIN': 'api.test.com'
    }
    with patch.dict('os.environ', env_vars, clear=False):
        yield env_vars
