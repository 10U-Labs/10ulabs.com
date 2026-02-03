"""Layer 3: Wiring tests for api/common/networking post-deployment.

Tests that components are connected. Assumes existence and configuration passed.

Three-layer testing model:
- Layer 3: Wiring - Components connected properly
"""





class TestVPCWiring:
    """Layer 3: Verify VPC components are connected."""

    def test_internet_gateway_attached_to_vpc(self, ec2_client, runners_vpc_id):
        """Verify internet gateway is attached to the runners VPC."""
        igws = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [runners_vpc_id]}]
        )
        assert len(igws["InternetGateways"]) >= 1, (
            f"No internet gateway attached to VPC {runners_vpc_id}"
        )

    def test_subnets_in_vpc(self, ec2_client, runners_vpc_id):
        """Verify subnets are in the runners VPC."""
        subnets = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        for subnet in subnets["Subnets"]:
            assert subnet["VpcId"] == runners_vpc_id, (
                f"Subnet {subnet['SubnetId']} is not in VPC {runners_vpc_id}"
            )

    def test_security_group_in_vpc(self, runners_security_group, runners_vpc_id):
        """Verify security group is in the runners VPC."""
        sg_id = runners_security_group["GroupId"]
        assert runners_security_group["VpcId"] == runners_vpc_id, (
            f"Security group {sg_id} is not in VPC {runners_vpc_id}"
        )

    def test_subnets_have_route_to_igw(self, ec2_client, runners_vpc_id):
        """Verify subnets have a route to the internet gateway."""
        # Get internet gateway
        igws = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [runners_vpc_id]}]
        )
        igw_id = igws["InternetGateways"][0]["InternetGatewayId"]

        # Get subnets by tag
        subnets = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )

        # Check each subnet has a route to the IGW
        for subnet in subnets["Subnets"]:
            route_tables = ec2_client.describe_route_tables(
                Filters=[
                    {"Name": "association.subnet-id", "Values": [subnet["SubnetId"]]}
                ]
            )
            # If no explicit association, use the main route table
            if not route_tables["RouteTables"]:
                route_tables = ec2_client.describe_route_tables(
                    Filters=[
                        {"Name": "vpc-id", "Values": [runners_vpc_id]},
                        {"Name": "association.main", "Values": ["true"]},
                    ]
                )

            has_igw_route = any(
                route.get("GatewayId") == igw_id
                for rt in route_tables["RouteTables"]
                for route in rt.get("Routes", [])
            )
            assert has_igw_route, (
                f"Subnet {subnet['SubnetId']} has no route to IGW {igw_id}"
            )


class TestVpcEndpointsWiring:
    """Layer 3: Verify VPC endpoints are wired correctly."""

    def test_logs_endpoint_in_vpc(self, ec2_client, runners_vpc_id, aws_region):
        """Verify CloudWatch Logs endpoint is in the runners VPC."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.logs"]},
            ]
        )
        assert len(response["VpcEndpoints"]) >= 1, (
            f"CloudWatch Logs endpoint not found in VPC {runners_vpc_id}"
        )

    def test_logs_endpoint_has_subnets(self, ec2_client, runners_vpc_id, aws_region):
        """Verify CloudWatch Logs endpoint has subnets attached."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.logs"]},
            ]
        )
        endpoint = response["VpcEndpoints"][0]
        assert len(endpoint.get("SubnetIds", [])) >= 1, (
            "CloudWatch Logs endpoint has no subnets attached"
        )
