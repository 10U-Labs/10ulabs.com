import os
import time
from botocore.exceptions import ClientError
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


def launch_spot_instance(ec2_client, config):
    response = ec2_client.run_instances(
        ImageId=config["ami_id"],
        InstanceType=config["instance_type"],
        MinCount=1,
        MaxCount=1,
        SubnetId=config["subnet_id"],
        SecurityGroupIds=[config["security_group_id"]],
        IamInstanceProfile={"Name": config["instance_profile"]},
        InstanceMarketOptions={
            "MarketType": "spot",
            "SpotOptions": {
                "MaxPrice": config["max_spot_price"],
                "SpotInstanceType": "one-time"
            }
        },
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Name", "Value": "integration-test-instance"},
                {"Key": "Purpose", "Value": "AMI Integration Testing"},
                {"Key": "ManagedBy", "Value": "pytest"}
            ]
        }]
    )
    return response["Instances"][0]["InstanceId"]


def terminate_instance_safely(ec2_client, instance_id):
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except ClientError:
        pass


def wait_for_instance_ready(ec2_client, instance_id):
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
                return True
        time.sleep(15)
    return False


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


@pytest.fixture(scope="session")
def test_instance(ec2_client, ssm_client, test_ami_id, config):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    subnet_id = os.environ.get("TEST_SUBNET_ID", "")
    if not subnet_id:
        pytest.fail("TEST_SUBNET_ID environment variable not set")

    security_group_id = os.environ.get("TEST_SECURITY_GROUP_ID", "")
    if not security_group_id:
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

    instance_profile = config.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile")
    spot_instance_types = config.get("ec2_spot_instance_types", ["t4g.small"])
    max_spot_price = config.get("ec2_max_spot_price", "0.05")

    if not isinstance(spot_instance_types, list):
        spot_instance_types = [spot_instance_types]

    instance_id = None
    last_error = None
    launch_config = {
        "ami_id": test_ami_id,
        "subnet_id": subnet_id,
        "security_group_id": security_group_id,
        "instance_profile": instance_profile,
        "max_spot_price": max_spot_price,
    }

    for instance_type in spot_instance_types:
        launch_config["instance_type"] = instance_type
        try:
            instance_id = launch_spot_instance(ec2_client, launch_config)
            break
        except ClientError as err:
            last_error = err

    if not instance_id:
        pytest.fail(f"Could not launch spot instance with any of the configured types: {spot_instance_types}. Last error: {last_error}")

    wait_for_instance_ready(ec2_client, instance_id)
    wait_for_ssm_ready(ssm_client, instance_id)

    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
