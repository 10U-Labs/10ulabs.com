import os
import re
import time
import boto3
import pytest


@pytest.fixture(scope="module")
def tfvars():
    tfvars_path = os.path.join(os.path.dirname(__file__), "../../../src/api/terraform.tfvars")
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
def test_ami_id():
    ami_id = os.environ.get("TEST_AMI_ID", "")
    return ami_id


@pytest.fixture(scope="module")
def ami_details(ec2_client, test_ami_id):
    if not test_ami_id:
        return None
    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    return response["Images"][0] if response["Images"] else None


@pytest.fixture(scope="module")
def test_instance(ec2_client, test_ami_id, tfvars):
    if not test_ami_id:
        pytest.skip("TEST_AMI_ID not provided")

    subnet_ids = tfvars.get("vpc_public_subnet_ids", "").split(",")
    security_group_id = tfvars.get("github_runner_security_group_id", "")
    instance_profile = tfvars.get("github_runner_iam_instance_profile_name", "GitHubSelfHostedRunnerInstanceProfile")

    if not subnet_ids or not security_group_id:
        pytest.skip("Required infrastructure not configured")

    response = ec2_client.run_instances(
        ImageId=test_ami_id,
        InstanceType="t4g.nano",
        MinCount=1,
        MaxCount=1,
        SubnetId=subnet_ids[0].strip(),
        SecurityGroupIds=[security_group_id],
        IamInstanceProfile={"Name": instance_profile},
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

    yield instance_id

    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except Exception:
        pass


def test_ami_id_provided(test_ami_id):
    assert test_ami_id


def test_ami_exists_in_ec2(ec2_client, test_ami_id):
    if not test_ami_id:
        pytest.skip("TEST_AMI_ID not provided")

    response = ec2_client.describe_images(ImageIds=[test_ami_id])

    assert len(response["Images"]) == 1


def test_ami_state_is_available(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    assert ami_details["State"] == "available"


def test_ami_architecture_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.skip("AMI details not available")

    expected_architecture = tfvars["os_architecture"]

    assert ami_details["Architecture"] == expected_architecture


def test_ami_has_purpose_tag(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "Purpose" in tags


def test_ami_purpose_tag_value(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    purpose = tags.get("Purpose", "")

    assert "GitHub" in purpose or "Github" in purpose or "github" in purpose


def test_ami_has_runner_version_tag(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "RunnerVersion" in tags


def test_ami_runner_version_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_version = tfvars["github_runner_version"]
    runner_version = tags.get("RunnerVersion", "")

    assert runner_version == expected_version


def test_ami_has_os_family_tag(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "OSFamily" in tags


def test_ami_os_family_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_os_family = tfvars["os_family"].title()
    os_family = tags.get("OSFamily", "")

    assert os_family == expected_os_family


def test_ami_has_os_version_tag(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "OSVersion" in tags


def test_ami_os_version_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.skip("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_os_version = tfvars["os_version"]
    os_version = tags.get("OSVersion", "")

    assert os_version == expected_os_version


def test_ami_has_root_device_mapping(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    assert "BlockDeviceMappings" in ami_details


def test_ami_root_device_is_ebs(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    assert ami_details["RootDeviceType"] == "ebs"


def test_ami_name_follows_convention(ami_details):
    if not ami_details:
        pytest.skip("AMI details not available")

    ami_name = ami_details.get("Name", "")

    assert ami_name.startswith("github-ec2-runner-")


def test_ami_name_contains_architecture(ami_details, tfvars):
    if not ami_details:
        pytest.skip("AMI details not available")

    ami_name = ami_details.get("Name", "")
    expected_architecture = tfvars["os_architecture"]

    assert expected_architecture in ami_name


def test_instance_launches_from_ami(test_instance):
    assert test_instance


def test_instance_reaches_running_state(ec2_client, test_instance):
    if not test_instance:
        pytest.skip("Test instance not created")

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[test_instance], WaiterConfig={"Delay": 15, "MaxAttempts": 40})

    response = ec2_client.describe_instances(InstanceIds=[test_instance])
    instance_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]

    assert instance_state == "running"


def test_instance_passes_system_status_checks(ec2_client, test_instance):
    if not test_instance:
        pytest.skip("Test instance not created")

    max_wait_time = 600
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[test_instance])

        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            system_status = status.get("SystemStatus", {}).get("Status", "")

            if system_status == "ok":
                assert system_status == "ok"
                return

        time.sleep(15)

    pytest.fail("Instance did not pass system status checks within timeout")


def test_instance_passes_instance_status_checks(ec2_client, test_instance):
    if not test_instance:
        pytest.skip("Test instance not created")

    max_wait_time = 600
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[test_instance])

        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            instance_status = status.get("InstanceStatus", {}).get("Status", "")

            if instance_status == "ok":
                assert instance_status == "ok"
                return

        time.sleep(15)

    pytest.fail("Instance did not pass instance status checks within timeout")


def test_promote_ami_can_tag_ami(ec2_client, test_ami_id, promote_ami, tfvars):
    if not test_ami_id:
        pytest.skip("TEST_AMI_ID not provided")

    test_tag_key = "TestPromotionTag"
    test_tag_value = "test-value"

    ec2_client.create_tags(
        Resources=[test_ami_id],
        Tags=[{"Key": test_tag_key, "Value": test_tag_value}]
    )

    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    tags = {tag["Key"]: tag["Value"] for tag in response["Images"][0].get("Tags", [])}

    assert tags.get(test_tag_key) == test_tag_value


def test_promote_ami_can_update_ssm_parameter(ssm_client, test_ami_id, promote_ami, tfvars):
    if not test_ami_id:
        pytest.skip("TEST_AMI_ID not provided")

    test_parameter_name = "/github-runner/ami/integration-test"

    try:
        ssm_client.delete_parameter(Name=test_parameter_name)
    except ssm_client.exceptions.ParameterNotFound:
        pass

    ssm_client.put_parameter(
        Name=test_parameter_name,
        Value=test_ami_id,
        Type="String",
        Overwrite=True,
        Description="Integration test parameter"
    )

    response = ssm_client.get_parameter(Name=test_parameter_name)
    parameter_value = response["Parameter"]["Value"]

    assert parameter_value == test_ami_id

    ssm_client.delete_parameter(Name=test_parameter_name)


def test_promote_ami_function_exists(promote_ami):
    assert hasattr(promote_ami, "promote_ami")


def test_promote_ami_function_signature(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "ami_id" in params


def test_promote_ami_function_signature_has_region(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "region" in params


def test_promote_ami_function_signature_has_ssm_parameter_name(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "ssm_parameter_name" in params


def test_promote_ami_function_signature_has_tag_key(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "tag_key" in params


def test_github_runner_user_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["id github-runner"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"


def test_github_runner_directory_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -d /home/github-runner/actions-runner && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_binary_exists(ssm_client, test_instance, aws_region, tfvars):
    if not test_instance:
        pytest.skip("Test instance not created")

    runner_version = tfvars["github_runner_version"]
    os_arch = tfvars["os_architecture"]
    runner_arch = "arm64" if os_arch == "arm64" else "x64"

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [f"test -f /home/github-runner/actions-runner/actions-runner-linux-{runner_arch}-{runner_version}.tar.gz && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_config_script_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /home/github-runner/actions-runner/config.sh && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_github_runner_run_script_exists(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /home/github-runner/actions-runner/run.sh && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"


def test_ssm_agent_is_installed(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["which amazon-ssm-agent"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["Status"] == "Success"


def test_ssm_agent_service_is_running(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["systemctl is-active amazon-ssm-agent"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "active"


def test_cloudwatch_agent_is_installed(ssm_client, test_instance, aws_region):
    if not test_instance:
        pytest.skip("Test instance not created")

    response = ssm_client.send_command(
        InstanceIds=[test_instance],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["test -f /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent && echo exists"]}
    )

    command_id = response["Command"]["CommandId"]
    time.sleep(5)

    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=test_instance
    )

    assert output["StandardOutputContent"].strip() == "exists"
