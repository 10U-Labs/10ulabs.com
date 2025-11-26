import json
import os
import time
from botocore.exceptions import ClientError
from ec2_helpers import launch_spot_instance, wait_for_instance_ready, terminate_instance_safely
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
    if not tags:
        return None
    for tag in tags:
        if tag["Key"] == key:
            return tag["Value"]
    return None


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
def ami_runner_version_tag(request):
    ami = request.getfixturevalue("fetched_ami")
    result = None
    if ami:
        result = _get_tag_value(ami.get("Tags", []), "RunnerVersion")
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


def get_spot_instance_types(config):
    test_spot_types_env = os.environ.get("TEST_SPOT_INSTANCE_TYPES", "")
    if test_spot_types_env:
        result = json.loads(test_spot_types_env)
    else:
        result = config.get("ec2_spot_instance_types", ["t4g.small"])
    if not isinstance(result, list):
        result = [result]
    return result


def build_launch_config(test_ami_id, config):
    result = {
        "ami_id": test_ami_id,
        "security_group_id": os.environ.get("TEST_SECURITY_GROUP_ID", ""),
        "instance_profile": config.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile"),
        "max_spot_price": config.get("ec2_max_spot_price", "0.05"),
        "tags": [
            {"Key": "Name", "Value": "integration-test-instance"},
            {"Key": "Purpose", "Value": "AMI Integration Testing"},
            {"Key": "ManagedBy", "Value": "pytest"}
        ],
    }
    return result


def try_launch_spot_instance(ec2_client, launch_config, subnet_ids, spot_instance_types):
    instance_id = None
    last_error = None
    for subnet_id in subnet_ids:
        launch_config["subnet_id"] = subnet_id
        for instance_type in spot_instance_types:
            launch_config["instance_type"] = instance_type
            try:
                instance_id = launch_spot_instance(ec2_client, launch_config)
                break
            except ClientError as err:
                last_error = err
        if instance_id:
            break
    return instance_id, last_error


@pytest.fixture(scope="session")
def test_instance(ec2_client, ssm_client, test_ami_id, config):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    subnet_ids = get_subnet_ids()
    if not subnet_ids:
        pytest.fail("TEST_SUBNET_IDS or TEST_SUBNET_ID environment variable not set")

    if not os.environ.get("TEST_SECURITY_GROUP_ID", ""):
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

    spot_instance_types = get_spot_instance_types(config)
    launch_config = build_launch_config(test_ami_id, config)
    instance_id, last_error = try_launch_spot_instance(ec2_client, launch_config, subnet_ids, spot_instance_types)

    if not instance_id:
        pytest.fail(f"Could not launch spot instance with types {spot_instance_types} in subnets {subnet_ids}. Last error: {last_error}")

    wait_for_instance_ready(ec2_client, instance_id)
    wait_for_ssm_ready(ssm_client, instance_id)

    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
