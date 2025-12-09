"""Tests to validate VPC resources exist for EC2 runners."""


def test_runners_terraform_outputs_readable(runners_outputs):
    """Verify runners terraform outputs are accessible."""
    assert runners_outputs.get("vpc_id"), \
        "vpc_id output not found in runners"
    assert runners_outputs.get("vpc_public_subnet_ids"), \
        "vpc_public_subnet_ids output not found in runners"
    assert runners_outputs.get("runner_security_group_id"), \
        "runner_security_group_id output not found in runners"


def test_vpc_exists(ec2_client, runners_outputs):
    """Verify the VPC exists."""
    vpc_id = runners_outputs.get("vpc_id")
    assert vpc_id, "vpc_id output not found"

    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert len(response["Vpcs"]) == 1
    vpc = response["Vpcs"][0]
    assert vpc["VpcId"] == vpc_id
    assert vpc["State"] == "available"


def test_subnets_exist(ec2_client, runners_outputs):
    """Verify all subnets exist."""
    subnet_ids_str = runners_outputs.get("vpc_public_subnet_ids")
    assert subnet_ids_str, "vpc_public_subnet_ids output not found"

    subnet_ids = subnet_ids_str.split(",")
    assert len(subnet_ids) > 0, "No subnet IDs found"

    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert len(response["Subnets"]) == len(subnet_ids)
    for subnet in response["Subnets"]:
        assert subnet["State"] == "available"


def test_security_group_exists(ec2_client, runners_outputs):
    """Verify the security group exists."""
    security_group_id = runners_outputs.get("runner_security_group_id")
    assert security_group_id, "runner_security_group_id output not found"

    response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
    assert len(response["SecurityGroups"]) == 1
    sg = response["SecurityGroups"][0]
    assert sg["GroupId"] == security_group_id
