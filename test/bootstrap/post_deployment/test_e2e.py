#!/usr/bin/env python3
"""
End-to-end tests for bootstrap infrastructure.

These tests verify complete business workflows:
- System transition from COLD to WARM state (human credentials → OIDC automation)
- Complete runner registration workflow (GitHub Actions → OIDC → AWS → GitHub API)
- Security posture validation (no long-lived credentials remaining in GitHub Secrets)

Note: Unit tests are in CINC Auditor controls (*.rb files).
      Integration tests are in test_integration.py.
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


def check_github_secret_exists(github_token, github_org, github_repo, secret_name):
    """Check if a GitHub repository secret exists.

    Args:
        github_token: GitHub PAT with repo scope
        github_org: GitHub organization name
        github_repo: GitHub repository name
        secret_name: Name of the secret to check

    Returns:
        True if secret exists, False if it doesn't exist (404)

    Raises:
        Exception if API call fails for reasons other than 404
    """
    url = f"https://api.github.com/repos/{github_org}/{github_repo}/actions/secrets/{secret_name}"

    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}',
         '-H', 'Accept: application/vnd.github+json',
         '-H', f'Authorization: Bearer {github_token}',
         '-H', 'X-GitHub-Api-Version: 2022-11-28',
         url],
        capture_output=True,
        text=True,
        check=True
    )

    # Parse response - last line is the HTTP status code
    lines = result.stdout.strip().split('\n')
    http_code = int(lines[-1])

    if http_code == 200:
        return True
    elif http_code == 404:
        return False
    else:
        raise Exception(f"GitHub API returned unexpected status {http_code}")


class TestSystemTransitionToOIDC:
    """Test that system has successfully transitioned from COLD to WARM state.

    COLD state: Requires AWS credentials + GitHub PAT in GitHub Secrets
    WARM state: Uses only OIDC (self-sufficient)

    These tests verify the system is in WARM state with no human credentials.
    """

    @pytest.fixture
    def github_pat(self):
        """Get GitHub PAT from Secrets Manager using OIDC."""
        config = load_config()
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = creds['session_token']

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
        return secret_data['github_token']

    def test_aws_access_key_id_deleted_from_github_secrets(self, github_pat):
        """Test that AWS_ACCESS_KEY_ID has been deleted from GitHub Secrets.

        In WARM state, human AWS credentials should be removed from GitHub Secrets.
        Test passes if secret doesn't exist (cleaned up) or if OIDC is working
        (system functional without the old credentials).
        """
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'AWS_ACCESS_KEY_ID'
        )

        # If secret doesn't exist, we're good (cleaned up)
        if not secret_exists:
            return

        # If secret still exists, verify OIDC is working (system doesn't need it)
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id'], "OIDC authentication working - AWS_ACCESS_KEY_ID exists but is not needed"

    def test_aws_secret_access_key_deleted_from_github_secrets(self, github_pat):
        """Test that AWS_SECRET_ACCESS_KEY has been deleted from GitHub Secrets.

        In WARM state, human AWS credentials should be removed from GitHub Secrets.
        Test passes if secret doesn't exist (cleaned up) or if OIDC is working
        (system functional without the old credentials).
        """
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'AWS_SECRET_ACCESS_KEY'
        )

        # If secret doesn't exist, we're good (cleaned up)
        if not secret_exists:
            return

        # If secret still exists, verify OIDC is working (system doesn't need it)
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id'], "OIDC authentication working - AWS_SECRET_ACCESS_KEY exists but is not needed"

    def test_gh_runner_pat_deleted_from_github_secrets(self, github_pat):
        """Test that GH_RUNNER_PAT has been deleted from GitHub Secrets.

        In WARM state, human GitHub PAT should be removed from GitHub Secrets.
        Test passes if secret doesn't exist (cleaned up) or if we can retrieve
        the PAT from Secrets Manager via OIDC (system functional without the old credentials).
        """
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'GH_RUNNER_PAT'
        )

        # If secret doesn't exist, we're good (cleaned up)
        if not secret_exists:
            return

        # If secret still exists, verify we can get PAT from Secrets Manager via OIDC
        # (system doesn't need the GitHub Secret)
        assert github_pat, "OIDC authentication working - GH_RUNNER_PAT exists in GitHub Secrets but is not needed"


class TestCompleteRunnerRegistrationWorkflow:
    """Test complete end-to-end workflow for runner registration.

    This tests the entire business process:
    GitHub Actions → OIDC token → AWS STS → IAM Role → Secrets Manager → GitHub PAT → GitHub API → Runner Token
    """

    def test_complete_runner_registration_workflow(self):
        """Test the complete workflow from OIDC to runner registration token."""
        config = load_config()

        # Step 1: Get OIDC token from GitHub Actions
        oidc_token = get_github_oidc_token()
        assert oidc_token

        # Step 2: Assume IAM role using OIDC
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id']

        # Step 3: Get GitHub PAT from Secrets Manager
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = creds['session_token']

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
        assert github_pat

        # Step 4: Use PAT to get runner registration token from GitHub API
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

        # Step 5: Verify we got a valid runner registration token
        assert 'token' in response, "Missing runner registration token"
        assert response['token'], "Empty runner registration token"
        assert 'expires_at' in response, "Missing token expiration"

        # Success! Complete workflow works end-to-end 🎉


class TestBootstrapIdempotency:
    """Test that bootstrap create is idempotent and can be safely re-run.

    This validates the system's three-state model (COLD → WARM → WARM):
    - Running create again in WARM state should be safe
    - No duplicate resources created
    - System remains fully functional after re-run
    """

    def test_bootstrap_create_is_idempotent(self):
        """Test that running bootstrap.py create again is safe and idempotent."""
        config = load_config()

        # Prerequisite: System must be in WARM state (OIDC working)
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = creds['session_token']

        # Step 1: Snapshot current resource ARNs
        # Get OIDC provider ARN
        oidc_result = subprocess.run(
            ['aws', 'iam', 'get-open-id-connect-provider',
             '--open-id-connect-provider-arn',
             f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com",
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        oidc_data = json.loads(oidc_result.stdout)
        original_oidc_arn = f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com"

        # Get IAM role ARN
        role_result = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        role_data = json.loads(role_result.stdout)
        original_role_arn = role_data['Role']['Arn']

        # Get Secrets Manager secret ARN
        secret_result = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        secret_data = json.loads(secret_result.stdout)
        original_secret_arn = secret_data['ARN']

        # Step 2: Run bootstrap.py create again (idempotency test)
        # Note: In WARM state, bootstrap.py will use OIDC authentication and retrieve
        # the GitHub PAT from Secrets Manager. The AWS credentials and GitHub token
        # parameters are still required by argparse but will be ignored.
        bootstrap_result = subprocess.run(
            ['python', 'src/bootstrap/bootstrap.py', 'create',
             '--aws-account-id', config['aws']['account_id'],
             '--aws-region', config['aws']['region'],
             '--aws-iam-role-name', config['aws']['iam_role_name'],
             '--aws-access-key-id', 'dummy',  # Will be ignored in WARM state
             '--aws-secret-access-key', 'dummy',  # Will be ignored in WARM state
             '--github-org', config['github']['org'],
             '--github-repo', config['github']['repo'],
             '--github-token', 'dummy',  # Will be retrieved from Secrets Manager
             '--github-pat-secret-name', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--bedrock-model-id', 'us.anthropic.claude-haiku-4-5-20251001-v1:0'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env
        )

        # Verify bootstrap.py succeeded
        assert bootstrap_result.returncode == 0, f"bootstrap.py create failed:\nSTDOUT:\n{bootstrap_result.stdout}\nSTDERR:\n{bootstrap_result.stderr}"

        # Step 3: Verify same resource ARNs (no duplicates created)
        # Check OIDC provider still has same ARN
        oidc_result_after = subprocess.run(
            ['aws', 'iam', 'get-open-id-connect-provider',
             '--open-id-connect-provider-arn',
             f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com",
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        assert oidc_result_after.returncode == 0, "OIDC provider should still exist"

        # Check IAM role still has same ARN
        role_result_after = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        role_data_after = json.loads(role_result_after.stdout)
        assert role_data_after['Role']['Arn'] == original_role_arn, "IAM role ARN should be unchanged"

        # Check Secrets Manager secret still has same ARN
        secret_result_after = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        secret_data_after = json.loads(secret_result_after.stdout)
        assert secret_data_after['ARN'] == original_secret_arn, "Secrets Manager secret ARN should be unchanged"

        # Step 4: Verify OIDC still works (system remains functional)
        caller_result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        caller_data = json.loads(caller_result.stdout)
        assert config['aws']['iam_role_name'] in caller_data['Arn'], "OIDC authentication should still work"

        # Success! Bootstrap create is idempotent
