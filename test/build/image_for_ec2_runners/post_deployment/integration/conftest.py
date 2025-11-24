import os
from botocore.exceptions import ClientError
import pytest


@pytest.fixture(scope="module")
def ami_details(ec2_client, test_ami_id):
    if not test_ami_id:
        return None
    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    if response["Images"]:
        return response["Images"][0]
    return None


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


@pytest.fixture(scope="module")
def test_instance(ec2_client, test_ami_id, tfvars_data):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    subnet_id = os.environ.get("TEST_SUBNET_ID", "")
    if not subnet_id:
        pytest.fail("TEST_SUBNET_ID environment variable not set")

    security_group_id = os.environ.get("TEST_SECURITY_GROUP_ID", "")
    if not security_group_id:
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

    instance_profile = tfvars_data.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile")
    spot_instance_types = tfvars_data.get("ec2_spot_instance_types", ["t4g.small"])
    max_spot_price = tfvars_data.get("ec2_max_spot_price", "0.05")

    if not isinstance(spot_instance_types, list):
        spot_instance_types = [spot_instance_types]

    instance_id = None
    last_error = None
    config = {
        "ami_id": test_ami_id,
        "subnet_id": subnet_id,
        "security_group_id": security_group_id,
        "instance_profile": instance_profile,
        "max_spot_price": max_spot_price,
    }

    for instance_type in spot_instance_types:
        config["instance_type"] = instance_type
        try:
            instance_id = launch_spot_instance(ec2_client, config)
            break
        except ClientError as err:
            last_error = err

    if not instance_id:
        pytest.fail(f"Could not launch spot instance with any of the configured types: {spot_instance_types}. Last error: {last_error}")

    yield instance_id
    terminate_instance_safely(ec2_client, instance_id)
