#!/usr/bin/env python3
"""
Integration tests for bootstrap infrastructure.

These tests verify integration between AWS services:
- OIDC authentication flow (GitHub Actions → AWS STS → IAM Role)
- Secrets Manager integration (OIDC → Secrets Manager → GitHub PAT)
- GitHub API integration (PAT → GitHub API → Runner Registration Token)
- Bedrock integration (OIDC → Bedrock → README check - catches signing errors)

Note: Unit tests are in CINC Auditor controls (*.rb files).
      End-to-end workflow tests are in test_e2e.py.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


# Test configuration
REPO_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_FILE = REPO_ROOT / 'config' / 'bootstrap.json'


def load_config():
    """Load bootstrap configuration."""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def get_github_oidc_token():
    """Get OIDC token from GitHub Actions environment."""
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')

    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available (not in GitHub Actions with id-token: write)")

    result = subprocess.run(
        ['curl', '-s', '-H', f'Authorization: Bearer {token_request_token}',
         f'{token_url}&audience=sts.amazonaws.com'],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    token = data.get('value')

    if not token:
        pytest.fail("Could not retrieve OIDC token from GitHub Actions")

    return token


def assume_role_with_oidc(account_id, region, role_name, oidc_token):
    """Assume IAM role using OIDC token."""
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    result = subprocess.run(
        ['aws', 'sts', 'assume-role-with-web-identity',
         '--role-arn', role_arn,
         '--role-session-name', 'integration-test-session',
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


class TestOIDCAuthentication:
    """Test OIDC authentication integration with AWS STS."""

    def test_oidc_token_retrieval(self):
        """Test that we can retrieve OIDC token from GitHub Actions."""
        token = get_github_oidc_token()
        assert token is not None
        assert len(token) > 0

    def test_assume_role_with_oidc(self):
        """Test that we can assume IAM role using OIDC."""
        config = load_config()
        oidc_token = get_github_oidc_token()

        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

        assert creds['access_key_id']
        assert creds['secret_access_key']
        assert creds['session_token']

    def test_temporary_credentials_work(self):
        """Test that temporary credentials from OIDC work for AWS API calls."""
        config = load_config()
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

        # Use temporary credentials to call AWS API
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = creds['session_token']

        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        identity = json.loads(result.stdout)
        assert config['aws']['iam_role_name'] in identity['Arn']


class TestSecretsManagerIntegration:
    """Test Secrets Manager integration with OIDC credentials."""

    @pytest.fixture
    def oidc_creds(self):
        """Get OIDC credentials for tests."""
        config = load_config()
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    def test_retrieve_github_pat_from_secrets_manager(self, oidc_creds):
        """Test that we can retrieve GitHub PAT from Secrets Manager using OIDC."""
        config = load_config()

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        # Get GitHub PAT from Secrets Manager
        result = subprocess.run(
            ['aws', 'secretsmanager', 'get-secret-value',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--query', 'SecretString',
             '--output', 'text'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        secret_data = json.loads(result.stdout)
        assert 'github_token' in secret_data
        assert secret_data['github_token']


class TestGitHubAPIIntegration:
    """Test GitHub API integration using PAT from Secrets Manager."""

    @pytest.fixture
    def oidc_creds(self):
        """Get OIDC credentials for tests."""
        config = load_config()
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    def test_github_pat_works_for_runner_registration(self, oidc_creds):
        """Test that GitHub PAT can generate runner registration tokens."""
        config = load_config()

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        # Get GitHub PAT from Secrets Manager
        result = subprocess.run(
            ['aws', 'secretsmanager', 'get-secret-value',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--query', 'SecretString',
             '--output', 'text'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        secret_data = json.loads(result.stdout)
        github_pat = secret_data['github_token']

        # Test PAT by getting runner registration token
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             '-H', 'Accept: application/vnd.github+json',
             '-H', f'Authorization: Bearer {github_pat}',
             '-H', 'X-GitHub-Api-Version: 2022-11-28',
             f"https://api.github.com/repos/{config['github']['org']}/{config['github']['repo']}/actions/runners/registration-token"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        assert 'token' in response
        assert response['token']
        assert 'expires_at' in response


class TestBedrockIntegration:
    """Test Bedrock integration with OIDC credentials."""

    def test_bedrock_readme_check_with_oidc(self):
        """Test that Bedrock README check works with OIDC credentials (catches signing errors)."""
        config = load_config()

        # Run auth_between_aws_and_github.py readme --check (uses OIDC automatically in GitHub Actions)
        result = subprocess.run(
            ['python', str(REPO_ROOT / 'src' / 'bootstrap' / 'auth_between_aws_and_github.py'), 'readme',
             '--aws-account-id', config['aws']['account_id'],
             '--aws-region', config['aws']['region'],
             '--aws-iam-role-name', config['aws']['iam_role_name'],
             '--check'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )

        # Test goal: Verify Bedrock integration works end-to-end
        # - Tests AWS signature is correct (service name, URI encoding, etc.)
        # - Tests IAM permissions are configured correctly
        # - Tests model access is working
        if result.returncode != 0:
            pytest.fail(f"Bedrock README check failed:\n{result.stderr}\n\nBootstrap should have configured everything correctly!")

        # If success, verify output format
        output = result.stdout.strip().split('\n')[-1]
        assert output in ['True', 'False'], f"Expected 'True' or 'False', got: {output}"
