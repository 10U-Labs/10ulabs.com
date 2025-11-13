#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
BOOTSTRAP_SCRIPT = REPO_ROOT / 'auth_between_aws_and_github' / 'auth_between_aws_and_github.py'
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
