import json
import os
import time
import boto3
import pytest


@pytest.fixture(scope="module")
def tfvars():
    import re
    tfvars_path = os.path.join(os.path.dirname(__file__), "../../../../src/api/terraform.tfvars")
    config = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('['):
                        value = eval(value)
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    config[key] = value
    return config


@pytest.fixture(scope="module")
def aws_region(tfvars):
    return tfvars["aws_region"]


@pytest.fixture(scope="module")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="module")
def ssm_client(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="module")
def logs_client(aws_region):
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(scope="module")
def test_ami_id():
    ami_id = os.environ.get("TEST_AMI_ID", "")
    return ami_id


@pytest.fixture(scope="module")
def github_token():
    token = os.environ.get("GITHUB_PAT", "")
    return token


@pytest.fixture(scope="module")
def github_repo(tfvars):
    return os.environ.get("GITHUB_REPOSITORY", "10U-Labs-LLC/10ulabs.com")


@pytest.fixture(scope="module")
def test_instance(ec2_client, test_ami_id, tfvars, github_token, github_repo):
    import subprocess
    import base64
    import urllib.request
    import urllib.error

    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    if not github_token:
        pytest.fail("GITHUB_PAT not provided")

    try:
        terraform_dir = os.path.join(os.path.dirname(__file__), "../../../../src/api")
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True
        )
        terraform_outputs = json.loads(result.stdout)
        subnet_ids_str = terraform_outputs.get("vpc_public_subnet_ids", {}).get("value", "")
        subnet_ids = subnet_ids_str.split(",") if subnet_ids_str else []
        security_group_id = terraform_outputs.get("runner_security_group_id", {}).get("value", "")
    except Exception as e:
        pytest.fail(f"Could not get infrastructure info from Terraform outputs: {e}")

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

    if not subnet_ids or not security_group_id:
        pytest.fail("Required infrastructure not configured")

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
                SubnetId=subnet_ids[0].strip(),
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


def test_github_runner_can_register(ssm_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 300
    start_time = time.time()
    runner_configured = False

    while time.time() - start_time < max_wait_time:
        try:
            response = ssm_client.send_command(
                InstanceIds=[test_instance],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": ["test -f /home/github-runner/actions-runner/.runner && echo 'configured' || echo 'not configured'"]}
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(5)

            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=test_instance
            )

            if output["Status"] == "Success" and "configured" in output["StandardOutputContent"]:
                runner_configured = True
                break
        except Exception:
            pass

        time.sleep(15)

    assert runner_configured


def test_github_runner_process_is_running(ssm_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 300
    start_time = time.time()
    runner_running = False

    while time.time() - start_time < max_wait_time:
        try:
            response = ssm_client.send_command(
                InstanceIds=[test_instance],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": ["pgrep -f 'Runner.Listener' && echo 'running' || echo 'not running'"]}
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(5)

            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=test_instance
            )

            if output["Status"] == "Success" and "running" in output["StandardOutputContent"]:
                runner_running = True
                break
        except Exception:
            pass

        time.sleep(15)

    assert runner_running


def test_ssm_session_manager_connection_works(ssm_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["echo 'SSM Session Manager Test'"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "SSM Session Manager Test"


def test_cloudwatch_agent_status_check(ssm_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"
    assert "status" in output["StandardOutputContent"]


def test_docker_can_run_containers_as_github_runner(ssm_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["sudo -u github-runner docker run --rm hello-world"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(10)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"
