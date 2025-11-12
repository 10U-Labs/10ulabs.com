


import json
import os
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))

import auth_between_aws_and_github

BOOTSTRAP_SCRIPT = REPO_ROOT / 'src' / 'auth_between_aws_and_github' / 'auth_between_aws_and_github.py'
TEST_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '781581267945')
TEST_REGION = os.environ.get('AWS_REGION', 'us-east-1')
TEST_ROLE_NAME = 'GitHubActionsBootstrapCITest'
TEST_GITHUB_ORG = '10U-Foundation'
TEST_GITHUB_REPO = '10ulabs.com'


def run_command(cmd, check=True, capture_output=True):
    result = subprocess.run(
        cmd,
        shell=True if isinstance(cmd, str) else False,
        capture_output=capture_output,
        text=True,
        check=False
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


class TestHelperFunctions:
    

    @patch('os.environ.get', return_value='true')
    def test_is_running_in_github_actions_returns_true(self, mock_env):
        
        result = auth_between_aws_and_github.is_running_in_github_actions()
        assert result is True

    @patch('os.environ.get', return_value='true')
    def test_is_running_in_github_actions_calls_environ_get_with_correct_args(self, mock_env):
        
        auth_between_aws_and_github.is_running_in_github_actions()
        assert mock_env.call_args == call('GITHUB_ACTIONS', '')

    @patch('os.environ.get', return_value='false')
    def test_is_running_in_github_actions_returns_false(self, mock_env):
        
        result = auth_between_aws_and_github.is_running_in_github_actions()
        assert result is False

    @patch('os.environ.get', return_value='')
    def test_is_running_in_github_actions_returns_false_when_empty(self, mock_env):
        
        result = auth_between_aws_and_github.is_running_in_github_actions()
        assert result is False

    @patch('auth_between_aws_and_github.assume_role_with_oidc')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_warm_with_oidc(self, mock_get_token, mock_assume_role):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_assume_role.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }

        result = auth_between_aws_and_github.detect_infrastructure_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'warm'

    @patch('auth_between_aws_and_github.assume_role_with_oidc')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_calls_assume_role_with_oidc_correctly(self, mock_get_token, mock_assume_role):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_assume_role.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }

        auth_between_aws_and_github.detect_infrastructure_state('123456789012', 'us-east-1', 'test-role')

        assert mock_assume_role.call_args == call('123456789012', 'us-east-1', 'test-role')

    @patch('auth_between_aws_and_github.assume_role_with_oidc')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_cold_with_oidc_failure(self, mock_get_token, mock_assume_role):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_assume_role.return_value = None

        result = auth_between_aws_and_github.detect_infrastructure_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'cold'

    @patch('urllib.request.urlopen')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_warm_with_credentials(self, mock_get_token, mock_urlopen):
        
        mock_get_token.return_value = None
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = auth_between_aws_and_github.detect_infrastructure_state(
            '123456789012', 'us-east-1', 'test-role',
            'AKIATEST', 'secret'
        )

        assert result == 'warm'

    @patch('urllib.request.urlopen')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_cold_with_credentials(self, mock_get_token, mock_urlopen):
        
        from urllib.error import HTTPError
        from io import BytesIO
        mock_get_token.return_value = None
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = auth_between_aws_and_github.detect_infrastructure_state(
            '123456789012', 'us-east-1', 'test-role',
            'AKIATEST', 'secret'
        )

        assert result == 'cold'

    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_detect_infrastructure_state_cold_with_no_credentials(self, mock_get_token):
        
        mock_get_token.return_value = None

        result = auth_between_aws_and_github.detect_infrastructure_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'cold'

    @patch('auth_between_aws_and_github.STSClient')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_assume_role_with_oidc_success(self, mock_get_token, mock_sts_class):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_sts_instance = MagicMock()
        mock_sts_instance.assume_role_with_web_identity.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }
        mock_sts_class.return_value = mock_sts_instance

        result = auth_between_aws_and_github.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is not None

    @patch('auth_between_aws_and_github.STSClient')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_assume_role_with_oidc_returns_correct_access_key_id(self, mock_get_token, mock_sts_class):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_sts_instance = MagicMock()
        mock_sts_instance.assume_role_with_web_identity.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }
        mock_sts_class.return_value = mock_sts_instance

        result = auth_between_aws_and_github.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result['access_key_id'] == 'AKIATEST'

    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_assume_role_with_oidc_no_token(self, mock_get_token):
        
        mock_get_token.return_value = None

        result = auth_between_aws_and_github.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is None

    @patch('auth_between_aws_and_github.STSClient')
    @patch('auth_between_aws_and_github.get_oidc_token')
    def test_assume_role_with_oidc_failure(self, mock_get_token, mock_sts_class):
        
        mock_get_token.return_value = 'test-oidc-token'
        mock_sts_instance = MagicMock()
        mock_sts_instance.assume_role_with_web_identity.return_value = None
        mock_sts_class.return_value = mock_sts_instance

        result = auth_between_aws_and_github.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is None

    @patch('auth_between_aws_and_github.SecretsManagerClient')
    def test_get_secret_from_secrets_manager_success(self, mock_sm_class):
        
        mock_sm_instance = MagicMock()
        mock_sm_instance.get_secret_value.return_value = {'key': 'value'}
        mock_sm_class.return_value = mock_sm_instance

        result = auth_between_aws_and_github.get_secret_from_secrets_manager(
            'test-secret', 'us-east-1', 'AKIATEST', 'secret'
        )

        assert result == {'key': 'value'}

    @patch('auth_between_aws_and_github.SecretsManagerClient')
    def test_get_secret_from_secrets_manager_calls_get_secret_value_correctly(self, mock_sm_class):
        
        mock_sm_instance = MagicMock()
        mock_sm_instance.get_secret_value.return_value = {'key': 'value'}
        mock_sm_class.return_value = mock_sm_instance

        auth_between_aws_and_github.get_secret_from_secrets_manager(
            'test-secret', 'us-east-1', 'AKIATEST', 'secret'
        )

        assert mock_sm_instance.get_secret_value.call_args == call('test-secret')


class TestAWSClientStdlib:
    

    @pytest.fixture
    def client(self):
        
        return auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret123')

    def test_init_sets_region(self, client):
        assert client.region == 'us-east-1'

    def test_init_creates_sts_client(self, client):
        assert isinstance(client.sts, auth_between_aws_and_github.STSClient)

    def test_init_creates_iam_client(self, client):
        assert isinstance(client.iam, auth_between_aws_and_github.IAMClient)

    def test_init_creates_secrets_manager_client(self, client):
        assert isinstance(client.secrets, auth_between_aws_and_github.SecretsManagerClient)

    @patch('urllib.request.urlopen')
    def test_oidc_provider_exists_returns_true_when_found(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.oidc_provider_exists('123456789012')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_oidc_provider_exists_returns_false_on_404(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.oidc_provider_exists('123456789012')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_create_oidc_provider_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.create_oidc_provider()

        assert result is True

    @patch('urllib.request.urlopen')
    def test_create_oidc_provider_calls_urlopen_once(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client.iam.create_oidc_provider()

        assert mock_urlopen.call_count == 1

    @patch('urllib.request.urlopen')
    def test_role_exists_returns_true_when_found(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.role_exists('test-role')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_role_exists_returns_false_on_404(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.role_exists('test-role')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_create_role_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.create_role('test-role', trust_policy)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_attach_managed_policy_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.attach_managed_policy('test-role', 'arn:aws:iam::aws:policy/AdministratorAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_put_role_policy_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        policy_doc = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.put_role_policy('test-role', 'TestPolicy', policy_doc)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_managed_policy_attached_returns_true_when_attached(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/AdministratorAccess</PolicyArn>
                    </member>
                </AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.managed_policy_attached('test-role', 'arn:aws:iam::aws:policy/AdministratorAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_managed_policy_attached_returns_false_when_not_attached(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies></AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.managed_policy_attached('test-role', 'arn:aws:iam::aws:policy/AdministratorAccess')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_inline_policy_exists_returns_true_when_found(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.inline_policy_exists('test-role', 'TestPolicy')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_inline_policy_exists_returns_false_on_404(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.inline_policy_exists('test-role', 'TestPolicy')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_list_attached_managed_policies_returns_two_policies(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/PowerUserAccess</PolicyArn>
                    </member>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/AdministratorAccess</PolicyArn>
                    </member>
                </AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_attached_managed_policies('test-role')

        assert len(result) == 2

    @patch('urllib.request.urlopen')
    def test_list_attached_managed_policies_includes_power_user_access(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/PowerUserAccess</PolicyArn>
                    </member>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/AdministratorAccess</PolicyArn>
                    </member>
                </AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_attached_managed_policies('test-role')

        assert 'arn:aws:iam::aws:policy/PowerUserAccess' in result

    @patch('urllib.request.urlopen')
    def test_list_attached_managed_policies_includes_administrator_access(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/PowerUserAccess</PolicyArn>
                    </member>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/AdministratorAccess</PolicyArn>
                    </member>
                </AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_attached_managed_policies('test-role')

        assert 'arn:aws:iam::aws:policy/AdministratorAccess' in result

    @patch('urllib.request.urlopen')
    def test_list_attached_managed_policies_returns_empty_on_no_policies(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies></AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_attached_managed_policies('test-role')

        assert result == []

    @patch('urllib.request.urlopen')
    def test_list_inline_policies_returns_two_policies(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListRolePoliciesResponse>
            <ListRolePoliciesResult>
                <PolicyNames>
                    <member>IAMRoleManagement</member>
                    <member>CustomPolicy</member>
                </PolicyNames>
            </ListRolePoliciesResult>
        </ListRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_inline_policies('test-role')

        assert len(result) == 2

    @patch('urllib.request.urlopen')
    def test_list_inline_policies_includes_iam_role_management(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListRolePoliciesResponse>
            <ListRolePoliciesResult>
                <PolicyNames>
                    <member>IAMRoleManagement</member>
                    <member>CustomPolicy</member>
                </PolicyNames>
            </ListRolePoliciesResult>
        </ListRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_inline_policies('test-role')

        assert 'IAMRoleManagement' in result

    @patch('urllib.request.urlopen')
    def test_list_inline_policies_includes_custom_policy(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <ListRolePoliciesResponse>
            <ListRolePoliciesResult>
                <PolicyNames>
                    <member>IAMRoleManagement</member>
                    <member>CustomPolicy</member>
                </PolicyNames>
            </ListRolePoliciesResult>
        </ListRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_inline_policies('test-role')

        assert 'CustomPolicy' in result

    @patch('urllib.request.urlopen')
    def test_list_inline_policies_returns_empty_on_no_policies(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <ListRolePoliciesResponse>
            <ListRolePoliciesResult>
                <PolicyNames></PolicyNames>
            </ListRolePoliciesResult>
        </ListRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.list_inline_policies('test-role')

        assert result == []

    @patch('urllib.request.urlopen')
    def test_create_secret_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.create_secret('test-secret', {'key': 'value'})

        assert result is True

    @patch('urllib.request.urlopen')
    def test_update_secret_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test", "VersionId": "v1"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.update_secret('test-secret', {'key': 'new_value'})

        assert result is True

    @patch('urllib.request.urlopen')
    def test_secret_exists_returns_true_when_found(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.secret_exists('test-secret')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_secret_exists_returns_false_on_400(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'ResourceNotFoundException'))
        mock_urlopen.side_effect = error

        result = client.secrets.secret_exists('test-secret')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_secret_on_success(self, mock_urlopen, client):
        
        secret_data = {'github_token': 'ghp_test123', 'github_org': 'test-org'}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'SecretString': json.dumps(secret_data)
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.get_secret_value('test-secret')

        assert result == secret_data

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_none_on_not_found(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'ResourceNotFoundException'))
        mock_urlopen.side_effect = error

        result = client.secrets.get_secret_value('nonexistent-secret')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_none_on_missing_secret_string(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.get_secret_value('test-secret')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_delete_secret_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.delete_secret('test-secret')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_detach_managed_policy_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.detach_managed_policy('test-role', 'arn:aws:iam::aws:policy/AdministratorAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_role_policy_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_role_policy('test-role', 'TestPolicy')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_role_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_role('test-role')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_oidc_provider_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_oidc_provider('123456789012')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_get_role_trust_policy_returns_policy_on_success(self, mock_urlopen, client):
        
        import urllib.parse
        trust_policy = {"Version": "2012-10-17", "Statement": []}
        encoded_policy = urllib.parse.quote(json.dumps(trust_policy))
        xml_response = f'''<?xml version="1.0"?>
        <GetRoleResponse>
            <GetRoleResult>
                <Role>
                    <AssumeRolePolicyDocument>{encoded_policy}</AssumeRolePolicyDocument>
                </Role>
            </GetRoleResult>
        </GetRoleResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.get_role_trust_policy('test-role')

        assert result == trust_policy

    @patch('urllib.request.urlopen')
    def test_get_role_trust_policy_returns_none_on_error(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.get_role_trust_policy('test-role')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_update_role_trust_policy_returns_true_on_success(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.update_role_trust_policy('test-role', trust_policy)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_update_role_trust_policy_returns_false_on_error(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'Error'))
        mock_urlopen.side_effect = error

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.update_role_trust_policy('test-role', trust_policy)

        assert result is False

    @patch('urllib.request.urlopen')
    def test_get_account_id_returns_account_id(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <GetCallerIdentityResponse>
            <GetCallerIdentityResult>
                <Account>123456789012</Account>
            </GetCallerIdentityResult>
        </GetCallerIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.get_account_id()

        assert result == '123456789012'

    @patch('urllib.request.urlopen')
    def test_sts_client_test_sts_access_succeeds(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client.sts.test_sts_access()

        assert mock_urlopen.call_count == 1

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_access_key_id(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
                <Credentials>
                    <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
                    <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</SecretAccessKey>
                    <SessionToken>FQoGZXIvYXdzEBYaD...</SessionToken>
                </Credentials>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-web-identity-token'
        )

        assert result['access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_secret_access_key(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
                <Credentials>
                    <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
                    <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</SecretAccessKey>
                    <SessionToken>FQoGZXIvYXdzEBYaD...</SessionToken>
                </Credentials>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-web-identity-token'
        )

        assert result['secret_access_key'] == 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_session_token(self, mock_urlopen, client):
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
                <Credentials>
                    <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
                    <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</SecretAccessKey>
                    <SessionToken>FQoGZXIvYXdzEBYaD...</SessionToken>
                </Credentials>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-web-identity-token'
        )

        assert result['session_token'] == 'FQoGZXIvYXdzEBYaD...'

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_http_error(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Access Denied'))
        mock_urlopen.side_effect = error

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'invalid-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_parse_error(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'Invalid XML'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_missing_credentials(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_iam_client_test_iam_access_succeeds(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client.iam.test_iam_access()

        assert mock_urlopen.call_count == 1

    @patch('urllib.request.urlopen')
    def test_secrets_manager_client_test_access_succeeds(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"SecretList": []}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client.secrets.test_secrets_manager_access()

        assert mock_urlopen.call_count == 1

    @patch('urllib.request.urlopen')
    def test_stdlib_get_account_id_delegates_to_iam(self, mock_urlopen, client):
        
        xml_response = '''<?xml version="1.0"?>
        <GetCallerIdentityResponse>
            <GetCallerIdentityResult>
                <Account>987654321098</Account>
            </GetCallerIdentityResult>
        </GetCallerIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.get_account_id()

        assert result == '987654321098'

    @patch('urllib.request.urlopen')
    def test_validate_access_succeeds_when_all_services_accessible(self, mock_urlopen, client):
        
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        
        client.validate_access()

        
        assert mock_urlopen.call_count == 3

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_sts_failure(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))
        mock_urlopen.side_effect = error

        raised = False
        try:
            client.validate_access()
        except auth_between_aws_and_github.AWSHTTPError:
            raised = True
        assert raised is True

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_iam_failure(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO

        def side_effect(*args, **kwargs):
            if mock_urlopen.call_count == 1:
                mock_response = MagicMock()
                mock_response.read.return_value = b'<Response></Response>'
                return mock_response.__enter__.return_value
            else:
                raise HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))

        mock_urlopen.side_effect = side_effect

        raised = False
        try:
            client.validate_access()
        except auth_between_aws_and_github.AWSHTTPError:
            raised = True
        assert raised is True

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_secrets_manager_failure(self, mock_urlopen, client):
        
        from urllib.error import HTTPError
        from io import BytesIO

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                mock_response = MagicMock()
                mock_response.read.return_value = b'<Response></Response>'
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                return mock_response
            else:
                raise HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))

        mock_urlopen.side_effect = side_effect

        raised = False
        try:
            client.validate_access()
        except auth_between_aws_and_github.AWSHTTPError:
            raised = True
        assert raised is True


class TestPolicyGenerators:
    

    def test_create_trust_policy_has_correct_version(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        assert policy['Version'] == '2012-10-17'

    def test_create_trust_policy_has_one_statement(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        assert len(policy['Statement']) == 1

    def test_create_trust_policy_statement_allows_action(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        statement = policy['Statement'][0]
        assert statement['Effect'] == 'Allow'

    def test_create_trust_policy_statement_uses_assume_role_with_web_identity(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        statement = policy['Statement'][0]
        assert statement['Action'] == 'sts:AssumeRoleWithWebIdentity'

    def test_create_trust_policy_statement_has_federated_principal(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        statement = policy['Statement'][0]
        assert 'Federated' in statement['Principal']

    def test_create_trust_policy_principal_contains_account_id(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        statement = policy['Statement'][0]
        assert '123456789012' in statement['Principal']['Federated']

    def test_create_trust_policy_condition_restricts_to_repo(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')
        statement = policy['Statement'][0]
        assert 'test-org/test-repo' in statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']

    def test_normalize_policy_includes_action_field(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        result = auth_between_aws_and_github.normalize_policy(policy)
        assert '"Action":"s3:GetObject"' in result

    def test_normalize_policy_includes_effect_field(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        result = auth_between_aws_and_github.normalize_policy(policy)
        assert '"Effect":"Allow"' in result

    def test_normalize_policy_includes_version_field(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        result = auth_between_aws_and_github.normalize_policy(policy)
        assert '"Version":"2012-10-17"' in result

    def test_normalize_policy_removes_spaces_after_commas(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        result = auth_between_aws_and_github.normalize_policy(policy)
        assert ', ' not in result

    def test_normalize_policy_removes_spaces_after_colons(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        result = auth_between_aws_and_github.normalize_policy(policy)
        assert ': ' not in result

    def test_policies_equal_returns_true_for_identical_policies(self):
        
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }

        assert auth_between_aws_and_github.policies_equal(policy1, policy2) is True

    def test_policies_equal_returns_true_for_reordered_keys(self):
        
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Statement": [{"Action": "s3:GetObject", "Effect": "Allow"}],
            "Version": "2012-10-17"
        }

        assert auth_between_aws_and_github.policies_equal(policy1, policy2) is True

    def test_policies_equal_returns_false_for_different_policies(self):
        
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:PutObject"}]
        }

        assert auth_between_aws_and_github.policies_equal(policy1, policy2) is False

    def test_trust_policy_condition_restricts_to_specific_repo(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        sub_condition = statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']
        assert sub_condition == 'repo:test-org/test-repo:*'

    def test_trust_policy_condition_not_overly_permissive(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        sub_condition = statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']
        assert ':*:*' not in sub_condition

    def test_trust_policy_condition_starts_with_correct_prefix(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        sub_condition = statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']
        assert sub_condition.startswith('repo:test-org/test-repo:')

    def test_trust_policy_requires_correct_audience(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        assert 'StringEquals' in statement['Condition']

    def test_trust_policy_audience_condition_equals_sts_amazonaws_com(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        aud_condition = statement['Condition']['StringEquals']['token.actions.githubusercontent.com:aud']
        assert aud_condition == 'sts.amazonaws.com'

    def test_trust_policy_uses_correct_oidc_provider_arn(self):
        
        account_id = '123456789012'
        policy = auth_between_aws_and_github.create_trust_policy(account_id, 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        federated_principal = statement['Principal']['Federated']

        
        expected_arn = f'arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com'
        assert federated_principal == expected_arn

    def test_trust_policy_only_allows_assume_role_with_web_identity(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        assert statement['Action'] == 'sts:AssumeRoleWithWebIdentity'

    def test_trust_policy_action_is_not_list(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        assert isinstance(statement['Action'], str)

    def test_trust_policy_no_wildcard_principals(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        assert statement['Principal'] != '*'

    def test_trust_policy_no_wildcard_aws_principals(self):
        
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        assert 'AWS' not in statement['Principal'] or statement['Principal'].get('AWS') != '*'

    def test_trust_policy_has_string_like_condition(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'my-org', 'my-repo')
        statement = policy['Statement'][0]
        conditions = statement['Condition']
        assert 'StringLike' in conditions

    def test_trust_policy_has_string_equals_condition(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'my-org', 'my-repo')
        statement = policy['Statement'][0]
        conditions = statement['Condition']
        assert 'StringEquals' in conditions

    def test_trust_policy_restricts_sub_claim_to_repo(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'my-org', 'my-repo')
        statement = policy['Statement'][0]
        conditions = statement['Condition']
        sub = conditions['StringLike']['token.actions.githubusercontent.com:sub']
        assert sub == 'repo:my-org/my-repo:*'

    def test_trust_policy_restricts_aud_claim_to_sts(self):
        policy = auth_between_aws_and_github.create_trust_policy('123456789012', 'my-org', 'my-repo')
        statement = policy['Statement'][0]
        conditions = statement['Condition']
        aud = conditions['StringEquals']['token.actions.githubusercontent.com:aud']
        assert aud == 'sts.amazonaws.com'


class TestSecretValueGeneration:
    

    def test_create_secret_value_sets_auth_method(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert result['auth_method'] == 'classic-pat'

    def test_create_secret_value_includes_github_token(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert result['github_token'] == 'ghp_test123'

    def test_create_secret_value_includes_github_org(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert result['github_org'] == 'test-org'

    def test_create_secret_value_includes_github_repo(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert result['github_repo'] == 'test-repo'

    def test_create_secret_value_sets_created_by_field(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert result['created_by'] == 'auth-script'

    def test_create_secret_value_includes_created_at_timestamp(self):
        result = auth_between_aws_and_github.create_secret_value('ghp_test123', 'test-org', 'test-repo')
        assert 'created_at' in result


class TestCreateResources:
    

    @pytest.fixture
    def args(self):
        
        args = Mock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.github_org = 'test-org'
        args.github_repo = 'test-repo'
        args.aws_access_key_id = 'AKIATEST'
        args.aws_secret_access_key = 'secret123'
        args.github_token = 'ghp_test123'
        return args

    @patch('auth_between_aws_and_github.validate_oidc_role_permissions')
    @patch('auth_between_aws_and_github.validate_github_pat')
    @patch('auth_between_aws_and_github.validate_aws_credentials')
    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_create_uses_stdlib_client_in_local_mode(self, mock_stdlib, mock_gh_check,
                                                      mock_aws_val, mock_pat_val, mock_role_val, args):
        
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_stdlib.return_value.set_bedrock_model_id.return_value = mock_client
        mock_client.bedrock.enable_model_access.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = False
        mock_client.iam.create_oidc_provider.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = True
        mock_client.iam.list_attached_managed_policies.return_value = []
        mock_client.iam.list_inline_policies.return_value = []
        mock_client.iam.attach_managed_policy.return_value = True
        mock_client.secrets.create_secret.return_value = True

        result = auth_between_aws_and_github.create_resources(args)

        assert result == 0
        mock_stdlib.assert_called_once_with('us-east-1', access_key_id='AKIATEST', secret_access_key='secret123', session_token=None)
        mock_stdlib.return_value.set_bedrock_model_id.assert_called_once_with(args.bedrock_model_id)
        
        mock_aws_val.assert_called_once()
        mock_pat_val.assert_called_once()
        mock_role_val.assert_called_once()

    @patch('auth_between_aws_and_github.validate_oidc_role_permissions')
    @patch('auth_between_aws_and_github.validate_github_pat')
    @patch('auth_between_aws_and_github.validate_aws_credentials')
    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=True)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_create_skips_existing_oidc_provider(self, mock_stdlib, mock_gh_check,
                                                  mock_aws_val, mock_pat_val, mock_role_val, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_stdlib.return_value.set_bedrock_model_id.return_value = mock_client
        mock_client.bedrock.enable_model_access.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = True
        mock_client.iam.list_attached_managed_policies.return_value = []
        mock_client.iam.list_inline_policies.return_value = []
        mock_client.iam.attach_managed_policy.return_value = True
        mock_client.secrets.create_secret.return_value = True

        result = auth_between_aws_and_github.create_resources(args)

        assert result == 0

    @patch('auth_between_aws_and_github.validate_oidc_role_permissions')
    @patch('auth_between_aws_and_github.validate_github_pat')
    @patch('auth_between_aws_and_github.validate_aws_credentials')
    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=True)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_create_does_not_call_create_oidc_provider_when_exists(self, mock_stdlib, mock_gh_check,
                                                                    mock_aws_val, mock_pat_val, mock_role_val, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_stdlib.return_value.set_bedrock_model_id.return_value = mock_client
        mock_client.bedrock.enable_model_access.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = True
        mock_client.iam.list_attached_managed_policies.return_value = []
        mock_client.iam.list_inline_policies.return_value = []
        mock_client.iam.attach_managed_policy.return_value = True
        mock_client.secrets.create_secret.return_value = True

        auth_between_aws_and_github.create_resources(args)

        assert mock_client.iam.create_oidc_provider.call_count == 0

    @patch('auth_between_aws_and_github.validate_oidc_role_permissions')
    @patch('auth_between_aws_and_github.validate_github_pat')
    @patch('auth_between_aws_and_github.validate_aws_credentials')
    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_create_returns_error_when_oidc_creation_fails(self, mock_stdlib, mock_gh_check,
                                                            mock_aws_val, mock_pat_val, mock_role_val, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_stdlib.return_value.set_bedrock_model_id.return_value = mock_client
        mock_client.bedrock.enable_model_access.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = False
        mock_client.iam.create_oidc_provider.return_value = False  

        result = auth_between_aws_and_github.create_resources(args)

        assert result == 1

    @patch('auth_between_aws_and_github.validate_oidc_role_permissions')
    @patch('auth_between_aws_and_github.validate_github_pat')
    @patch('auth_between_aws_and_github.validate_aws_credentials')
    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_create_returns_error_when_role_creation_fails(self, mock_stdlib, mock_gh_check,
                                                            mock_aws_val, mock_pat_val, mock_role_val, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_stdlib.return_value.set_bedrock_model_id.return_value = mock_client
        mock_client.bedrock.enable_model_access.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = False  

        result = auth_between_aws_and_github.create_resources(args)

        assert result == 1


class TestDestroyResources:
    

    @pytest.fixture
    def args(self):
        
        args = Mock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.github_org = 'test-org'
        args.github_repo = 'test-repo'
        args.aws_access_key_id = 'AKIATEST'
        args.aws_secret_access_key = 'secret123'
        args.force = True
        return args

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_destroy_uses_stdlib_client_in_local_mode(self, mock_stdlib, mock_gh_check, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = True
        mock_client.secrets.delete_secret.return_value = True
        mock_client.iam.role_exists.return_value = True
        mock_client.iam.list_attached_managed_policies.return_value = ['arn:aws:iam::aws:policy/AdministratorAccess']
        mock_client.iam.list_inline_policies.return_value = []
        mock_client.iam.detach_managed_policy.return_value = True
        mock_client.iam.delete_role_policy.return_value = True
        mock_client.iam.delete_role.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.delete_oidc_provider.return_value = True

        result = auth_between_aws_and_github.destroy_resources(args)

        assert result == 0

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_destroy_calls_stdlib_with_correct_args(self, mock_stdlib, mock_gh_check, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = True
        mock_client.secrets.delete_secret.return_value = True
        mock_client.iam.role_exists.return_value = True
        mock_client.iam.list_attached_managed_policies.return_value = ['arn:aws:iam::aws:policy/AdministratorAccess']
        mock_client.iam.list_inline_policies.return_value = []
        mock_client.iam.detach_managed_policy.return_value = True
        mock_client.iam.delete_role_policy.return_value = True
        mock_client.iam.delete_role.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.delete_oidc_provider.return_value = True

        auth_between_aws_and_github.destroy_resources(args)

        assert mock_stdlib.call_args == call('us-east-1', access_key_id='AKIATEST', secret_access_key='secret123', session_token=None)

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=True)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_destroy_skips_non_existent_resources(self, mock_stdlib, mock_gh_check, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = False  
        mock_client.iam.role_exists.return_value = False  
        mock_client.iam.oidc_provider_exists.return_value = False  

        result = auth_between_aws_and_github.destroy_resources(args)

        assert result == 0
        mock_client.secrets.delete_secret.assert_not_called()
        mock_client.iam.delete_role.assert_not_called()
        mock_client.iam.delete_oidc_provider.assert_not_called()

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    @patch('builtins.input', return_value='n')
    def test_destroy_aborts_when_user_declines_confirmation(self, mock_input, mock_stdlib, mock_gh_check, args):
        
        args.force = False
        mock_client = Mock()
        mock_stdlib.return_value = mock_client

        result = auth_between_aws_and_github.destroy_resources(args)

        assert result == 1

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    @patch('builtins.input', return_value='n')
    def test_destroy_does_not_delete_secret_when_user_declines(self, mock_input, mock_stdlib, mock_gh_check, args):
        
        args.force = False
        mock_client = Mock()
        mock_stdlib.return_value = mock_client

        auth_between_aws_and_github.destroy_resources(args)

        assert mock_client.secrets.delete_secret.call_count == 0

    @patch('auth_between_aws_and_github.is_running_in_github_actions', return_value=False)
    @patch('auth_between_aws_and_github.AWSClientStdlib')
    def test_destroy_returns_error_when_secret_deletion_fails(self, mock_stdlib, mock_gh_check, args):
        
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = True
        mock_client.secrets.delete_secret.return_value = False  

        result = auth_between_aws_and_github.destroy_resources(args)

        assert result == 1


class TestDeleteGitHubSecrets:
    

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_returns_true_on_success(self, mock_urlopen):
        
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        )

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_calls_urlopen_twice_for_two_secrets(self, mock_urlopen):
        
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        )

        assert mock_urlopen.call_count == 2

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_handles_404_gracefully(self, mock_urlopen):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        assert result is True  

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_returns_false_on_error(self, mock_urlopen):
        
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 500, 'Internal Server Error', {}, BytesIO(b'Error'))
        mock_urlopen.side_effect = error

        result = auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        assert result is False

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_uses_delete_method(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.get_method() == 'DELETE'

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_url_includes_org_and_repo(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert 'test-org/test-repo' in request.full_url

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_url_includes_secret_name(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert 'AWS_ACCESS_KEY_ID' in request.full_url

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_sets_authorization_header(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.headers['Authorization'] == 'Bearer ghp_test123'

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_sets_accept_header(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        auth_between_aws_and_github.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.headers['Accept'] == 'application/vnd.github+json'


class TestMainFunction:
    

    @patch('sys.argv', ['auth_between_aws_and_github.py'])
    def test_main_shows_help_when_no_args(self):
        
        result = auth_between_aws_and_github.main()
        assert result == 1

    @patch('sys.argv', ['auth_between_aws_and_github.py', '--verbose', 'create',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--github-token', 'ghp_test123'])
    @patch('auth_between_aws_and_github.create_resources')
    def test_main_sets_debug_level_with_verbose_flag(self, mock_create):
        
        import logging
        mock_create.return_value = 0

        with patch('sys.exit'):
            auth_between_aws_and_github.main()

        assert logging.getLogger().level == logging.DEBUG

    @patch('sys.argv', ['auth_between_aws_and_github.py', '--quiet', 'create',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--github-token', 'ghp_test123'])
    @patch('auth_between_aws_and_github.create_resources')
    def test_main_sets_error_level_with_quiet_flag(self, mock_create):
        
        import logging
        mock_create.return_value = 0

        with patch('sys.exit'):
            auth_between_aws_and_github.main()

        assert logging.getLogger().level == logging.ERROR

    @patch('sys.argv', ['auth_between_aws_and_github.py', 'destroy',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--force'])
    @patch('auth_between_aws_and_github.destroy_resources')
    def test_main_calls_destroy_with_force_flag(self, mock_destroy):
        
        mock_destroy.return_value = 0

        with patch('sys.exit'):
            auth_between_aws_and_github.main()

        assert mock_destroy.call_count == 1

    @patch('sys.argv', ['auth_between_aws_and_github.py', 'destroy',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--force'])
    @patch('auth_between_aws_and_github.destroy_resources')
    def test_main_sets_force_flag_correctly(self, mock_destroy):
        
        mock_destroy.return_value = 0

        with patch('sys.exit'):
            auth_between_aws_and_github.main()

        args = mock_destroy.call_args[0][0]
        assert args.force is True



import json
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))

import auth_between_aws_and_github


class TestValidateAWSCredentials:
    

    def test_validates_sts_authentication_with_stdlib(self):
        
        mock_client = Mock()
        mock_client.validate_access = Mock(return_value=None)

        auth_between_aws_and_github.validate_aws_credentials(mock_client)

        assert mock_client.validate_access.call_count == 1

    def test_fails_on_invalid_credentials_stdlib(self):
        
        import urllib.error
        from io import BytesIO

        mock_client = Mock()
        
        original_error = urllib.error.HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))
        error = auth_between_aws_and_github.AWSHTTPError(original_error, 'Access Denied')
        mock_client.validate_access = Mock(side_effect=error)

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_aws_credentials(mock_client)

        assert exc_info.value.code == 1

class TestValidateGitHubPAT:
    

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_validates_admin_org_scope(self, mock_urlopen):
        
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'admin:org, repo, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert mock_urlopen.call_count == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_validates_repo_scope(self, mock_urlopen):
        
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'admin:org, repo'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert mock_urlopen.call_count == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_fails_on_missing_admin_org_scope(self, mock_urlopen):
        
        mock_response = MagicMock()
        
        mock_response.headers.get.return_value = 'repo, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_fails_on_missing_repo_scope(self, mock_urlopen):
        
        mock_response = MagicMock()
        
        mock_response.headers.get.return_value = 'admin:org, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_fails_on_missing_both_scopes(self, mock_urlopen):
        
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'workflow, gist'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_fails_on_invalid_token(self, mock_urlopen):
        
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            'https://api.github.com/user',
            401,
            'Unauthorized',
            {},
            None
        )

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_github_pat('ghp_invalid')

        assert exc_info.value.code == 1

    @patch('auth_between_aws_and_github.urllib.request.urlopen')
    def test_fails_on_network_error(self, mock_urlopen):
        
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Network error")

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1


class TestValidateOIDCRolePermissions:
    

    def test_validates_administrator_access_attached(self):
        
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=True)

        auth_between_aws_and_github.validate_oidc_role_permissions(mock_client, 'TestRole')

        assert mock_client.iam.managed_policy_attached.call_args == call(
            'TestRole',
            'arn:aws:iam::aws:policy/AdministratorAccess'
        )

    def test_fails_on_missing_administrator_access(self):
        
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=False)

        with pytest.raises(SystemExit) as exc_info:
            auth_between_aws_and_github.validate_oidc_role_permissions(mock_client, 'TestRole')

        assert exc_info.value.code == 1


class TestClassHierarchy:
    

    def test_iam_client_inherits_from_base(self):
        client = auth_between_aws_and_github.IAMClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, auth_between_aws_and_github.AWSClientBase)

    def test_iam_client_stores_region(self):
        client = auth_between_aws_and_github.IAMClient('us-east-1', 'AKIATEST', 'secret')
        assert client.region == 'us-east-1'

    def test_iam_client_stores_access_key_id(self):
        client = auth_between_aws_and_github.IAMClient('us-east-1', 'AKIATEST', 'secret')
        assert client.access_key_id == 'AKIATEST'

    def test_iam_client_stores_secret_access_key(self):
        client = auth_between_aws_and_github.IAMClient('us-east-1', 'AKIATEST', 'secret')
        assert client.secret_access_key == 'secret'

    def test_secrets_manager_client_inherits_from_base(self):
        client = auth_between_aws_and_github.SecretsManagerClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, auth_between_aws_and_github.AWSClientBase)

    def test_secrets_manager_client_stores_region(self):
        client = auth_between_aws_and_github.SecretsManagerClient('us-east-1', 'AKIATEST', 'secret')
        assert client.region == 'us-east-1'

    def test_secrets_manager_client_stores_access_key_id(self):
        client = auth_between_aws_and_github.SecretsManagerClient('us-east-1', 'AKIATEST', 'secret')
        assert client.access_key_id == 'AKIATEST'

    def test_sts_client_inherits_from_base(self):
        client = auth_between_aws_and_github.STSClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, auth_between_aws_and_github.AWSClientBase)

    def test_sts_client_stores_region(self):
        client = auth_between_aws_and_github.STSClient('us-east-1', 'AKIATEST', 'secret')
        assert client.region == 'us-east-1'

    def test_sts_client_stores_access_key_id(self):
        client = auth_between_aws_and_github.STSClient('us-east-1', 'AKIATEST', 'secret')
        assert client.access_key_id == 'AKIATEST'

    def test_sts_client_stores_secret_access_key(self):
        client = auth_between_aws_and_github.STSClient('us-east-1', 'AKIATEST', 'secret')
        assert client.secret_access_key == 'secret'

    def test_base_client_has_add_aws_signing_headers_with_timestamp_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_add_aws_signing_headers_with_timestamp')

    def test_base_client_has_build_canonical_request_string_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_build_canonical_request_string')

    def test_base_client_has_build_string_to_sign_with_credential_scope_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_build_string_to_sign_with_credential_scope')

    def test_base_client_has_calculate_aws_signature_v4_hmac_chain_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_calculate_aws_signature_v4_hmac_chain')

    def test_base_client_has_build_aws_authorization_header_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_build_aws_authorization_header')

    def test_base_client_has_sign_request_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_sign_request')

    def test_base_client_has_prepare_json_api_request_with_signing_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_prepare_json_api_request_with_signing')

    def test_base_client_has_prepare_query_api_request_with_signing_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, '_prepare_query_api_request_with_signing')

    def test_base_client_has_make_request_method(self):
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')
        assert hasattr(client, 'make_request')

    def test_canonical_request_url_encodes_uri_segments(self):
        
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')

        canonical_request, _ = client._build_canonical_request_string(
            'POST',
            request_components={
                'uri': '/model/anthropic.claude-sonnet-4-5-20250929-v1:0/invoke',
                'query': '',
                'headers': {'host': 'bedrock-runtime.us-east-1.amazonaws.com'},
                'payload': b'test payload'
            }
        )

        assert '/model/anthropic.claude-sonnet-4-5-20250929-v1%3A0/invoke' in canonical_request

    def test_canonical_request_does_not_encode_slashes_and_dots(self):
        
        client = auth_between_aws_and_github.AWSClientBase('us-east-1', 'AKIATEST', 'secret')

        canonical_request, _ = client._build_canonical_request_string(
            'POST',
            request_components={
                'uri': '/model/anthropic.claude-sonnet-4-5-20250929-v1:0/invoke',
                'query': '',
                'headers': {'host': 'bedrock-runtime.us-east-1.amazonaws.com'},
                'payload': b'test payload'
            }
        )

        assert canonical_request.startswith('POST\n/model/anthropic')


class TestContainerUtilityMethods:
    

    def test_container_has_utility_methods(self):
        
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert callable(client.get_account_id)

    def test_container_has_validate_access_method(self):
        
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert callable(client.validate_access)

    def test_get_account_id_delegates_to_sts_client(self):
        
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert hasattr(client, 'get_account_id')

    def test_sts_client_has_get_account_id_method(self):
        
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert hasattr(client.sts, 'get_account_id')

    def test_client_has_validate_access_method(self):
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')
        assert callable(client.validate_access)

    def test_sts_client_has_test_sts_access_method(self):
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')
        assert callable(client.sts.test_sts_access)

    def test_iam_client_has_test_iam_access_method(self):
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')
        assert callable(client.iam.test_iam_access)

    def test_secrets_client_has_test_secrets_manager_access_method(self):
        client = auth_between_aws_and_github.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')
        assert callable(client.secrets.test_secrets_manager_access)


class TestBedrockClient:
    

    @pytest.fixture
    def bedrock_client(self):
        
        return auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123')

    @patch('urllib.request.urlopen')
    def test_invoke_model_success_anthropic(self, mock_urlopen):
        
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')

        response_data = {
            'content': [{'text': 'Test response from Claude'}]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt')

        assert result == 'Test response from Claude'

    @patch('urllib.request.urlopen')
    def test_invoke_model_success_amazon_nova(self, mock_urlopen):
        
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('amazon.nova-micro-v1:0')

        response_data = {
            'output': {'message': {'content': [{'text': 'Test response from Nova'}]}}
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt')

        assert result == 'Test response from Nova'

    def test_bedrock_client_inherits_from_base(self):
        client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, auth_between_aws_and_github.AWSClientBase)

    def test_bedrock_client_stores_region(self):
        client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        assert client.region == 'us-east-1'

    def test_bedrock_client_stores_access_key_id(self):
        client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        assert client.access_key_id == 'AKIATEST'

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_returns_true(self, mock_request):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]
        result = bedrock_client.enable_model_access()
        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_makes_four_api_calls(self, mock_request):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]
        bedrock_client.enable_model_access()
        assert len(mock_request.call_args_list) == 4

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_calls_have_four_positional_args(self, mock_request):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]
        bedrock_client.enable_model_access()
        call = mock_request.call_args_list[0]
        args, kwargs = call
        assert len(args) == 4

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_calls_use_bedrock_service(self, mock_request):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]
        bedrock_client.enable_model_access()
        call = mock_request.call_args_list[0]
        args, kwargs = call
        assert args[0] == 'bedrock'

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_calls_use_bedrock_signing_service(self, mock_request):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]
        bedrock_client.enable_model_access()
        call = mock_request.call_args_list[0]
        args, kwargs = call
        assert args[3] == 'bedrock'

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_idempotent_on_already_exists(self, mock_request, bedrock_client):
        
        from io import BytesIO
        
        error = auth_between_aws_and_github.AWSHTTPError(
            urllib.error.HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'')),
            '{"message": "Use case already exists"}'
        )
        mock_request.side_effect = [
            error,  
            '{"offers": []}',  
            '{}'  
        ]

        result = bedrock_client.enable_model_access()

        assert result is True  

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_accepts_agreement(self, mock_request):
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]

        result = bedrock_client.enable_model_access()

        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_calls_create_foundation_model_agreement(self, mock_request):
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',
            '{"offers": [{"offerToken": "token123"}]}',
            '{}',
            '{}'
        ]

        bedrock_client.enable_model_access()

        create_agreement_call = [call for call in mock_request.call_args_list
                                if 'create-foundation-model-agreement' in str(call)]
        assert len(create_agreement_call) == 1

    @patch.object(auth_between_aws_and_github.BedrockClient, 'make_rest_request')
    def test_enable_model_access_fails_on_account_not_authorized(self, mock_request):
        
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        from io import BytesIO
        
        error = auth_between_aws_and_github.AWSHTTPError(
            urllib.error.HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'')),
            '{"message":"Your account is not authorized to perform this action. Please create a support case"}'
        )
        mock_request.side_effect = [
            '{}',  
            '{"offers": []}',  
            error  
        ]

        result = bedrock_client.enable_model_access()

        assert result is False  

    def test_enable_model_access_skips_for_non_anthropic_models(self):
        
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('amazon.nova-micro-v1:0')

        
        result = bedrock_client.enable_model_access()

        assert result is True

    def test_bedrock_client_accepts_custom_model_id(self):
        
        client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('amazon.nova-micro-v1:0')
        assert client.model_id == 'amazon.nova-micro-v1:0'

    def test_bedrock_client_accepts_anthropic_model_id(self):
        
        client2 = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('anthropic.claude-sonnet-4-5-20250929-v1:0')
        assert client2.model_id == 'anthropic.claude-sonnet-4-5-20250929-v1:0'

    def test_bedrock_client_defaults_to_claude_haiku(self):
        
        client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123')
        assert client.model_id == 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

    @patch('urllib.request.urlopen')
    def test_invoke_model_caps_max_tokens_for_amazon_nova(self, mock_urlopen):
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('amazon.nova-micro-v1:0')

        response_data = {
            'output': {'message': {'content': [{'text': 'Test response'}]}}
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt', max_tokens=16000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['inferenceConfig']['max_new_tokens'] == 10240

    @patch('urllib.request.urlopen')
    def test_invoke_model_returns_response_text(self, mock_urlopen):
        
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('amazon.nova-micro-v1:0')

        response_data = {
            'output': {'message': {'content': [{'text': 'Test response'}]}}
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt', max_tokens=16000)

        assert result == 'Test response'

    @patch('urllib.request.urlopen')
    def test_invoke_model_includes_messages_in_body(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert 'messages' in body

    @patch('urllib.request.urlopen')
    def test_invoke_model_has_single_message(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert len(body['messages']) == 1

    @patch('urllib.request.urlopen')
    def test_invoke_model_message_role_is_user(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['messages'][0]['role'] == 'user'

    @patch('urllib.request.urlopen')
    def test_invoke_model_content_is_list(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert isinstance(body['messages'][0]['content'], list)

    @patch('urllib.request.urlopen')
    def test_invoke_model_content_has_single_element(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert len(body['messages'][0]['content']) == 1

    @patch('urllib.request.urlopen')
    def test_invoke_model_content_type_is_text(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['messages'][0]['content'][0]['type'] == 'text'

    @patch('urllib.request.urlopen')
    def test_invoke_model_content_text_matches_prompt(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['messages'][0]['content'][0]['text'] == 'Test prompt'

    @patch('urllib.request.urlopen')
    def test_invoke_model_includes_anthropic_version(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['anthropic_version'] == 'bedrock-2023-05-31'

    @patch('urllib.request.urlopen')
    def test_invoke_model_includes_max_tokens(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['max_tokens'] == 1000

    @patch('urllib.request.urlopen')
    def test_invoke_model_returns_response_text(self, mock_urlopen):
        bedrock_client = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret123').set_model_id('us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {'content': [{'text': 'Test response'}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        assert result == 'Test response'


class TestReadmeHelperFunctions:
    

    @patch('auth_between_aws_and_github.assume_role_with_oidc')
    @patch('auth_between_aws_and_github.is_running_in_github_actions')
    @patch('auth_between_aws_and_github.detect_infrastructure_state')
    def test_get_credentials_for_state_oidc_returns_access_key(self, mock_state, mock_is_gha, mock_oidc):
        
        mock_state.return_value = 'warm'
        mock_is_gha.return_value = True
        mock_oidc.return_value = {
            'access_key_id': 'AKIAOIDC',
            'secret_access_key': 'secret',
            'session_token': 'token'
        }

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'

        access_key, secret_key, session_token = auth_between_aws_and_github._get_credentials_for_state(args)

        assert access_key == 'AKIAOIDC'

    @patch('auth_between_aws_and_github.assume_role_with_oidc')
    @patch('auth_between_aws_and_github.is_running_in_github_actions')
    @patch('auth_between_aws_and_github.detect_infrastructure_state')
    def test_get_credentials_for_state_oidc_returns_session_token(self, mock_state, mock_is_gha, mock_oidc):
        
        mock_state.return_value = 'warm'
        mock_is_gha.return_value = True
        mock_oidc.return_value = {
            'access_key_id': 'AKIAOIDC',
            'secret_access_key': 'secret',
            'session_token': 'token'
        }

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'

        access_key, secret_key, session_token = auth_between_aws_and_github._get_credentials_for_state(args)

        assert session_token == 'token'

    @patch('auth_between_aws_and_github.is_running_in_github_actions')
    @patch('auth_between_aws_and_github.detect_infrastructure_state')
    def test_get_credentials_for_state_returns_access_key(self, mock_state, mock_is_gha):
        mock_state.return_value = 'cold'
        mock_is_gha.return_value = False

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.aws_access_key_id = 'AKIADIRECT'
        args.aws_secret_access_key = 'secretdirect'

        access_key, secret_key, session_token = auth_between_aws_and_github._get_credentials_for_state(args)

        assert access_key == 'AKIADIRECT'

    @patch('auth_between_aws_and_github.is_running_in_github_actions')
    @patch('auth_between_aws_and_github.detect_infrastructure_state')
    def test_get_credentials_for_state_returns_secret_key(self, mock_state, mock_is_gha):
        mock_state.return_value = 'cold'
        mock_is_gha.return_value = False

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.aws_access_key_id = 'AKIADIRECT'
        args.aws_secret_access_key = 'secretdirect'

        access_key, secret_key, session_token = auth_between_aws_and_github._get_credentials_for_state(args)

        assert secret_key == 'secretdirect'

    @patch('auth_between_aws_and_github.is_running_in_github_actions')
    @patch('auth_between_aws_and_github.detect_infrastructure_state')
    def test_get_credentials_for_state_returns_no_session_token(self, mock_state, mock_is_gha):
        mock_state.return_value = 'cold'
        mock_is_gha.return_value = False

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.aws_access_key_id = 'AKIADIRECT'
        args.aws_secret_access_key = 'secretdirect'

        access_key, secret_key, session_token = auth_between_aws_and_github._get_credentials_for_state(args)

        assert session_token is None

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_true(self, mock_invoke):
        
        mock_invoke.return_value = 'true'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', 'readme')

        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_calls_invoke_model_once(self, mock_invoke):
        
        mock_invoke.return_value = 'true'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', 'readme')

        assert mock_invoke.call_count == 1

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_false(self, mock_invoke):
        
        mock_invoke.return_value = 'false'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', 'readme')

        assert result is False

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_propagates_exception(self, mock_invoke):
        
        mock_invoke.side_effect = Exception('Bedrock error')

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')

        raised = False
        try:
            auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', 'readme')
        except Exception as e:
            if 'Bedrock error' in str(e):
                raised = True
        assert raised is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_true_for_empty_string(self, mock_invoke):
        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', '')
        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_true_for_whitespace_only(self, mock_invoke):
        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', '   \n\t  ')
        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_handles_verbose_true_response(self, mock_invoke):
        
        
        mock_invoke.return_value = 'true\n\nThe README incorrectly mentions AWS CLI'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._check_readme_needs_update(bedrock, 'code', 'readme')

        assert result is True

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_update_readme_success(self, mock_invoke):
        
        mock_invoke.return_value = '# New README\nContent here'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = auth_between_aws_and_github._update_readme(bedrock, 'code')

        assert result == '# New README\nContent here'

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_update_readme_calls_invoke_model_once(self, mock_invoke):
        
        mock_invoke.return_value = '# New README\nContent here'

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        auth_between_aws_and_github._update_readme(bedrock, 'code')

        assert mock_invoke.call_count == 1

    @patch.object(auth_between_aws_and_github.BedrockClient, 'invoke_model')
    def test_update_readme_raises_on_exception(self, mock_invoke):
        
        mock_invoke.side_effect = Exception('Bedrock error')

        bedrock = auth_between_aws_and_github.BedrockClient('us-east-1', 'AKIATEST', 'secret')

        raised = False
        try:
            auth_between_aws_and_github._update_readme(bedrock, 'code')
        except Exception:
            raised = True
        assert raised is True


class TestReadmeCommand:
    

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_check_update_needed(self, mock_exists, mock_open, mock_creds,
                                           mock_bedrock_class, mock_check):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = None

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 0

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_check_calls_check_readme_needs_update_once(self, mock_exists, mock_open, mock_creds,
                                                                     mock_bedrock_class, mock_check):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = None

        auth_between_aws_and_github.cmd_readme(args)

        assert mock_check.call_count == 1

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_check_no_update_needed(self, mock_exists, mock_open, mock_creds,
                                               mock_bedrock_class, mock_check):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = False
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = None

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 0

    @patch('auth_between_aws_and_github._update_readme')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_update_success(self, mock_exists, mock_open, mock_creds,
                                       mock_bedrock_class, mock_update):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_update.return_value = '# New README'
        mock_exists.return_value = False

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = False
        args.update = True
        args.aws_region = 'us-east-1'

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 0

    @patch('auth_between_aws_and_github._update_readme')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_update_calls_update_readme_once(self, mock_exists, mock_open, mock_creds,
                                                         mock_bedrock_class, mock_update):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_update.return_value = '# New README'
        mock_exists.return_value = False

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = False
        args.update = True
        args.aws_region = 'us-east-1'

        auth_between_aws_and_github.cmd_readme(args)

        assert mock_update.call_count == 1

    @patch('auth_between_aws_and_github._get_credentials_for_state')
    def test_cmd_readme_fails_without_credentials(self, mock_creds):
        
        mock_creds.return_value = (None, None, None)

        args = MagicMock()
        args.check = True
        args.aws_region = 'us-east-1'

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 1

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_propagates_bedrock_errors(self, mock_exists, mock_open, mock_creds,
                                                   mock_bedrock_class, mock_check):
        
        from urllib.error import HTTPError
        from io import BytesIO

        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Access Denied'))
        mock_check.side_effect = error

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'

        raised = False
        try:
            auth_between_aws_and_github.cmd_readme(args)
        except HTTPError as e:
            if 'Forbidden' in str(e):
                raised = True
        assert raised is True

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    def test_cmd_readme_writes_to_output_file_when_update_needed(self, mock_creds,
                                                                  mock_bedrock_class,
                                                                  mock_check, tmp_path, monkeypatch):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True

        bootstrap_file = tmp_path / "auth_between_aws_and_github.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        monkeypatch.setattr('auth_between_aws_and_github.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 0

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    def test_cmd_readme_writes_should_update_true_to_output_file(self, mock_creds,
                                                                   mock_bedrock_class,
                                                                   mock_check, tmp_path, monkeypatch):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True

        bootstrap_file = tmp_path / "auth_between_aws_and_github.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        monkeypatch.setattr('auth_between_aws_and_github.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        auth_between_aws_and_github.cmd_readme(args)

        assert output_file.read_text() == 'readme_is_current=false\n'

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    def test_cmd_readme_writes_to_output_file_when_no_update_needed(self, mock_creds,
                                                                     mock_bedrock_class,
                                                                     mock_check, tmp_path, monkeypatch):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = False

        bootstrap_file = tmp_path / "auth_between_aws_and_github.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        monkeypatch.setattr('auth_between_aws_and_github.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        result = auth_between_aws_and_github.cmd_readme(args)

        assert result == 0

    @patch('auth_between_aws_and_github._check_readme_needs_update')
    @patch('auth_between_aws_and_github.BedrockClient')
    @patch('auth_between_aws_and_github._get_credentials_for_state')
    def test_cmd_readme_writes_should_update_false_to_output_file(self, mock_creds,
                                                                    mock_bedrock_class,
                                                                    mock_check, tmp_path, monkeypatch):
        
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = False

        bootstrap_file = tmp_path / "auth_between_aws_and_github.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        monkeypatch.setattr('auth_between_aws_and_github.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        auth_between_aws_and_github.cmd_readme(args)

        assert output_file.read_text() == 'readme_is_current=true\n'


class TestArgumentValidation:

    def test_no_command_returns_error_code(self):
        result = run_command([str(BOOTSTRAP_SCRIPT)], check=False)
        assert result.returncode != 0

    def test_no_command_shows_usage_message(self):
        result = run_command([str(BOOTSTRAP_SCRIPT)], check=False)
        assert 'usage:' in result.stderr.lower() or 'usage:' in result.stdout.lower()

    def test_help_flag_returns_success_code(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), '--help'], check=False)
        assert result.returncode == 0

    def test_help_flag_shows_usage_message(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), '--help'], check=False)
        assert 'usage:' in result.stdout.lower()

    def test_help_flag_shows_create_command(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), '--help'], check=False)
        assert 'create' in result.stdout.lower()

    def test_help_flag_shows_destroy_command(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), '--help'], check=False)
        assert 'destroy' in result.stdout.lower()

    def test_invalid_command_returns_error_code(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), 'invalid-command'], check=False)
        assert result.returncode != 0

    def test_invalid_command_shows_error_message(self):
        result = run_command([str(BOOTSTRAP_SCRIPT), 'invalid-command'], check=False)
        assert 'invalid choice' in result.stderr.lower() or 'unrecognized' in result.stderr.lower()

    def test_create_command_with_missing_params_returns_error_code(self):
        result = run_command(
            [str(BOOTSTRAP_SCRIPT), 'create', '--aws-account-id', TEST_ACCOUNT_ID],
            check=False
        )
        assert result.returncode != 0

    def test_create_command_with_missing_params_shows_required_message(self):
        result = run_command(
            [str(BOOTSTRAP_SCRIPT), 'create', '--aws-account-id', TEST_ACCOUNT_ID],
            check=False
        )
        assert 'required' in result.stderr.lower() or 'arguments are required' in result.stderr.lower()

    def test_destroy_command_with_missing_params_returns_error_code(self):
        result = run_command(
            [str(BOOTSTRAP_SCRIPT), 'destroy', '--aws-account-id', TEST_ACCOUNT_ID],
            check=False
        )
        assert result.returncode != 0

    def test_destroy_command_with_missing_params_shows_required_message(self):
        result = run_command(
            [str(BOOTSTRAP_SCRIPT), 'destroy', '--aws-account-id', TEST_ACCOUNT_ID],
            check=False
        )
        assert 'required' in result.stderr.lower() or 'arguments are required' in result.stderr.lower()


class TestDependencyRequirements:

    def test_script_loads_without_boto3(self):
        test_script = """
import sys

if 'boto3' in sys.modules:
    del sys.modules['boto3']

class ImportBlocker:
    def find_module(self, fullname, path=None):
        if fullname == 'boto3' or fullname.startswith('boto3.'):
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(f"Import of {fullname} is blocked for testing")

sys.meta_path.insert(0, ImportBlocker())

sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

print("imports_without_boto3=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'imports_without_boto3=True' in result.stdout

    def test_script_loads_without_awscli(self):
        test_script = """
import sys

if 'awscli' in sys.modules:
    del sys.modules['awscli']

class ImportBlocker:
    def find_module(self, fullname, path=None):
        if fullname == 'awscli' or fullname.startswith('awscli.'):
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(f"Import of {fullname} is blocked for testing")

sys.meta_path.insert(0, ImportBlocker())

sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

print("imports_without_awscli=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'imports_without_awscli=True' in result.stdout

    def test_all_imports_are_stdlib(self):
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

imported_modules = set(sys.modules.keys())

external_packages = {'boto3', 'botocore', 'awscli', 'requests', 'urllib3'}

found_external = external_packages & imported_modules

if found_external:
    print(f"ERROR: Found external packages: {found_external}")
    sys.exit(1)

print("only_stdlib_imports=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'only_stdlib_imports=True' in result.stdout


class TestAWSSignatureValidation:

    def test_sts_request_uses_correct_api_version(self):
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'sts', 'GetCallerIdentity', 'sts.us-east-1.amazonaws.com', {}
)

assert b'Version=2011-06-15' in request.data, f"Expected STS API version 2011-06-15, got: {request.data}"
assert b'Action=GetCallerIdentity' in request.data, f"Expected Action=GetCallerIdentity, got: {request.data}"
assert request.method == 'POST', f"Expected POST method, got: {request.method}"

print("sts_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'sts_signature_valid=True' in result.stdout

    def test_iam_request_uses_correct_api_version(self):
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'iam', 'ListRoles', 'iam.us-east-1.amazonaws.com', {}
)

assert b'Version=2010-05-08' in request.data, f"Expected IAM API version 2010-05-08, got: {request.data}"
assert b'Action=ListRoles' in request.data, f"Expected Action=ListRoles, got: {request.data}"
assert request.method == 'POST', f"Expected POST method, got: {request.method}"

print("iam_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'iam_signature_valid=True' in result.stdout

    def test_secrets_manager_request_uses_json_format(self):
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_json_api_request_with_signing(
    'secretsmanager', 'ListSecrets', 'secretsmanager.us-east-1.amazonaws.com', {}
)

assert request.method == 'POST', f"Expected POST method, got: {request.method}"
assert 'X-amz-target' in request.headers or 'X-Amz-Target' in request.headers, f"Expected X-Amz-Target header, got: {list(request.headers.keys())}"

print("secrets_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'secrets_signature_valid=True' in result.stdout

    def test_request_includes_required_aws_signature_headers(self):
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'sts', 'GetCallerIdentity', 'sts.us-east-1.amazonaws.com', {}
)

headers_lower = {k.lower(): v for k, v in request.headers.items()}
assert 'authorization' in headers_lower, f"Missing Authorization header, got: {list(request.headers.keys())}"
assert 'AWS4-HMAC-SHA256' in request.headers.get('Authorization', ''), "Authorization should use AWS4-HMAC-SHA256"
assert 'x-amz-date' in headers_lower, f"Missing x-amz-date header, got: {list(request.headers.keys())}"
assert 'content-type' in headers_lower, f"Missing Content-Type header, got: {list(request.headers.keys())}"

assert request.host == 'sts.us-east-1.amazonaws.com', f"Expected host sts.us-east-1.amazonaws.com, got: {request.host}"

print("signature_headers_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'signature_headers_valid=True' in result.stdout


