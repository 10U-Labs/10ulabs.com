"""Pre-deployment tests for VPC Terraform configuration."""
import re


def test_vpc_tf_defines_vpc_resource(bootstrap_dir):
    """Test that vpc.tf defines the VPC resource."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_vpc"\s+"main"'
    assert re.search(pattern, content) is not None


def test_vpc_tf_defines_public_subnets(bootstrap_dir):
    """Test that vpc.tf defines public subnets."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_subnet"\s+"public"'
    assert re.search(pattern, content) is not None


def test_vpc_tf_defines_internet_gateway(bootstrap_dir):
    """Test that vpc.tf defines an internet gateway."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_internet_gateway"\s+"main"'
    assert re.search(pattern, content) is not None


def test_vpc_tf_defines_route_table(bootstrap_dir):
    """Test that vpc.tf defines a route table."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_route_table"\s+"public"'
    assert re.search(pattern, content) is not None


def test_vpc_tf_defines_security_group(bootstrap_dir):
    """Test that vpc.tf defines the runner security group."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    pattern = r'resource\s+"aws_security_group"\s+"runner"'
    assert re.search(pattern, content) is not None


def test_vpc_uses_correct_cidr_block(bootstrap_dir):
    """Test that VPC uses the expected CIDR block."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert '10.0.0.0/16' in content


def test_vpc_enables_dns_hostnames(bootstrap_dir):
    """Test that VPC enables DNS hostnames."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert 'enable_dns_hostnames = true' in content


def test_vpc_enables_dns_support(bootstrap_dir):
    """Test that VPC enables DNS support."""
    vpc_tf = bootstrap_dir / "vpc.tf"
    content = vpc_tf.read_text()
    assert 'enable_dns_support   = true' in content


def test_outputs_contains_vpc_id(bootstrap_dir):
    """Test that outputs.tf contains vpc_id output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"vpc_id"'
    assert re.search(pattern, content) is not None


def test_outputs_contains_vpc_public_subnet_ids(bootstrap_dir):
    """Test that outputs.tf contains vpc_public_subnet_ids output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"vpc_public_subnet_ids"'
    assert re.search(pattern, content) is not None


def test_outputs_contains_runner_security_group_id(bootstrap_dir):
    """Test that outputs.tf contains runner_security_group_id output."""
    outputs_tf = bootstrap_dir / "outputs.tf"
    content = outputs_tf.read_text()
    pattern = r'output\s+"runner_security_group_id"'
    assert re.search(pattern, content) is not None
