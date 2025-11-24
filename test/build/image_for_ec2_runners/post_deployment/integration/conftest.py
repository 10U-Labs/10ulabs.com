import os
import time
import pytest


@pytest.fixture(scope="module")
def ami_details(ec2_client, test_ami_id):
    if not test_ami_id:
        return None
    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    if response["Images"]:
        return response["Images"][0]
    return None


@pytest.fixture(scope="module")
def test_instance(ec2_client, test_ami_id, tfvars):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    subnet_id = os.environ.get("TEST_SUBNET_ID", "")
    if not subnet_id:
        pytest.fail("TEST_SUBNET_ID environment variable not set")

    security_group_id = os.environ.get("TEST_SECURITY_GROUP_ID", "")
    if not security_group_id:
        pytest.fail("TEST_SECURITY_GROUP_ID environment variable not set")

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
                        {"Key": "Name", "Value": "integration-test-instance"},
                        {"Key": "Purpose", "Value": "AMI Integration Testing"},
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

    yield instance_id

    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except Exception:
        pass


def wait_for_ssm_command(ssm_client, command_id, instance_id, max_attempts=8):
    for attempt in range(max_attempts):
        wait_time = 2 ** attempt
        time.sleep(wait_time)

        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        if output["Status"] == "Success":
            return output
        if output["Status"] == "Failed":
            return output

    return None
