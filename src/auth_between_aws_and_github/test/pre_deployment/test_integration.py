#!/usr/bin/env python3
"""
Integration tests for auth_between_aws_and_github.py

Tests component integration and real API integration (read-only operations).

Component Integration Tests:
- CLI argument validation
- User interaction flows
- Subprocess execution with fake credentials
- AWS Signature V4 validation

API Integration Tests (Read-Only):
- Real AWS API calls (STS, IAM, Secrets Manager)
- Real GitHub API calls (PAT validation)
- Infrastructure state detection
- Uses OIDC in GitHub Actions, env vars locally
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


# Test configuration
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
BOOTSTRAP_SCRIPT = REPO_ROOT / 'src' / 'auth_between_aws_and_github' / 'auth_between_aws_and_github.py'
TEST_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '781581267945')
TEST_REGION = os.environ.get('AWS_REGION', 'us-east-1')
TEST_ROLE_NAME = 'GitHubActionsBootstrapCITest'
TEST_GITHUB_ORG = '10U-Foundation'
TEST_GITHUB_REPO = '10ulabs.com'


def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result."""
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


class TestArgumentValidation:
    """Test command-line argument validation."""

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
    """Test that auth_between_aws_and_github.py uses only Python stdlib (no external dependencies)."""

    def test_script_loads_without_boto3(self):
        """Test that auth_between_aws_and_github.py can be imported without boto3 installed."""
        test_script = """
import sys

# Hide boto3 if it exists
if 'boto3' in sys.modules:
    del sys.modules['boto3']

# Add to import blacklist
class ImportBlocker:
    def find_module(self, fullname, path=None):
        if fullname == 'boto3' or fullname.startswith('boto3.'):
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(f"Import of {fullname} is blocked for testing")

sys.meta_path.insert(0, ImportBlocker())

# Now try to import auth_between_aws_and_github as bootstrap
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

print("imports_without_boto3=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'imports_without_boto3=True' in result.stdout

    def test_script_loads_without_awscli(self):
        """Test that auth_between_aws_and_github.py can be imported without AWS CLI installed."""
        test_script = """
import sys

# Hide awscli if it exists
if 'awscli' in sys.modules:
    del sys.modules['awscli']

# Add to import blacklist
class ImportBlocker:
    def find_module(self, fullname, path=None):
        if fullname == 'awscli' or fullname.startswith('awscli.'):
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(f"Import of {fullname} is blocked for testing")

sys.meta_path.insert(0, ImportBlocker())

# Now try to import auth_between_aws_and_github as bootstrap
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

print("imports_without_awscli=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'imports_without_awscli=True' in result.stdout

    def test_all_imports_are_stdlib(self):
        """Test that auth_between_aws_and_github.py only imports from Python stdlib."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

# Get all imported modules
imported_modules = set(sys.modules.keys())

# Known external packages that should NOT be imported
external_packages = {'boto3', 'botocore', 'awscli', 'requests', 'urllib3'}

# Check if any external packages were imported
found_external = external_packages & imported_modules

if found_external:
    print(f"ERROR: Found external packages: {found_external}")
    sys.exit(1)

print("only_stdlib_imports=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'only_stdlib_imports=True' in result.stdout


class TestModeDetection:
    """Test environment detection (local vs GitHub Actions)."""

    def test_detects_local_mode_when_not_in_github_actions(self):
        """Test that script correctly detects local mode."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap
import os

# Ensure we're not in GitHub Actions
if 'GITHUB_ACTIONS' in os.environ:
    del os.environ['GITHUB_ACTIONS']

print(f"is_github_actions={bootstrap.is_running_in_github_actions()}")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'is_github_actions=False' in result.stdout

    def test_detects_github_actions_mode(self):
        """Test that script correctly detects GitHub Actions mode."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import os

# Set GitHub Actions environment variable
os.environ['GITHUB_ACTIONS'] = 'true'

import auth_between_aws_and_github as bootstrap

print(f"is_github_actions={bootstrap.is_running_in_github_actions()}")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'is_github_actions=True' in result.stdout


class TestUserInteraction:
    """Test interactive user prompts and confirmations."""

    def test_destroy_without_force_returns_error_code_on_decline(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='n\n', timeout=30)
        assert proc.returncode == 1

    def test_destroy_without_force_shows_aborted_message_on_decline(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='n\n', timeout=30)
        assert 'Aborted' in stdout or 'Aborted' in stderr

    def test_destroy_with_force_does_not_show_aborted_in_stdout(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy', '--force',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = proc.communicate(timeout=30)
            assert 'Aborted' not in stdout
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Script hung waiting for input despite --force flag")

    def test_destroy_with_force_does_not_show_aborted_in_stderr(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy', '--force',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = proc.communicate(timeout=30)
            assert 'Aborted' not in stderr
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Script hung waiting for input despite --force flag")

    def test_destroy_does_not_abort_in_stdout_on_yes(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='y\n', timeout=30)
        assert 'Aborted' not in stdout

    def test_destroy_does_not_abort_in_stderr_on_yes(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='y\n', timeout=30)
        assert 'Aborted' not in stderr

    def test_destroy_does_not_abort_in_stdout_on_empty_input(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='\n', timeout=30)
        assert 'Aborted' not in stdout

    def test_destroy_does_not_abort_in_stderr_on_empty_input(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input='\n', timeout=30)
        assert 'Aborted' not in stderr

    def test_destroy_returns_nonzero_on_keyboard_interrupt(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            proc.send_signal(subprocess.signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=30)
            assert proc.returncode != 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Script didn't handle SIGINT gracefully")

    def test_destroy_shows_aborted_or_fails_on_keyboard_interrupt(self):
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'destroy',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--github-pat-secret-name', 'github-runner/credentials',
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            proc.send_signal(subprocess.signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=30)
            assert 'Aborted' in stdout or 'Aborted' in stderr or proc.returncode < 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Script didn't handle SIGINT gracefully")

    def test_create_is_non_interactive(self):
        """Test that create command doesn't hang waiting for input."""
        # create should not prompt for input - should fail fast with bad credentials
        proc = subprocess.Popen(
            [str(BOOTSTRAP_SCRIPT), 'create',
             '--aws-account-id', TEST_ACCOUNT_ID,
             '--aws-region', TEST_REGION,
             '--aws-iam-role-name', TEST_ROLE_NAME,
             '--github-org', TEST_GITHUB_ORG,
             '--github-repo', TEST_GITHUB_REPO,
             '--aws-access-key-id', 'AKIATEST',
             '--aws-secret-access-key', 'test',
             '--github-token', 'ghp_test123'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Don't send any input
        try:
            stdout, stderr = proc.communicate(timeout=10)
            # Should have exited (with error due to bad credentials)
            # but should NOT have hung waiting for input
            assert proc.returncode != 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("create command hung waiting for input (should be non-interactive)")


class TestAWSSignatureValidation:
    """Test AWS Signature V4 implementation produces correct request format.

    These tests validate that our AWS request signing produces the correct
    API versions and request formats without making actual AWS API calls.
    This would have caught the API version bug that caused STS failures.
    """

    def test_sts_request_uses_correct_api_version(self):
        """Verify STS requests use API version 2011-06-15."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'sts', 'GetCallerIdentity', 'sts.us-east-1.amazonaws.com', {}
)

# Validate request format
assert b'Version=2011-06-15' in request.data, f"Expected STS API version 2011-06-15, got: {request.data}"
assert b'Action=GetCallerIdentity' in request.data, f"Expected Action=GetCallerIdentity, got: {request.data}"
assert request.method == 'POST', f"Expected POST method, got: {request.method}"

print("sts_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'sts_signature_valid=True' in result.stdout

    def test_iam_request_uses_correct_api_version(self):
        """Verify IAM requests use API version 2010-05-08."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'iam', 'ListRoles', 'iam.us-east-1.amazonaws.com', {}
)

# Validate request format
assert b'Version=2010-05-08' in request.data, f"Expected IAM API version 2010-05-08, got: {request.data}"
assert b'Action=ListRoles' in request.data, f"Expected Action=ListRoles, got: {request.data}"
assert request.method == 'POST', f"Expected POST method, got: {request.method}"

print("iam_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'iam_signature_valid=True' in result.stdout

    def test_secrets_manager_request_uses_json_format(self):
        """Verify Secrets Manager requests use JSON format with X-Amz-Target."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_json_api_request_with_signing(
    'secretsmanager', 'ListSecrets', 'secretsmanager.us-east-1.amazonaws.com', {}
)

# Validate request format (JSON API style)
assert request.method == 'POST', f"Expected POST method, got: {request.method}"
assert 'X-amz-target' in request.headers or 'X-Amz-Target' in request.headers, f"Expected X-Amz-Target header, got: {list(request.headers.keys())}"

print("secrets_signature_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'secrets_signature_valid=True' in result.stdout

    def test_request_includes_required_aws_signature_headers(self):
        """Verify requests include required AWS Signature V4 headers."""
        test_script = """
import sys
sys.path.insert(0, 'src/auth_between_aws_and_github')
import auth_between_aws_and_github as bootstrap

client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'test')
request = client._prepare_query_api_request_with_signing(
    'sts', 'GetCallerIdentity', 'sts.us-east-1.amazonaws.com', {}
)

# Validate AWS Signature V4 headers (case-insensitive check)
headers_lower = {k.lower(): v for k, v in request.headers.items()}
assert 'authorization' in headers_lower, f"Missing Authorization header, got: {list(request.headers.keys())}"
assert 'AWS4-HMAC-SHA256' in request.headers.get('Authorization', ''), "Authorization should use AWS4-HMAC-SHA256"
assert 'x-amz-date' in headers_lower, f"Missing x-amz-date header, got: {list(request.headers.keys())}"
assert 'content-type' in headers_lower, f"Missing Content-Type header, got: {list(request.headers.keys())}"

# Validate host
assert request.host == 'sts.us-east-1.amazonaws.com', f"Expected host sts.us-east-1.amazonaws.com, got: {request.host}"

print("signature_headers_valid=True")
"""
        result = run_command(['python3', '-c', test_script], check=True, capture_output=True)
        assert 'signature_headers_valid=True' in result.stdout

# ==============================================================================
# AWS API Integration Tests (Real AWS API Calls - Read-Only)
# ==============================================================================

import os
import sys
import json


def is_github_actions():
    """Check if running in GitHub Actions."""
    return os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'


def get_aws_credentials():
    """Get AWS credentials from environment or OIDC.

    Returns:
        tuple: (access_key, secret_key, session_token, region) or None if unavailable
    """
    # Try direct credentials first (local development)
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    session_token = os.environ.get('AWS_SESSION_TOKEN')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    if access_key and secret_key:
        return (access_key, secret_key, session_token, region)

    # Try OIDC in GitHub Actions (warm state)
    if is_github_actions():
        try:
            # Get config
            config_path = REPO_ROOT / 'config' / 'auth_between_aws_and_github.json'
            with open(config_path) as f:
                config = json.load(f)

            account_id = config['aws']['account_id']
            role_name = config['aws']['iam_role_name']
            region = config['aws']['region']

            # Add src/auth_between_aws_and_github to path if not already
            sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
            import auth_between_aws_and_github as bootstrap

            # Assume role with OIDC (this calls get_oidc_token() internally)
            temp_creds = bootstrap.assume_role_with_oidc(account_id, region, role_name)
            if temp_creds:
                return (
                    temp_creds['access_key_id'],
                    temp_creds['secret_access_key'],
                    temp_creds['session_token'],
                    region
                )
        except Exception as e:
            # Log the exception for debugging
            import logging
            logging.warning("OIDC authentication failed in integration tests: %s", e)
            # OIDC not available or failed - tests will skip
            pass

    return None


def has_aws_credentials():
    """Check if AWS credentials are available (direct or via OIDC)."""
    return get_aws_credentials() is not None


def get_github_pat():
    """Get GitHub PAT from environment or AWS Secrets Manager.

    Returns:
        str: GitHub PAT or None if unavailable
    """
    # Try environment variable first (local development, COLD state)
    pat = os.environ.get('GH_RUNNER_PAT')
    if pat:
        return pat

    # Try AWS Secrets Manager (GitHub Actions WARM state)
    if is_github_actions():
        try:
            creds = get_aws_credentials()
            if not creds:
                return None

            access_key, secret_key, session_token, region = creds

            # Get secret name from config
            config_path = REPO_ROOT / 'config' / 'auth_between_aws_and_github.json'
            with open(config_path) as f:
                config = json.load(f)

            secret_name = config['aws']['secrets_manager']['github_pat_secret_name']

            # Add src/auth_between_aws_and_github to path if not already
            sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
            import auth_between_aws_and_github as bootstrap

            # Retrieve PAT from Secrets Manager
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


def has_github_pat():
    """Check if GitHub PAT is available (from env or Secrets Manager)."""
    return get_github_pat() is not None


class TestAWSAPIIntegration:
    """Integration tests for AWS API (real API calls - read-only operations)."""

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_sts_get_caller_identity_works(self):
        """Integration: Verify STS GetCallerIdentity works with real credentials."""
        creds = get_aws_credentials()
        assert creds is not None, "Credentials should be available"
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.STSClient(region, access_key, secret_key, session_token)

        # This is READ-ONLY - just validates credentials work
        # Should not raise exception
        client.test_sts_access()

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_get_account_id_returns_numeric_value(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        assert account_id.isdigit()

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_get_account_id_returns_twelve_digits(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        assert len(account_id) == 12

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_validate_access_with_real_credentials(self):
        """Integration: Verify validate_access works with real credentials.
        
        This test validates integration with:
        - STS API (GetCallerIdentity)
        - IAM API (ListRoles) - Would have caught the regional endpoint bug!
        - Secrets Manager API (ListSecrets) - Would have caught the JSON format bug!
        """
        creds = get_aws_credentials()
        assert creds is not None, "Credentials should be available"
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        # This is READ-ONLY - tests STS, IAM, and Secrets Manager access
        # Should not raise if credentials have proper permissions
        client.validate_access()


class TestAWSStateDetectionIntegration:
    """Integration tests for AWS infrastructure state detection (read-only)."""

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_oidc_provider_exists_returns_boolean(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)
        account_id = client.get_account_id()

        exists = client.iam.oidc_provider_exists(account_id)
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_role_exists_returns_boolean(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_role_exists_returns_false_for_nonexistent_role(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.iam.role_exists('NonExistentRoleThatShouldNeverExist12345')
        assert exists is False

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_secret_exists_returns_boolean(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.secrets.secret_exists('non-existent-secret-12345')
        assert isinstance(exists, bool)

    @pytest.mark.skipif(not has_aws_credentials(), reason="No AWS credentials available")
    def test_secret_exists_returns_false_for_nonexistent_secret(self):
        creds = get_aws_credentials()
        access_key, secret_key, session_token, region = creds

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        client = bootstrap.AWSClientStdlib(region, access_key, secret_key, session_token)

        exists = client.secrets.secret_exists('non-existent-secret-12345')
        assert exists is False


class TestGitHubAPIIntegration:
    """Integration tests for GitHub API (real API calls - read-only)."""

    @pytest.mark.skipif(not has_github_pat(), reason="No GitHub PAT available")
    def test_github_pat_validation_with_real_api(self):
        """Integration: Verify GitHub PAT validation works with real GitHub API."""
        github_token = get_github_pat()
        assert github_token is not None, "GitHub PAT should be available"

        sys.path.insert(0, str(REPO_ROOT / 'src' / 'auth_between_aws_and_github'))
        import auth_between_aws_and_github as bootstrap

        # Makes real GitHub API call to validate token scopes
        # This is READ-ONLY - only reads token scopes
        # Should not raise if token has correct scopes
        bootstrap.validate_github_pat(github_token)
