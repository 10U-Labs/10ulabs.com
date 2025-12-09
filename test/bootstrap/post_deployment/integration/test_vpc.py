"""Integration tests for VPC configuration."""


def test_vpc_exists(ec2_client, _config):
    """Test that the VPC exists with the expected CIDR block."""
    response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(response['Vpcs']) >= 1


def test_vpc_has_dns_hostnames_enabled(ec2_client, _config):
    """Test that the VPC has DNS hostnames enabled."""
    response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(response['Vpcs']) >= 1
    vpc_id = response['Vpcs'][0]['VpcId']
    attrs = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id,
        Attribute='enableDnsHostnames'
    )
    assert attrs['EnableDnsHostnames']['Value'] is True


def test_vpc_has_dns_support_enabled(ec2_client, _config):
    """Test that the VPC has DNS support enabled."""
    response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(response['Vpcs']) >= 1
    vpc_id = response['Vpcs'][0]['VpcId']
    attrs = ec2_client.describe_vpc_attribute(
        VpcId=vpc_id,
        Attribute='enableDnsSupport'
    )
    assert attrs['EnableDnsSupport']['Value'] is True


def test_public_subnets_exist(ec2_client, _config):
    """Test that public subnets exist in the VPC."""
    # First get the VPC ID
    vpc_response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(vpc_response['Vpcs']) >= 1
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    # Get subnets in this VPC
    subnet_response = ec2_client.describe_subnets(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(subnet_response['Subnets']) >= 1


def test_internet_gateway_exists(ec2_client, _config):
    """Test that an internet gateway is attached to the VPC."""
    # First get the VPC ID
    vpc_response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(vpc_response['Vpcs']) >= 1
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    # Get internet gateways attached to this VPC
    igw_response = ec2_client.describe_internet_gateways(
        Filters=[
            {'Name': 'attachment.vpc-id', 'Values': [vpc_id]}
        ]
    )
    assert len(igw_response['InternetGateways']) >= 1


def test_runner_security_group_exists(ec2_client, _config):
    """Test that the runner security group exists."""
    # First get the VPC ID
    vpc_response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(vpc_response['Vpcs']) >= 1
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    # Get security groups in this VPC with the runner tag
    sg_response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'group-name', 'Values': ['self-hosted-runner-sg']}
        ]
    )
    assert len(sg_response['SecurityGroups']) == 1


def test_runner_security_group_has_egress_rule(ec2_client, _config):
    """Test that the runner security group has egress to anywhere."""
    # First get the VPC ID
    vpc_response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(vpc_response['Vpcs']) >= 1
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    # Get the runner security group
    sg_response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'group-name', 'Values': ['self-hosted-runner-sg']}
        ]
    )
    assert len(sg_response['SecurityGroups']) == 1
    sg = sg_response['SecurityGroups'][0]
    # Check for egress rule allowing all traffic
    has_all_egress = any(
        rule.get('IpProtocol') == '-1' and
        any(ip.get('CidrIp') == '0.0.0.0/0' for ip in rule.get('IpRanges', []))
        for rule in sg['IpPermissionsEgress']
    )
    assert has_all_egress


def test_runner_security_group_has_no_ingress_rules(ec2_client, _config):
    """Test that the runner security group has no ingress rules."""
    # First get the VPC ID
    vpc_response = ec2_client.describe_vpcs(
        Filters=[
            {'Name': 'cidr-block', 'Values': ['10.0.0.0/16']},
            {'Name': 'tag:ManagedBy', 'Values': ['terraform']}
        ]
    )
    assert len(vpc_response['Vpcs']) >= 1
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    # Get the runner security group
    sg_response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'group-name', 'Values': ['self-hosted-runner-sg']}
        ]
    )
    assert len(sg_response['SecurityGroups']) == 1
    sg = sg_response['SecurityGroups'][0]
    # Security group should have no ingress rules (egress only)
    assert len(sg['IpPermissions']) == 0
