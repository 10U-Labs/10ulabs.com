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
