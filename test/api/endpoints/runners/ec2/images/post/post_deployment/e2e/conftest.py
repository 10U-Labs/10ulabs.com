"""E2E test fixtures for EC2 runner AMI."""
import base64
import json
import os
import urllib.request
import urllib.error
import pytest
from test.api.endpoints.runners.ec2.images.post.post_deployment.conftest import (
    launch_instance,
    wait_for_instance_ready,
    terminate_instance_safely,
    get_subnet_ids,
    get_instance_types,
)


def get_registration_token(github_repo, github_token):
    """Get a GitHub Actions runner registration token."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{github_repo}/actions/runners/registration-token",
        method="POST",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        return data.get("token", "")


def create_user_data(github_repo, registration_token):
    """Create base64-encoded user data script for runner setup."""
    user_data_script = f"""#!/bin/bash
exec > /var/log/user-data.log 2>&1
set -ex

echo "=== User data script started at $(date) ==="
echo "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"

echo "=== Detecting NVMe instance store ==="
INSTANCE_STORE=$(lsblk -dn -o NAME,TYPE | awk '$2=="disk" {{print "/dev/"$1}}' | while read dev; do
    if [ -z "$(lsblk -n "$dev" -o MOUNTPOINT 2>/dev/null | tr -d ' ')" ]; then
        echo "$dev"
        break
    fi
done)
echo "Found instance store: $INSTANCE_STORE"

echo "=== Setting up NVMe instance store ==="
mkfs.ext4 -F "$INSTANCE_STORE"
mount "$INSTANCE_STORE" /mnt
cp -a /home/github-runner/. /mnt/
umount /mnt
mount "$INSTANCE_STORE" /home/github-runner
chown -R github-runner:github-runner /home/github-runner

cd /home/github-runner/actions-runner

echo "=== Starting config.sh at $(date) ==="
sudo -u github-runner ./config.sh \\
    --url "https://github.com/{github_repo}" \\
    --token "{registration_token}" \\
    --name "e2e-test-runner-$(hostname)" \\
    --labels "e2e-test" \\
    --ephemeral \\
    --unattended
echo "=== config.sh completed at $(date) ==="

echo "=== Starting run.sh at $(date) ==="
sudo -u github-runner ./run.sh &
RUNNER_PID=$!
echo "=== run.sh started with PID $RUNNER_PID ==="
"""
    return base64.b64encode(user_data_script.encode()).decode()


def validate_e2e_inputs(test_ami_id, github_token):
    """Validate required E2E test inputs."""
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")
    if not github_token:
        pytest.fail("GITHUB_PAT not provided")
    subnet_ids_env = os.environ.get("TEST_SUBNET_IDS", "")
    subnet_id_env = os.environ.get("TEST_SUBNET_ID", "")
    if not subnet_ids_env and not subnet_id_env:
        pytest.fail("TEST_SUBNET_IDS or TEST_SUBNET_ID environment variable not set")
    if not os.environ.get("TEST_SECURITY_GROUP_ID", ""):
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")


def build_e2e_config(test_ami_id, test_config, github_repo, registration_token):
    """Build configuration dict for E2E test instance."""
    result = {
        "ami_id": test_ami_id,
        "subnet_ids": get_subnet_ids(),
        "security_group_id": os.environ.get("TEST_SECURITY_GROUP_ID", ""),
        "instance_profile": test_config.get(
            "github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile"
        ),
        "user_data": create_user_data(github_repo, registration_token),
        "instance_types": get_instance_types(),
        "tags": [
            {"Key": "Name", "Value": "e2e-test-instance"},
            {"Key": "Purpose", "Value": "AMI E2E Testing"},
            {"Key": "ManagedBy", "Value": "pytest"}
        ],
    }
    return result


@pytest.fixture(scope="session")
def e2e_test_instance(ec2_client, test_ami_id, config, github_token, github_repo):
    """Create and manage E2E test EC2 instance for the session."""
    validate_e2e_inputs(test_ami_id, github_token)

    try:
        registration_token = get_registration_token(github_repo, github_token)
    except (urllib.error.HTTPError, urllib.error.URLError):
        pytest.fail("Unable to get GitHub registration token")

    if not registration_token:
        pytest.fail("Failed to retrieve registration token")

    instance_config = build_e2e_config(test_ami_id, config, github_repo, registration_token)
    instance_id = launch_instance(ec2_client, instance_config)

    wait_for_instance_ready(ec2_client, instance_id)
    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
