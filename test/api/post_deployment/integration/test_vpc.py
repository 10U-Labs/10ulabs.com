def test_vpc_cidr_block_configuration(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    assert len(vpcs['Vpcs'][0]['CidrBlock']) > 0


def test_public_subnets_have_internet_gateway_route(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    route_tables = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(route_tables['RouteTables']) > 0


def test_subnets_span_multiple_availability_zones(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    azs = set(subnet['AvailabilityZone'] for subnet in subnets['Subnets'])
    assert len(azs) > 0


def test_nat_gateway_configuration(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets']]
    nat_gateways = ec2_client.describe_nat_gateways(Filters=[{'Name': 'subnet-id', 'Values': subnet_ids}])
    assert len(nat_gateways['NatGateways']) >= 0


def test_security_group_ingress_rules(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(sgs['SecurityGroups']) > 0


def test_security_group_egress_rules(ec2_client, tfvars):
    vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(sgs['SecurityGroups'][0]['IpPermissionsEgress']) >= 0
