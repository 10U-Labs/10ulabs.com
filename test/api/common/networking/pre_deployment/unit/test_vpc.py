"""Pre-deployment unit tests for api/common/networking vpc.tf."""
import re


def test_vpc_file_exists(api_common_networking_dir):
    """Test that vpc.tf file exists."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    assert vpc_tf.exists()


def test_vpc_defines_vpc_resource(api_common_networking_dir):
    """Test that vpc.tf defines the VPC resource."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_vpc"\s+"main"'
    assert re.search(pattern, content) is not None


def test_vpc_uses_cidr_from_locals(api_common_networking_dir):
    """Test that VPC uses CIDR block from locals."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "local.vpc_cidr" in content


def test_vpc_has_dns_support_enabled(api_common_networking_dir):
    """Test that VPC has DNS support enabled."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_support" in content


def test_vpc_dns_support_is_true(api_common_networking_dir):
    """Test that VPC DNS support is true."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_support" in content and "= true" in content


def test_vpc_has_dns_hostnames_enabled(api_common_networking_dir):
    """Test that VPC has DNS hostnames enabled."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_hostnames" in content


def test_vpc_dns_hostnames_is_true(api_common_networking_dir):
    """Test that VPC DNS hostnames is true."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "enable_dns_hostnames" in content and "= true" in content


def test_vpc_has_tags(api_common_networking_dir):
    """Test that VPC has tags configured."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "tags" in content


def test_vpc_defines_subnets(api_common_networking_dir):
    """Test that vpc.tf defines public subnets."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_subnet"\s+"public"'
    assert re.search(pattern, content) is not None


def test_subnets_use_count(api_common_networking_dir):
    """Test that subnets use count for multiple AZs."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "count" in content


def test_subnets_reference_vpc(api_common_networking_dir):
    """Test that subnets reference the VPC."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "aws_vpc.main.id" in content


def test_subnets_have_map_public_ip_disabled(api_common_networking_dir):
    """Test that subnets do NOT map public IPv4 (IPv6-only)."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "map_public_ip_on_launch         = false" in content


def test_vpc_has_ipv6_cidr_block(api_common_networking_dir):
    """Test that VPC has IPv6 CIDR block enabled."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "assign_generated_ipv6_cidr_block = true" in content


def test_subnets_have_ipv6_cidr_block(api_common_networking_dir):
    """Test that subnets have IPv6 CIDR blocks."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "ipv6_cidr_block" in content


def test_subnets_assign_ipv6_on_creation(api_common_networking_dir):
    """Test that subnets assign IPv6 addresses on creation."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "assign_ipv6_address_on_creation = true" in content


def test_vpc_defines_internet_gateway(api_common_networking_dir):
    """Test that vpc.tf defines internet gateway."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_internet_gateway"\s+"main"'
    assert re.search(pattern, content) is not None


def test_internet_gateway_references_vpc(api_common_networking_dir):
    """Test that internet gateway references the VPC."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "vpc_id = aws_vpc.main.id" in content


def test_vpc_defines_route_table(api_common_networking_dir):
    """Test that vpc.tf defines route table."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_route_table"\s+"public"'
    assert re.search(pattern, content) is not None


def test_route_table_has_ipv6_default_route(api_common_networking_dir):
    """Test that route table has IPv6 default route."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "::/0" in content


def test_route_table_has_no_ipv4_route(api_common_networking_dir):
    """Test that route table has no IPv4 default route (IPv6-only)."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "0.0.0.0/0" not in content


def test_route_table_references_igw(api_common_networking_dir):
    """Test that route table default route references IGW."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert "aws_internet_gateway.main.id" in content


def test_vpc_defines_route_table_association(api_common_networking_dir):
    """Test that vpc.tf defines route table association."""
    vpc_tf = api_common_networking_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_route_table_association"\s+"public"'
    assert re.search(pattern, content) is not None
