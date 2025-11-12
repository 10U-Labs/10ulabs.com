#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

import pytest



REPO_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_FILE = REPO_ROOT / 'config' / 'bootstrap.json'


def load_config():
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def get_github_oidc_token():
    
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

    
    lines = result.stdout.strip().split('\n')
    http_code = int(lines[-1])

    if http_code == 200:
        return True
    elif http_code == 404:
        return False
    else:
        raise Exception(f"GitHub API returned unexpected status {http_code}")


class TestSystemTransitionToOIDC:
    

    @pytest.fixture
    def github_pat(self):
        
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
        
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'AWS_ACCESS_KEY_ID'
        )

        
        if not secret_exists:
            return

        
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id'], "OIDC authentication working - AWS_ACCESS_KEY_ID exists but is not needed"

    def test_aws_secret_access_key_deleted_from_github_secrets(self, github_pat):
        
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'AWS_SECRET_ACCESS_KEY'
        )

        
        if not secret_exists:
            return

        
        oidc_token = get_github_oidc_token()
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id'], "OIDC authentication working - AWS_SECRET_ACCESS_KEY exists but is not needed"

    def test_gh_runner_pat_deleted_from_github_secrets(self, github_pat):
        
        config = load_config()

        secret_exists = check_github_secret_exists(
            github_pat,
            config['github']['org'],
            config['github']['repo'],
            'GH_RUNNER_PAT'
        )

        
        if not secret_exists:
            return

        
        
        assert github_pat, "OIDC authentication working - GH_RUNNER_PAT exists in GitHub Secrets but is not needed"


class TestCompleteRunnerRegistrationWorkflow:
    

    def test_complete_runner_registration_workflow(self):
        
        config = load_config()

        
        oidc_token = get_github_oidc_token()
        assert oidc_token

        
        creds = assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )
        assert creds['access_key_id']

        
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

        
        assert 'token' in response, "Missing runner registration token"
        assert response['token'], "Empty runner registration token"
        assert 'expires_at' in response, "Missing token expiration"

        


class TestBootstrapIdempotency:
    

    def test_bootstrap_create_is_idempotent(self):
        
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

        
        
        
        
        bootstrap_result = subprocess.run(
            ['python', 'src/auth_between_aws_and_github/auth_between_aws_and_github.py', 'create',
             '--aws-account-id', config['aws']['account_id'],
             '--aws-region', config['aws']['region'],
             '--aws-iam-role-name', config['aws']['iam_role_name'],
             '--aws-access-key-id', 'dummy',  
             '--aws-secret-access-key', 'dummy',  
             '--github-org', config['github']['org'],
             '--github-repo', config['github']['repo'],
             '--github-token', 'dummy',  
             '--github-pat-secret-name', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--bedrock-model-id', 'us.anthropic.claude-haiku-4-5-20251001-v1:0'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env
        )

        
        assert bootstrap_result.returncode == 0, f"auth_between_aws_and_github.py create failed:\nSTDOUT:\n{bootstrap_result.stdout}\nSTDERR:\n{bootstrap_result.stderr}"

        
        
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

        
