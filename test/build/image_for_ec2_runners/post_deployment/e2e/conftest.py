import base64
import json
import os
import time
import urllib.request
import urllib.error
import pytest


@pytest.fixture(scope="module")
def e2e_test_instance(ec2_client, test_ami_id, tfvars, github_token, github_repo):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    if not github_token:
        pytest.fail("GITHUB_PAT not provided")

    subnet_id = os.environ.get("TEST_SUBNET_ID", "")
    if not subnet_id:
        pytest.fail("TEST_SUBNET_ID environment variable not set")

    security_group_id = os.environ.get("TEST_SECURITY_GROUP_ID", "")
    if not security_group_id:
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

    req = urllib.request.Request(
        f"https://api.github.com/repos/{github_repo}/actions/runners/registration-token",
        method="POST",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            registration_token = data.get("token", "")
    except (urllib.error.HTTPError, urllib.error.URLError):
        pytest.fail("Unable to get GitHub registration token")

    if not registration_token:
        pytest.fail("Failed to retrieve registration token")

    aws_region = tfvars.get("aws_region", "us-east-1")
    user_data_script = f"""#!/bin/bash
set -e

cd /home/github-runner/actions-runner

sudo -u github-runner ./config.sh \
    --url "https://github.com/{github_repo}" \
    --token "{registration_token}" \
    --name "e2e-test-runner-$(hostname)" \
    --labels "e2e-test" \
    --ephemeral \
    --unattended

sudo -u github-runner ./run.sh

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --region {aws_region} \
    || shutdown -h now
"""

    user_data_encoded = base64.b64encode(user_data_script.encode()).decode()

    instance_profile = tfvars.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile")
    spot_instance_types = tfvars.get("ec2_spot_instance_types", ["t4g.small"])
    max_spot_price = tfvars.get("ec2_max_spot_price", "0.05")

    if not isinstance(spot_instance_types, list):
        spot_instance_types = [spot_instance_types]

    instance_id = None
    last_error = None

    for instance_type in spot_instance_types:
        try:
            response = ec2_client.run_instances(
                ImageId=test_ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                SubnetId=subnet_id,
                SecurityGroupIds=[security_group_id],
                IamInstanceProfile={"Name": instance_profile},
                UserData=user_data_encoded,
                InstanceMarketOptions={
                    "MarketType": "spot",
                    "SpotOptions": {
                        "MaxPrice": max_spot_price,
                        "SpotInstanceType": "one-time"
                    }
                },
                TagSpecifications=[{
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "e2e-test-instance"},
                        {"Key": "Purpose", "Value": "AMI E2E Testing"},
                        {"Key": "ManagedBy", "Value": "pytest"}
                    ]
                }]
            )
            instance_id = response["Instances"][0]["InstanceId"]
            break
        except Exception as e:
            last_error = e
            continue

    if not instance_id:
        pytest.fail(f"Could not launch spot instance with any of the configured types: {spot_instance_types}. Last error: {last_error}")

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 15, "MaxAttempts": 40})

    max_wait_time = 600
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            instance_status = status.get("InstanceStatus", {}).get("Status", "")
            system_status = status.get("SystemStatus", {}).get("Status", "")
            if instance_status == "ok" and system_status == "ok":
                break
        time.sleep(15)

    yield instance_id

    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except Exception:
        pass
