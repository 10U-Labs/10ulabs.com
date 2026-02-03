"""Pre-deployment unit tests for api/common/networking vpc_endpoints.tf."""
import re


def test_vpc_endpoints_file_exists(api_common_networking_dir):
    """Test that vpc_endpoints.tf file exists."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    assert vpc_endpoints_tf.exists()


def test_vpc_endpoints_defines_security_group(api_common_networking_dir):
    """Test that vpc_endpoints.tf defines security group for endpoints."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    pattern = r'resource\s+"aws_security_group"\s+"vpc_endpoints"'
    assert re.search(pattern, content) is not None


def test_vpc_endpoints_defines_ecr_api_endpoint(api_common_networking_dir):
    """Test that vpc_endpoints.tf defines ECR API endpoint."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    pattern = r'resource\s+"aws_vpc_endpoint"\s+"ecr_api"'
    assert re.search(pattern, content) is not None


def test_vpc_endpoints_defines_ecr_dkr_endpoint(api_common_networking_dir):
    """Test that vpc_endpoints.tf defines ECR DKR endpoint."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    pattern = r'resource\s+"aws_vpc_endpoint"\s+"ecr_dkr"'
    assert re.search(pattern, content) is not None


def test_vpc_endpoints_defines_s3_endpoint(api_common_networking_dir):
    """Test that vpc_endpoints.tf defines S3 gateway endpoint."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    pattern = r'resource\s+"aws_vpc_endpoint"\s+"s3"'
    assert re.search(pattern, content) is not None


def test_ecr_api_endpoint_uses_interface_type(api_common_networking_dir):
    """Test that ECR API endpoint uses Interface type."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    assert 'vpc_endpoint_type   = "Interface"' in content


def test_s3_endpoint_uses_gateway_type(api_common_networking_dir):
    """Test that S3 endpoint uses Gateway type."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    assert 'vpc_endpoint_type = "Gateway"' in content


def test_ecr_endpoints_have_private_dns_enabled(api_common_networking_dir):
    """Test that ECR endpoints have private DNS enabled."""
    vpc_endpoints_tf = api_common_networking_dir / "vpc_endpoints.tf"
    content = vpc_endpoints_tf.read_text()
    assert "private_dns_enabled = true" in content
