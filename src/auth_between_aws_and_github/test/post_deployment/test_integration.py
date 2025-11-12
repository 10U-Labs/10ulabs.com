#!/usr/bin/env python3
"""
Post-deployment integration tests for auth_between_aws_and_github infrastructure.

These tests verify integration between AWS services after infrastructure deployment:
- OIDC authentication flow (GitHub Actions → AWS STS → IAM Role)
- Secrets Manager integration (OIDC → Secrets Manager → GitHub PAT)
- GitHub API integration (PAT → GitHub API → Runner Registration Token)
- Bedrock integration (OIDC → Bedrock → README check - catches signing errors)
- Auth module AWS API integration (real STS, IAM, Secrets Manager calls)
- Auth module GitHub API integration (real GitHub PAT validation)

These tests require deployed infrastructure and make real API calls.
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


def is_github_actions():
    return os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'


def get_aws_credentials_from_auth_module():
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    session_token = os.environ.get('AWS_SESSION_TOKEN')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    if access_key and secret_key:
        return (access_key, secret_key, session_token, region)

    if is_github_actions():
        try:
            config_path = REPO_ROOT / 'config' / 'auth_between_aws_and_github.json'
            with open(config_path) as f:
                config = json.load(f)

            account_id = config['aws']['account_id']
            role_name = config['aws']['iam_role_name']
            region = config['aws']['region']

            import sys
            sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
            import auth_between_aws_and_github as bootstrap

            temp_creds = bootstrap.assume_role_with_oidc(account_id, region, role_name)
            if temp_creds:
                return (
                    temp_creds['access_key_id'],
                    temp_creds['secret_access_key'],
                    temp_creds['session_token'],
                    region
                )
        except Exception as e:
            import logging
            logging.warning("OIDC authentication failed in integration tests: %s", e)
            pass

    return None


def has_aws_credentials_for_auth_module():
    return get_aws_credentials_from_auth_module() is not None


def get_github_pat_from_auth_module():
    pat = os.environ.get('GH_RUNNER_PAT')
    if pat:
        return pat

    if is_github_actions():
        try:
            creds = get_aws_credentials_from_auth_module()
            if not creds:
                return None

            access_key, secret_key, session_token, region = creds

            config_path = REPO_ROOT / 'config' / 'auth_between_aws_and_github.json'
            with open(config_path) as f:
                config = json.load(f)

            secret_name = config['aws']['secrets_manager']['github_pat_secret_name']

            import sys
            sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
            import auth_between_aws_and_github as bootstrap

            secret_data = bootstrap.get_secret_from_secrets_manager(
                secret_name, region, access_key, secret_key, session_token
            )

            if secret_data:
                return secret_data.get('github_token')
            return None
        except Exception as e:
            import logging
            logging.warning("Failed to retrieve GitHub PAT from Secrets Manager: %s", e)
            return None

    return None


def has_github_pat_for_auth_module():
    return get_github_pat_from_auth_module() is not None


class TestAuthModuleAWSAPIIntegration:

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_sts_get_caller_identity_works(self):
        creds = get_aws_credentials_from_auth_module()
        assert creds is not None, "Credentials should be available"
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.STSClient(region, access_key, secret_key, session_token)

        client.test_sts_access()

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_get_account_id_returns_numeric_value(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        assert account_id.isdigit()

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_get_account_id_returns_twelve_digits(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        assert len(account_id) == 12

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_validate_access_with_real_credentials(self):
        creds = get_aws_credentials_from_auth_module()
        assert creds is not None, "Credentials should be available"
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        client.validate_access()


class TestAuthModuleAWSStateDetectionIntegration:

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_oidc_provider_exists_returns_boolean(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        exists = client.iam.oidc_provider_exists(account_id)
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_role_exists_returns_boolean(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_role_exists_returns_false_for_nonexistent_role(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert exists is False

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_secret_exists_returns_boolean(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.secrets.secret_exists('non-existent-secret-12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_secret_exists_returns_false_for_nonexistent_secret(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.secrets.secret_exists('non-existent-secret-12345')
        assert exists is False


class TestAuthModuleGitHubAPIIntegration:

    @pytest.mark.skipif(not has_github_pat_for_auth_module(), reason="No GitHub PAT available")
    def test_github_pat_validation_with_real_api(self):
        github_token = get_github_pat_from_auth_module()
        assert github_token is not None, "GitHub PAT should be available"

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        bootstrap.validate_github_pat(github_token)
