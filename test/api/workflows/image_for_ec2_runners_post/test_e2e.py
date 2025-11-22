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
def test_instance(ec2_client, test_ami_id, tfvars):
    import subprocess
    if not test_ami_id:
        pytest.skip("TEST_AMI_ID not provided")

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
        pytest.skip(f"Could not get infrastructure info from Terraform outputs: {e}")

    instance_profile = tfvars.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile")
    spot_instance_types = tfvars.get("ec2_spot_instance_types", ["t4g.small"])
    max_spot_price = tfvars.get("ec2_max_spot_price", "0.05")

    if not subnet_ids or not security_group_id:
        pytest.skip("Required infrastructure not configured")

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
        pytest.skip(f"Could not launch spot instance with any of the configured types: {spot_instance_types}. Last error: {last_error}")

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


def test_github_runner_can_register(ssm_client, test_instance, github_token, github_repo):
    if not test_instance:
        pytest.skip("Test instance not created")
    if not github_token:
        pytest.skip("GITHUB_PAT not provided")

    import urllib.request
    import urllib.error

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
        pytest.skip("Unable to get GitHub registration token")

    if not registration_token:
        pytest.skip("Failed to retrieve registration token")

    runner_name = f"e2e-test-runner-{int(time.time())}"

    commands = [
        f"cd /home/github-runner/actions-runner",
        f"sudo -u github-runner ./config.sh --url https://github.com/{github_repo} --token {registration_token} --name {runner_name} --labels e2e-test --unattended --ephemeral"
    ]

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [" && ".join(commands)]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(30)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"


def test_github_runner_can_execute_simple_workflow(ssm_client, test_instance, github_token, github_repo):
    if not test_instance:
        pytest.skip("Test instance not created")
    if not github_token:
        pytest.skip("GITHUB_PAT not provided")

    import urllib.request
    import urllib.error

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
        pytest.skip("Unable to get GitHub registration token")

    if not registration_token:
        pytest.skip("Failed to retrieve registration token")

    runner_name = f"e2e-test-runner-{int(time.time())}"

    config_commands = [
        f"cd /home/github-runner/actions-runner",
        f"sudo -u github-runner ./config.sh --url https://github.com/{github_repo} --token {registration_token} --name {runner_name} --labels e2e-test --unattended --ephemeral"
    ]

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [" && ".join(config_commands)]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(30)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    if output["Status"] != "Success":
        pytest.skip("Runner registration failed")

    run_commands = [
        "cd /home/github-runner/actions-runner",
        "timeout 60 sudo -u github-runner ./run.sh --once || true"
    ]

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [" && ".join(run_commands)]},
        TimeoutSeconds=120
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(70)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert "Listening for Jobs" in output["StandardOutputContent"] or "Running listener" in output["StandardOutputContent"]


def test_ssm_session_manager_connection_works(ssm_client, test_instance):
    if not test_instance:
        pytest.skip("Test instance not created")

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


def test_cloudwatch_agent_can_be_started(ssm_client, test_instance):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a query"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"
