"""Post-deployment integration tests for api/shared/runners VPC configuration."""
import boto3


def test_runners_vpc_exists(aws_region):
    """Test that the runners VPC exists."""
    ec2 = boto3.client("ec2", region_name=aws_region)
    response = ec2.describe_vpcs(
        Filters=[
            {"Name": "tag:Purpose", "Values": ["runners"]},
            {"Name": "tag:ManagedBy", "Values": ["terraform"]},
        ]
    )
    assert len(response["Vpcs"]) >= 1


def test_runners_vpc_has_internet_gateway(aws_region):
    """Test that the runners VPC has an internet gateway attached."""
    ec2 = boto3.client("ec2", region_name=aws_region)

    # First get the VPC
    vpcs = ec2.describe_vpcs(
        Filters=[
            {"Name": "tag:Purpose", "Values": ["runners"]},
            {"Name": "tag:ManagedBy", "Values": ["terraform"]},
        ]
    )
    if not vpcs["Vpcs"]:
        assert False, "No runners VPC found"

    vpc_id = vpcs["Vpcs"][0]["VpcId"]

    # Check for attached internet gateway
    igws = ec2.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    )
    assert len(igws["InternetGateways"]) >= 1


def test_runners_security_group_exists(aws_region):
    """Test that the runner security group exists."""
    ec2 = boto3.client("ec2", region_name=aws_region)
    response = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": ["self-hosted-runner-sg"]},
            {"Name": "tag:Purpose", "Values": ["runners"]},
        ]
    )
    assert len(response["SecurityGroups"]) >= 1
