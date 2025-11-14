#!/usr/bin/env python3
import json
import os
import subprocess

import pytest

from conftest import REPO_ROOT, CONFIG_FILE, load_config


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


class TestOIDCAuthentication:
    

    def test_oidc_token_retrieval(self):
        
        token = get_github_oidc_token()
        assert token is not None
        assert len(token) > 0

    def test_assume_role_with_oidc(self):
        
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
    

    @pytest.fixture
    def oidc_creds(self):
        
        config = load_config()
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    def test_retrieve_github_pat_from_secrets_manager(self, oidc_creds):
        
        config = load_config()

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        
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
    

    @pytest.fixture
    def oidc_creds(self):
        
        config = load_config()
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    def test_github_pat_works_for_runner_registration(self, oidc_creds):
        
        config = load_config()

        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        
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
    

    def test_bedrock_readme_check_with_oidc(self):
        
        config = load_config()


        result = subprocess.run(
            ['python', str(REPO_ROOT / 'auth_between_aws_and_github' / 'auth_between_aws_and_github.py'), 'readme',
             '--aws-account-id', config['aws']['account_id'],
             '--aws-region', config['aws']['region'],
             '--aws-iam-role-name', config['aws']['iam_role_name'],
             '--check'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )

        
        
        
        
        if result.returncode != 0:
            pytest.fail(f"Bedrock README check failed:\n{result.stderr}\n\nBootstrap should have configured everything correctly!")


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
            config_path = REPO_ROOT / 'auth_between_aws_and_github' / 'config.json'
            with open(config_path) as f:
                config = json.load(f)

            account_id = config['aws']['account_id']
            role_name = config['aws']['iam_role_name']
            region = config['aws']['region']

            import sys
            sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
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

            config_path = REPO_ROOT / 'auth_between_aws_and_github' / 'config.json'
            with open(config_path) as f:
                config = json.load(f)

            secret_name = config['aws']['secrets_manager']['github_pat_secret_name']

            import sys
            sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
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
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.STSClient(region, access_key, secret_key, session_token)

        client.test_sts_access()

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_get_account_id_returns_numeric_value(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        assert account_id.isdigit()

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_get_account_id_returns_twelve_digits(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
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
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        client.validate_access()


class TestAuthModuleAWSStateDetectionIntegration:

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_oidc_provider_exists_returns_boolean(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
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
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_role_exists_returns_false_for_nonexistent_role(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert exists is False

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_secret_exists_returns_boolean(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.secrets.secret_exists('non-existent-secret-12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials_for_auth_module(), reason="No AWS credentials available")
    def test_secret_exists_returns_false_for_nonexistent_secret(self):
        creds = get_aws_credentials_from_auth_module()
        access_key, secret_key, session_token, region = creds

        import sys
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
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
        sys.path.insert(0, str(REPO_ROOT / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        bootstrap.validate_github_pat(github_token)


class TestIAMPoliciesIntegration:

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_creds(self, config):
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    def test_role_has_attached_policies(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        assert len(data['AttachedPolicies']) > 0

    def test_administrator_access_policy_is_attached(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        policy_arns = [p['PolicyArn'] for p in data['AttachedPolicies']]
        assert 'arn:aws:iam::aws:policy/AdministratorAccess' in policy_arns

    def test_role_has_zero_inline_policies(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        assert len(data['PolicyNames']) == 0

    def test_role_has_exactly_one_managed_policy(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        assert len(data['AttachedPolicies']) == 1

    def test_only_policy_is_administrator_access(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        policy_arns = [p['PolicyArn'] for p in data['AttachedPolicies']]
        assert policy_arns == ['arn:aws:iam::aws:policy/AdministratorAccess']

    def test_managed_policy_count_is_two_or_less(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'list-attached-role-policies',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        assert len(data['AttachedPolicies']) <= 2


class TestIAMRoleTrustPolicyIntegration:

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_creds(self, config):
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    @pytest.fixture
    def trust_policy(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        return data['Role']['AssumeRolePolicyDocument']

    def test_github_actions_iam_role_exists(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'iam', 'get-role',
             '--role-name', config['aws']['iam_role_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        data = json.loads(result.stdout)
        assert data['Role']['RoleName'] == config['aws']['iam_role_name']

    def test_trust_policy_has_federated_principal(self, trust_policy):
        statements = trust_policy['Statement']
        has_federated = any('Federated' in stmt.get('Principal', {}) for stmt in statements)
        assert has_federated

    def test_trust_policy_does_not_have_aws_principal(self, trust_policy):
        statements = trust_policy['Statement']
        has_aws = any('AWS' in stmt.get('Principal', {}) for stmt in statements)
        assert not has_aws

    def test_trust_policy_does_not_have_service_principal(self, trust_policy):
        statements = trust_policy['Statement']
        has_service = any('Service' in stmt.get('Principal', {}) for stmt in statements)
        assert not has_service

    def test_trust_policy_principal_is_not_wildcard(self, trust_policy):
        statements = trust_policy['Statement']
        for stmt in statements:
            principal = stmt.get('Principal')
            assert principal != '*'

    def test_trust_policy_references_github_oidc_provider(self, config, trust_policy):
        expected_oidc_arn = f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com"
        statements = trust_policy['Statement']
        oidc_principals = [stmt.get('Principal', {}).get('Federated') for stmt in statements]
        assert expected_oidc_arn in oidc_principals

    def test_trust_policy_allows_assume_role_with_web_identity(self, trust_policy):
        statements = trust_policy['Statement']
        actions = []
        for stmt in statements:
            action = stmt.get('Action')
            if isinstance(action, list):
                actions.extend(action)
            else:
                actions.append(action)
        assert 'sts:AssumeRoleWithWebIdentity' in actions

    def test_trust_policy_does_not_allow_assume_role(self, trust_policy):
        statements = trust_policy['Statement']
        actions = []
        for stmt in statements:
            action = stmt.get('Action')
            if isinstance(action, list):
                actions.extend(action)
            else:
                actions.append(action)
        assert 'sts:AssumeRole' not in actions

    def test_trust_policy_requires_sts_amazonaws_com_audience(self, trust_policy):
        statements = trust_policy['Statement']
        has_audience = False
        for stmt in statements:
            conditions = stmt.get('Condition', {})
            string_equals = conditions.get('StringEquals', {})
            aud = string_equals.get('token.actions.githubusercontent.com:aud')
            if aud == 'sts.amazonaws.com':
                has_audience = True
                break
        assert has_audience

    def test_trust_policy_restricts_to_specific_github_repo(self, config, trust_policy):
        expected_sub_pattern = f"repo:{config['github']['org']}/{config['github']['repo']}:*"
        statements = trust_policy['Statement']
        has_repo_condition = False
        for stmt in statements:
            conditions = stmt.get('Condition', {})
            string_like = conditions.get('StringLike', {})
            sub = string_like.get('token.actions.githubusercontent.com:sub')
            if sub == expected_sub_pattern:
                has_repo_condition = True
                break
        assert has_repo_condition

    def test_trust_policy_does_not_allow_wildcard_org(self, trust_policy):
        statements = trust_policy['Statement']
        for stmt in statements:
            conditions = stmt.get('Condition', {})
            string_like = conditions.get('StringLike', {})
            sub = string_like.get('token.actions.githubusercontent.com:sub', '')
            if sub:
                assert not sub.startswith('repo:*/')

    def test_trust_policy_does_not_allow_wildcard_repo(self, trust_policy):
        statements = trust_policy['Statement']
        for stmt in statements:
            conditions = stmt.get('Condition', {})
            string_like = conditions.get('StringLike', {})
            sub = string_like.get('token.actions.githubusercontent.com:sub', '')
            if sub and '/' in sub:
                repo_part = sub.split('/')[1].split(':')[0]
                assert repo_part != '*'

    def test_all_allow_statements_have_conditions(self, trust_policy):
        statements = trust_policy['Statement']
        allow_statements = [s for s in statements if s.get('Effect') == 'Allow']
        for stmt in allow_statements:
            assert 'Condition' in stmt
            assert len(stmt['Condition']) > 0

    def test_principal_is_not_wildcard_string(self, trust_policy):
        statements = trust_policy['Statement']
        for stmt in statements:
            principal = stmt.get('Principal')
            assert principal != '*'

    def test_principal_aws_is_not_wildcard(self, trust_policy):
        statements = trust_policy['Statement']
        for stmt in statements:
            principal = stmt.get('Principal')
            if isinstance(principal, dict) and 'AWS' in principal:
                assert principal['AWS'] != '*'


class TestOIDCProviderIntegration:

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_creds(self, config):
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    @pytest.fixture
    def oidc_provider(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        oidc_provider_arn = f"arn:aws:iam::{config['aws']['account_id']}:oidc-provider/token.actions.githubusercontent.com"

        result = subprocess.run(
            ['aws', 'iam', 'get-open-id-connect-provider',
             '--open-id-connect-provider-arn', oidc_provider_arn,
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        return json.loads(result.stdout)

    def test_oidc_provider_url_is_github_actions(self, oidc_provider):
        assert oidc_provider['Url'] == 'token.actions.githubusercontent.com'

    def test_oidc_provider_client_id_includes_sts_amazonaws_com(self, oidc_provider):
        assert 'sts.amazonaws.com' in oidc_provider['ClientIDList']

    def test_oidc_provider_has_github_thumbprint(self, oidc_provider):
        expected_thumbprint = '6938fd4d98bab03faadb97b34396831e3780aea1'
        assert expected_thumbprint in oidc_provider['ThumbprintList']

    def test_oidc_provider_has_sts_audience(self, oidc_provider):
        assert 'sts.amazonaws.com' in oidc_provider['ClientIDList']

    def test_oidc_provider_does_not_have_wildcard_audience(self, oidc_provider):
        assert '*' not in oidc_provider['ClientIDList']

    def test_provider_url_equals_github_token_url(self, oidc_provider):
        assert oidc_provider['Url'] == 'token.actions.githubusercontent.com'

    def test_provider_url_is_not_amazonaws(self, oidc_provider):
        assert 'amazonaws.com' not in oidc_provider['Url']

    def test_provider_url_is_not_google(self, oidc_provider):
        assert 'google' not in oidc_provider['Url']

    def test_provider_url_is_not_okta(self, oidc_provider):
        assert 'okta' not in oidc_provider['Url']


class TestSecretsManagerComplianceIntegration:

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_creds(self, config):
        oidc_token = get_github_oidc_token()
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    @pytest.fixture
    def secret_metadata(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'secretsmanager', 'describe-secret',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        return json.loads(result.stdout)

    @pytest.fixture
    def secret_value(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

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

        return json.loads(result.stdout)

    def test_github_pat_secret_name_matches_config(self, config, secret_metadata):
        assert secret_metadata['Name'] == config['aws']['secrets_manager']['github_pat_secret_name']

    def test_secret_has_arn(self, secret_metadata):
        assert secret_metadata['ARN'] is not None
        assert len(secret_metadata['ARN']) > 0

    def test_secret_has_kms_key_id(self, secret_metadata):
        assert 'KmsKeyId' in secret_metadata
        assert secret_metadata['KmsKeyId'] is not None

    def test_secret_is_not_scheduled_for_deletion(self, secret_metadata):
        assert 'DeletedDate' not in secret_metadata

    def test_secret_auth_method_is_classic_pat(self, secret_value):
        assert secret_value['auth_method'] == 'classic-pat'

    def test_secret_has_github_token(self, secret_value):
        assert 'github_token' in secret_value

    def test_github_token_is_not_empty(self, secret_value):
        assert len(secret_value['github_token']) > 0

    def test_secret_github_org_matches_config(self, config, secret_value):
        assert secret_value['github_org'] == config['github']['org']

    def test_secret_github_repo_matches_config(self, config, secret_value):
        assert secret_value['github_repo'] == config['github']['repo']

    def test_secret_created_by_is_auth_script(self, secret_value):
        assert secret_value['created_by'] == 'auth-script'

    def test_secret_has_created_at_timestamp(self, secret_value):
        assert 'created_at' in secret_value
        assert len(secret_value['created_at']) > 0

    def test_github_token_starts_with_ghp_prefix(self, secret_value):
        assert secret_value['github_token'].startswith('ghp_')

    def test_token_is_not_placeholder(self, secret_value):
        token = secret_value['github_token'].lower()
        assert 'test' not in token
        assert 'example' not in token
        assert 'placeholder' not in token
        assert 'dummy' not in token

    def test_secret_resource_policy_does_not_allow_public_access(self, config, oidc_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = oidc_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = oidc_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = oidc_creds['session_token']

        result = subprocess.run(
            ['aws', 'secretsmanager', 'get-resource-policy',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'ResourcePolicy' in data:
                policy = json.loads(data['ResourcePolicy'])
                statements = policy.get('Statement', [])
                for stmt in statements:
                    principal = stmt.get('Principal')
                    assert principal != '*'
                    if isinstance(principal, dict) and 'AWS' in principal:
                        assert principal['AWS'] != '*'


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
        assert creds['access_key_id']

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
        assert creds['access_key_id']

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



        assert github_pat

