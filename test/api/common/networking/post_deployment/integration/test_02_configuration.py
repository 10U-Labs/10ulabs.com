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
        """Verify security group allows all outbound traffic (IPv6)."""
        egress_rules = runners_security_group.get("IpPermissionsEgress", [])

        # Look for a rule that allows all traffic (::/0 for IPv6-only)
        has_all_egress = any(
            any(
                ip_range.get("CidrIpv6") == "::/0"
                for ip_range in rule.get("Ipv6Ranges", [])
            )
            for rule in egress_rules
        )
        sg_id = runners_security_group["GroupId"]
        assert has_all_egress, (
            f"Security group {sg_id} does not allow all egress traffic"
        )

    def test_security_group_allows_ipv4_internet_egress(self, runners_security_group):
        """Verify security group allows IPv4 internet egress (0.0.0.0/0)."""
        egress_rules = runners_security_group.get("IpPermissionsEgress", [])

        has_ipv4_egress = any(
            any(
                ip_range.get("CidrIp") == "0.0.0.0/0"
                for ip_range in rule.get("IpRanges", [])
            )
            for rule in egress_rules
        )
        sg_id = runners_security_group["GroupId"]
        assert has_ipv4_egress, (
            f"Security group {sg_id} does not allow IPv4 internet egress"
        )

    def test_internet_gateway_attachment_state_is_available(
        self, ec2_client, runners_vpc_id
    ):
        """Verify internet gateway attachment state is available."""
        response = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [runners_vpc_id]}]
        )
        igw = response["InternetGateways"][0]
        attachment = igw["Attachments"][0]
        assert attachment["State"] == "available"


class TestSubnetConfiguration:
    """Layer 2: Verify subnet configuration."""

    def test_subnets_have_ipv6_on_creation(self, ec2_client):
        """Verify subnets assign IPv6 addresses on creation (IPv6-only)."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for subnet in response["Subnets"]:
            assert subnet.get("AssignIpv6AddressOnCreation") is True, (
                f"Subnet {subnet['SubnetId']} does not assign IPv6 addresses"
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
        """Verify route table has default IPv6 route (::/0)."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for rt in response["RouteTables"]:
            has_default_route = any(
                route.get("DestinationIpv6CidrBlock") == "::/0"
                for route in rt.get("Routes", [])
            )
            assert has_default_route, (
                f"Route table {rt['RouteTableId']} has no default IPv6 route"
            )

    def test_route_table_default_route_targets_igw(self, ec2_client, runners_vpc_id):
        """Verify default IPv6 route targets an internet gateway."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for rt in response["RouteTables"]:
            for route in rt.get("Routes", []):
                if route.get("DestinationIpv6CidrBlock") == "::/0":
                    gateway_id = route.get("GatewayId", "")
                    assert gateway_id.startswith("igw-"), (
                        f"Route table {rt['RouteTableId']} default route does not "
                        f"target an IGW, got: {gateway_id}"
                    )

    def test_route_table_has_ipv4_default_route(self, ec2_client, runners_vpc_id):
        """Verify route table has IPv4 default route for external services."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for rt in response["RouteTables"]:
            has_ipv4_route = any(
                route.get("DestinationCidrBlock") == "0.0.0.0/0"
                for route in rt.get("Routes", [])
            )
            assert has_ipv4_route, (
                f"Route table {rt['RouteTableId']} has no IPv4 default route"
            )


class TestVpcEndpointsConfiguration:
    """Layer 2: Verify VPC endpoints are configured correctly."""

    def test_logs_endpoint_has_private_dns_enabled(self, logs_vpc_endpoint):
        """Verify CloudWatch Logs endpoint has private DNS enabled."""
        assert logs_vpc_endpoint.get("PrivateDnsEnabled") is True, (
            "CloudWatch Logs endpoint does not have private DNS enabled"
        )

    def test_logs_endpoint_is_interface_type(self, logs_vpc_endpoint):
        """Verify CloudWatch Logs endpoint is Interface type."""
        endpoint_type = logs_vpc_endpoint.get("VpcEndpointType")
        assert endpoint_type == "Interface", (
            f"CloudWatch Logs endpoint type is {endpoint_type}, expected Interface"
        )
