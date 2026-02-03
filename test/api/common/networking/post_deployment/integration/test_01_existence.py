"""Layer 1: Existence tests for api/common/networking post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""





class TestVPCResourcesExist:
    """Layer 1: Verify VPC and networking resources exist."""

    def test_runners_vpc_exists(self, runners_vpc):
        """Verify the runners VPC exists."""
        assert runners_vpc is not None, (
            "Runners VPC not found. Run terraform apply in src/api/common/networking/"
        )

    def test_runners_subnets_exist(self, ec2_client):
        """Verify the runners subnets exist."""
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        assert len(response["Subnets"]) >= 1, (
            "Runners subnets not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_runners_internet_gateway_exists(self, ec2_client):
        """Verify the runners internet gateway exists."""
        response = ec2_client.describe_internet_gateways(
            Filters=[
                {"Name": "tag:Purpose", "Values": ["runners"]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        assert len(response["InternetGateways"]) >= 1, (
            "Runners internet gateway not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_runners_security_group_exists(self, runners_security_group):
        """Verify the runner security group exists."""
        assert runners_security_group is not None, (
            "Runner security group not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_runners_route_table_exists(self, ec2_client, runners_vpc_id):
        """Verify the runners route table exists."""
        response = ec2_client.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "tag:ManagedBy", "Values": ["terraform"]},
            ]
        )
        assert len(response["RouteTables"]) >= 1, (
            "Runners route table not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_ecr_api_vpc_endpoint_exists(self, ec2_client, runners_vpc_id, aws_region):
        """Verify the ECR API VPC endpoint exists."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.ecr.api"]},
            ]
        )
        assert len(response["VpcEndpoints"]) >= 1, (
            "ECR API VPC endpoint not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_ecr_dkr_vpc_endpoint_exists(self, ec2_client, runners_vpc_id, aws_region):
        """Verify the ECR DKR VPC endpoint exists."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.ecr.dkr"]},
            ]
        )
        assert len(response["VpcEndpoints"]) >= 1, (
            "ECR DKR VPC endpoint not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_s3_vpc_endpoint_exists(self, ec2_client, runners_vpc_id, aws_region):
        """Verify the S3 VPC endpoint exists."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.s3"]},
            ]
        )
        assert len(response["VpcEndpoints"]) >= 1, (
            "S3 VPC endpoint not found. "
            "Run terraform apply in src/api/common/networking/"
        )

    def test_cloudwatch_logs_vpc_endpoint_exists(self, ec2_client, runners_vpc_id, aws_region):
        """Verify the CloudWatch Logs VPC endpoint exists."""
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {"Name": "vpc-id", "Values": [runners_vpc_id]},
                {"Name": "service-name", "Values": [f"com.amazonaws.{aws_region}.logs"]},
            ]
        )
        assert len(response["VpcEndpoints"]) >= 1, (
            "CloudWatch Logs VPC endpoint not found. "
            "Run terraform apply in src/api/common/networking/"
        )
