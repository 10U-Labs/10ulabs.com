"""End-to-end tests for OIDC workflow."""
import json
import os
import subprocess
import urllib.request
import pytest


def get_github_oidc_token():
    """Get GitHub OIDC token from environment."""
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available")
    url = f'{token_url}&audience=sts.amazonaws.com'
    request = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token_request_token}'}
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
    token = data.get('value')
    if not token:
        pytest.fail("Could not retrieve OIDC token")
    return token


def assume_role_with_oidc(account_id, region, role_name, oidc_token):
    """Assume IAM role using OIDC token."""
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    result = subprocess.run(
        ['aws', 'sts', 'assume-role-with-web-identity',
         '--role-arn', role_arn,
         '--role-session-name', 'e2e-test-session',
         '--web-identity-token', oidc_token,
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    creds = data['Credentials']
    return {
        'access_key_id': creds['AccessKeyId'],
        'secret_access_key': creds['SecretAccessKey'],
        'session_token': creds['SessionToken']
    }


class TestCompleteOIDCWorkflow:
    """Test class for complete OIDC workflow."""

    @pytest.fixture
    def oidc_token(self):
        """Get OIDC token fixture."""
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(self, config, oidc_token):
        """Get AWS credentials fixture."""
        return assume_role_with_oidc(
            config['aws_account_id'],
            config['aws_region'],
            config['name_for_github_actions_role'],
            oidc_token
        )

    def test_complete_oidc_workflow(self, oidc_token, aws_creds):
        """Test complete OIDC workflow from token to credentials."""
        assert oidc_token is not None
        assert len(oidc_token) > 0
        assert aws_creds['access_key_id'] is not None
        assert aws_creds['secret_access_key'] is not None
        assert aws_creds['session_token'] is not None

    def test_assumed_role_has_correct_identity(self, config, aws_creds):
        """Test that assumed role has correct identity."""
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws_region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        identity = json.loads(result.stdout)
        arn = identity['Arn']
        role_name_present = config['name_for_github_actions_role'] in arn
        assumed_role_present = 'assumed-role' in arn
        both_present = role_name_present and assumed_role_present
        assert both_present is True
