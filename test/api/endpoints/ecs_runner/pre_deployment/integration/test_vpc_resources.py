"""Tests to validate VPC resources exist for ECS runners."""


def test_runners_outputs_has_vpc_id(runners_outputs):
    """Verify vpc_id output is accessible."""
    assert runners_outputs.get("vpc_id"), "vpc_id output not found in runners"


def test_runners_outputs_has_subnet_ids(runners_outputs):
    """Verify vpc_public_subnet_ids output is accessible."""
    assert runners_outputs.get("vpc_public_subnet_ids"), \
        "vpc_public_subnet_ids output not found in runners"


def test_runners_outputs_has_security_group_id(runners_outputs):
    """Verify runner_security_group_id output is accessible."""
    assert runners_outputs.get("runner_security_group_id"), \
        "runner_security_group_id output not found in runners"


def test_vpc_exists_and_available(ec2_client, runners_outputs):
    """Verify the VPC exists and is available."""
    vpc_id = runners_outputs.get("vpc_id")
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert response["Vpcs"][0]["State"] == "available"


def test_subnets_exist_and_available(ec2_client, runners_outputs):
    """Verify all subnets exist and are available."""
    subnet_ids = runners_outputs.get("vpc_public_subnet_ids").split(",")
    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert all(s["State"] == "available" for s in response["Subnets"])


def test_security_group_exists(ec2_client, runners_outputs):
    """Verify the security group exists."""
    security_group_id = runners_outputs.get("runner_security_group_id")
    response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
    assert response["SecurityGroups"][0]["GroupId"] == security_group_id
