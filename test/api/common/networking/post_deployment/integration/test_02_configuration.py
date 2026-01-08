"""Layer 2: Configuration tests for api/common/networking post-deployment.

Tests that resources have correct settings. Assumes existence tests passed.

Three-layer testing model:
- Layer 2: Configuration - Resources configured correctly
"""





class TestDeployedResourcesConfiguration:
    """Layer 2: Verify deployed resources are configured correctly."""

    def test_vpc_has_dns_support_enabled(self, ec2_client, runners_vpc_id):
        """Verify VPC has DNS support enabled."""
        response = ec2_client.describe_vpc_attribute(
            VpcId=runners_vpc_id,
            Attribute="enableDnsSupport"
        )
        assert response["EnableDnsSupport"]["Value"] is True, (
            f"VPC {runners_vpc_id} does not have DNS support enabled"
        )

    def test_vpc_has_dns_hostnames_enabled(self, ec2_client, runners_vpc_id):
        """Verify VPC has DNS hostnames enabled."""
        response = ec2_client.describe_vpc_attribute(
            VpcId=runners_vpc_id,
            Attribute="enableDnsHostnames"
        )
        assert response["EnableDnsHostnames"]["Value"] is True, (
            f"VPC {runners_vpc_id} does not have DNS hostnames enabled"
        )

    def test_vpc_has_expected_cidr(self, runners_vpc):
        """Verify VPC has the expected CIDR block."""
        cidr = runners_vpc["CidrBlock"]
        assert cidr == "10.0.0.0/16", (
            f"VPC has unexpected CIDR block: {cidr}, expected 10.0.0.0/16"
        )

    def test_security_group_allows_all_egress(self, runners_security_group):
        """Verify security group allows all outbound traffic."""
        egress_rules = runners_security_group.get("IpPermissionsEgress", [])

        # Look for a rule that allows all traffic (0.0.0.0/0)
        has_all_egress = any(
            any(
                ip_range.get("CidrIp") == "0.0.0.0/0"
                for ip_range in rule.get("IpRanges", [])
            )
            for rule in egress_rules
        )
        sg_id = runners_security_group["GroupId"]
        assert has_all_egress, (
            f"Security group {sg_id} does not allow all egress traffic"
        )


class TestSubnetConfiguration:
    """Layer 2: Verify subnet configuration."""

    def test_subnets_have_public_ip_mapping(self, ec2_client):
        """Verify subnets assign public IPs to instances."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for subnet in response["Subnets"]:
            assert subnet.get("MapPublicIpOnLaunch") is True, (
                f"Subnet {subnet['SubnetId']} does not assign public IPs"
            )

    def test_subnets_are_in_different_azs(self, ec2_client):
        """Verify subnets are distributed across availability zones."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        azs = [subnet["AvailabilityZone"] for subnet in response["Subnets"]]
        # If there are multiple subnets, they should be in different AZs
        if len(azs) > 1:
            assert len(set(azs)) == len(azs), (
                f"Subnets are not in different AZs: {azs}"
            )


class TestRouteTableConfiguration:
    """Layer 2: Verify route table configuration."""

    def test_route_table_has_default_route(self, ec2_client, runners_vpc_id):
        """Verify route table has default route (0.0.0.0/0)."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for rt in response["RouteTables"]:
            has_default_route = any(
                route.get("DestinationCidrBlock") == "0.0.0.0/0"
                for route in rt.get("Routes", [])
            )
            assert has_default_route, (
                f"Route table {rt['RouteTableId']} has no default route"
            )

    def test_route_table_default_route_targets_igw(self, ec2_client, runners_vpc_id):
        """Verify default route targets an internet gateway."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for rt in response["RouteTables"]:
            for route in rt.get("Routes", []):
                if route.get("DestinationCidrBlock") == "0.0.0.0/0":
                    gateway_id = route.get("GatewayId", "")
                    assert gateway_id.startswith("igw-"), (
                        f"Route table {rt['RouteTableId']} default route does not "
                        f"target an IGW, got: {gateway_id}"
                    )
