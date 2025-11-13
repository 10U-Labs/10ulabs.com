
import os
import subprocess
from pathlib import Path

import pytest

from conftest import (
    REPO_ROOT, BOOTSTRAP_SCRIPT, TEST_ACCOUNT_ID, TEST_REGION,
    TEST_ROLE_NAME, TEST_GITHUB_ORG, TEST_GITHUB_REPO, run_command
)


class TestUserInteraction:

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
        try:
            stdout, stderr = proc.communicate(timeout=10)
            assert proc.returncode != 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("create command hung waiting for input (should be non-interactive)")
