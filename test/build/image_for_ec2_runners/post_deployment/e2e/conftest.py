import base64
import json
import os
import urllib.request
import urllib.error
from botocore.exceptions import ClientError
from ec2_helpers import launch_spot_instance, wait_for_instance_ready, terminate_instance_safely
import pytest


def get_registration_token(github_repo, github_token):
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
    user_data_script = f"""#!/bin/bash
exec > /var/log/user-data.log 2>&1
set -ex

echo "=== User data script started at $(date) ==="
echo "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"

cd /home/github-runner/actions-runner

echo "=== Starting config.sh at $(date) ==="
sudo -u github-runner ./config.sh \
    --url "https://github.com/{github_repo}" \
    --token "{registration_token}" \
    --name "e2e-test-runner-$(hostname)" \
    --labels "e2e-test" \
    --ephemeral \
    --unattended
echo "=== config.sh completed at $(date) ==="

echo "=== Starting run.sh at $(date) ==="
sudo -u github-runner ./run.sh &
RUNNER_PID=$!
echo "=== run.sh started with PID $RUNNER_PID ==="
"""
    return base64.b64encode(user_data_script.encode()).decode()


def validate_e2e_inputs(test_ami_id, github_token):
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


def get_subnet_ids():
    subnet_ids_env = os.environ.get("TEST_SUBNET_IDS", "")
    subnet_id_env = os.environ.get("TEST_SUBNET_ID", "")
    if subnet_ids_env:
        result = [s.strip() for s in subnet_ids_env.split(",") if s.strip()]
    elif subnet_id_env:
        result = [subnet_id_env]
    else:
        result = []
    return result


def build_e2e_config(test_ami_id, test_config, github_repo, registration_token):
    env_value = os.environ.get("TEST_SPOT_INSTANCE_TYPES", "")
    spot_types = env_value.split(",") if env_value else []
    result = {
        "ami_id": test_ami_id,
        "subnet_ids": get_subnet_ids(),
        "security_group_id": os.environ.get("TEST_SECURITY_GROUP_ID", ""),
        "instance_profile": test_config.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile"),
        "user_data": create_user_data(github_repo, registration_token),
        "max_spot_price": test_config.get("ec2_max_spot_price", "0.05"),
        "spot_instance_types": spot_types,
        "tags": [
            {"Key": "Name", "Value": "e2e-test-instance"},
            {"Key": "Purpose", "Value": "AMI E2E Testing"},
            {"Key": "ManagedBy", "Value": "pytest"}
        ],
    }
    return result


@pytest.fixture(scope="session")
def e2e_test_instance(ec2_client, test_ami_id, config, github_token, github_repo):
    validate_e2e_inputs(test_ami_id, github_token)

    try:
        registration_token = get_registration_token(github_repo, github_token)
    except (urllib.error.HTTPError, urllib.error.URLError):
        pytest.fail("Unable to get GitHub registration token")

    if not registration_token:
        pytest.fail("Failed to retrieve registration token")

    instance_config = build_e2e_config(test_ami_id, config, github_repo, registration_token)
    instance_id = None
    last_error = None

    for subnet_id in instance_config["subnet_ids"]:
        instance_config["subnet_id"] = subnet_id
        for instance_type in instance_config["spot_instance_types"]:
            instance_config["instance_type"] = instance_type
            try:
                instance_id = launch_spot_instance(ec2_client, instance_config)
                break
            except ClientError as err:
                last_error = err
        if instance_id:
            break

    if not instance_id:
        pytest.fail(f"Could not launch spot instance with types {instance_config['spot_instance_types']} in subnets {instance_config['subnet_ids']}. Last error: {last_error}")

    wait_for_instance_ready(ec2_client, instance_id)
    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
