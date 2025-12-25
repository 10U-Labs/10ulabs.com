"""Pre-deployment tests for api/shared/networking VPC Terraform configuration."""
import re


def test_vpc_tf_defines_vpc(api_shared_networking_dir):
    """Test that vpc.tf defines the VPC."""
    vpc_tf = api_shared_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_vpc"\s+"main"'
    assert re.search(pattern, content) is not None


def test_vpc_has_correct_cidr(api_shared_networking_dir):
    """Test that VPC uses the expected CIDR block."""
    locals_tf = api_shared_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "10.0.0.0/16" in content


def test_vpc_has_dns_support(api_shared_networking_dir):
    """Test that VPC has DNS support enabled."""
    vpc_tf = api_shared_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_support   = true" in content


def test_vpc_has_dns_hostnames(api_shared_networking_dir):
    """Test that VPC has DNS hostnames enabled."""
    vpc_tf = api_shared_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_hostnames = true" in content


def test_vpc_has_public_subnets(api_shared_networking_dir):
    """Test that public subnets are defined."""
    vpc_tf = api_shared_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_subnet"\s+"public"'
    assert re.search(pattern, content) is not None


def test_vpc_has_internet_gateway(api_shared_networking_dir):
    """Test that internet gateway is defined."""
    vpc_tf = api_shared_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_internet_gateway"\s+"main"'
    assert re.search(pattern, content) is not None


def test_security_group_defined(api_shared_networking_dir):
    """Test that runner security group is defined."""
    sg_tf = api_shared_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    pattern = r'resource\s+"aws_security_group"\s+"runner"'
    assert re.search(pattern, content) is not None


def test_security_group_has_egress_block(api_shared_networking_dir):
    """Test that security group has egress block defined."""
    sg_tf = api_shared_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "egress" in content


def test_security_group_allows_all_outbound(api_shared_networking_dir):
    """Test that security group allows outbound to all destinations."""
    sg_tf = api_shared_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "0.0.0.0/0" in content
