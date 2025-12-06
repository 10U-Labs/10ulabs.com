"""Integration test fixtures for EC2 runner AMI."""
# pylint: disable=duplicate-code,missing-function-docstring,line-too-long,import-error
import os
import time
from ec2_helpers import launch_instance, wait_for_instance_ready, terminate_instance_safely
import pytest


@pytest.fixture(scope="session")
def fetched_ami(ec2_client, test_ami_id):
    result = None
    if test_ami_id:
        response = ec2_client.describe_images(ImageIds=[test_ami_id])
        if response["Images"]:
            result = response["Images"][0]
    return result


def _get_tag_value(tags, key):
    result = None
    if tags:
        for tag in tags:
            if tag["Key"] == key:
                result = tag["Value"]
                break
    return result


@pytest.fixture(scope="session")
def ami_tags_dict(request):
    ami = request.getfixturevalue("fetched_ami")
    result = {}
    if ami:
        tags = ami.get("Tags", [])
        for tag in tags:
            result[tag["Key"]] = tag["Value"]
    return result


@pytest.fixture(scope="session")
def ami_purpose_tag(request):
    ami = request.getfixturevalue("fetched_ami")
    result = None
    if ami:
        result = _get_tag_value(ami.get("Tags", []), "Purpose")
    return result


@pytest.fixture(scope="session")
def ami_os_family_tag(request):
    ami = request.getfixturevalue("fetched_ami")
    result = None
    if ami:
        result = _get_tag_value(ami.get("Tags", []), "OSFamily")
    return result


@pytest.fixture(scope="session")
def ami_os_version_tag(request):
    ami = request.getfixturevalue("fetched_ami")
    result = None
    if ami:
        result = _get_tag_value(ami.get("Tags", []), "OSVersion")
    return result


@pytest.fixture
def run_ssm_command():
    def _run_command(ssm_client, instance_id, command, retries=8):
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]}
        )
        command_id = response["Command"]["CommandId"]
        result = {"Status": "Timeout", "StandardOutputContent": "", "StandardErrorContent": "Command timed out"}
        for _ in range(retries):
            time.sleep(2)
            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            if output["Status"] in ("Success", "Failed"):
                result = output
                break
        return result
    return _run_command


def wait_for_ssm_ready(ssm_client, instance_id):
    max_attempts = 8
    result = False
    for _ in range(max_attempts):
        response = ssm_client.describe_instance_information(
            Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
        )
        if response["InstanceInformationList"]:
            info = response["InstanceInformationList"][0]
            if info.get("PingStatus") == "Online":
                result = True
                break
        time.sleep(15)
    return result


def get_subnet_ids():
    subnet_ids_env = os.environ.get("TEST_SUBNET_IDS", "")
    subnet_id_env = os.environ.get("TEST_SUBNET_ID", "")
    result = []
    if subnet_ids_env:
        result = [s.strip() for s in subnet_ids_env.split(",") if s.strip()]
    elif subnet_id_env:
        result = [subnet_id_env]
    return result


def get_instance_types():
    """Get instance types from INSTANCE_TYPES environment variable."""
    env_value = os.environ.get("INSTANCE_TYPES", "")
    result = env_value.split(",") if env_value else []
    return result


def build_launch_config(test_ami_id, config):
    """Build launch configuration for integration test instance."""
    result = {
        "ami_id": test_ami_id,
        "security_group_id": os.environ.get("TEST_SECURITY_GROUP_ID", ""),
        "instance_profile": config.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile"),
        "subnet_ids": get_subnet_ids(),
        "instance_types": get_instance_types(),
        "tags": [
            {"Key": "Name", "Value": "integration-test-instance"},
            {"Key": "Purpose", "Value": "AMI Integration Testing"},
            {"Key": "ManagedBy", "Value": "pytest"}
        ],
    }
    return result


@pytest.fixture(scope="session")
def test_instance(ec2_client, ssm_client, test_ami_id, config):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    subnet_ids = get_subnet_ids()
    if not subnet_ids:
        pytest.fail("TEST_SUBNET_IDS or TEST_SUBNET_ID environment variable not set")

    if not os.environ.get("TEST_SECURITY_GROUP_ID", ""):
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

    launch_config = build_launch_config(test_ami_id, config)
    instance_id = launch_instance(ec2_client, launch_config)

    wait_for_instance_ready(ec2_client, instance_id)
    wait_for_ssm_ready(ssm_client, instance_id)

    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
