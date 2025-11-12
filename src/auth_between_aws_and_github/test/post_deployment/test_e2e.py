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


class TestCompleteRunnerRegistrationWorkflow:


    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_token(self):
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(self, config, oidc_token):
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    @pytest.fixture
    def github_pat(self, config, aws_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']

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

    @pytest.fixture
    def runner_registration_response(self, config, github_pat):
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
        return json.loads(result.stdout)

    def test_oidc_token_obtained(self, oidc_token):
        assert oidc_token

    def test_aws_credentials_obtained_via_oidc(self, aws_creds):
        assert aws_creds['access_key_id']

    def test_github_pat_retrieved_from_secrets_manager(self, github_pat):
        assert github_pat

    def test_runner_registration_response_contains_token(self, runner_registration_response):
        assert 'token' in runner_registration_response

    def test_runner_registration_token_not_empty(self, runner_registration_response):
        assert runner_registration_response['token']

    def test_runner_registration_token_has_expiration(self, runner_registration_response):
        assert 'expires_at' in runner_registration_response




class TestBootstrapIdempotency:


    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_creds(self, config):
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
        return env

    @pytest.fixture
    def original_resources(self, config, oidc_creds):
        oidc_result = subprocess.run(
            ['aws', 'iam', 'get-open-id-connect-provider',
             '--open-id-connect-provider-arn',
             f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com",
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        oidc_arn = f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com"

        role_result = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        role_data = json.loads(role_result.stdout)
        role_arn = role_data['Role']['Arn']

        secret_result = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        secret_data = json.loads(secret_result.stdout)
        secret_arn = secret_data['ARN']

        return {
            'oidc_arn': oidc_arn,
            'role_arn': role_arn,
            'secret_arn': secret_arn
        }

    @pytest.fixture
    def bootstrap_execution(self, config, oidc_creds, original_resources):
        return subprocess.run(
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
            env=oidc_creds
        )

    @pytest.fixture
    def resources_after_bootstrap(self, config, oidc_creds, bootstrap_execution):
        oidc_result_after = subprocess.run(
            ['aws', 'iam', 'get-open-id-connect-provider',
             '--open-id-connect-provider-arn',
             f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com",
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )

        role_result_after = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        role_data_after = json.loads(role_result_after.stdout)

        secret_result_after = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        secret_data_after = json.loads(secret_result_after.stdout)

        caller_result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=oidc_creds
        )
        caller_data = json.loads(caller_result.stdout)

        return {
            'oidc_result': oidc_result_after,
            'role_arn': role_data_after['Role']['Arn'],
            'secret_arn': secret_data_after['ARN'],
            'caller_arn': caller_data['Arn']
        }

    def test_bootstrap_create_succeeds_when_rerun(self, bootstrap_execution):
        assert bootstrap_execution.returncode == 0

    def test_oidc_provider_still_exists_after_bootstrap_rerun(self, resources_after_bootstrap):
        assert resources_after_bootstrap['oidc_result'].returncode == 0

    def test_iam_role_arn_unchanged_after_bootstrap_rerun(self, original_resources, resources_after_bootstrap):
        assert resources_after_bootstrap['role_arn'] == original_resources['role_arn']

    def test_secrets_manager_secret_arn_unchanged_after_bootstrap_rerun(self, original_resources, resources_after_bootstrap):
        assert resources_after_bootstrap['secret_arn'] == original_resources['secret_arn']

    def test_oidc_authentication_still_works_after_bootstrap_rerun(self, config, resources_after_bootstrap):
        assert config['aws']['iam_role_name'] in resources_after_bootstrap['caller_arn']


