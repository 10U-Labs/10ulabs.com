"""Pre-deployment unit tests for api/common/networking locals.tf."""


def test_locals_file_exists(api_common_networking_dir):
    """Test that locals.tf file exists."""
    locals_tf = api_common_networking_dir / "locals.tf"
    assert locals_tf.exists()


def test_locals_defines_aws_region(api_common_networking_dir):
    """Test that locals.tf defines aws_region."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "aws_region" in content


def test_locals_defines_resource_prefix(api_common_networking_dir):
    """Test that locals.tf defines resource_prefix."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "resource_prefix" in content


def test_locals_defines_vpc_name(api_common_networking_dir):
    """Test that locals.tf defines vpc_name."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "vpc_name" in content


def test_locals_defines_vpc_cidr(api_common_networking_dir):
    """Test that locals.tf defines vpc_cidr."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "vpc_cidr" in content


def test_locals_vpc_cidr_uses_valid_block(api_common_networking_dir):
    """Test that VPC CIDR is a valid block."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "10.0.0.0/16" in content


def test_locals_defines_vpc_max_azs(api_common_networking_dir):
    """Test that locals.tf defines vpc_max_azs."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "vpc_max_azs" in content


def test_locals_defines_public_subnet_cidr_mask(api_common_networking_dir):
    """Test that locals.tf defines public_subnet_cidr_mask."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "public_subnet_cidr_mask" in content


def test_locals_defines_vpc_azs(api_common_networking_dir):
    """Test that locals.tf defines vpc_azs."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "vpc_azs" in content


def test_locals_defines_common_tags(api_common_networking_dir):
    """Test that locals.tf defines common_tags."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "common_tags" in content


def test_locals_common_tags_has_project(api_common_networking_dir):
    """Test that common_tags includes Project."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "Project" in content


def test_locals_common_tags_has_environment(api_common_networking_dir):
    """Test that common_tags includes Environment."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "Environment" in content


def test_locals_common_tags_has_managed_by(api_common_networking_dir):
    """Test that common_tags includes ManagedBy."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "ManagedBy" in content


def test_locals_common_tags_has_component(api_common_networking_dir):
    """Test that common_tags includes Component."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "Component" in content


def test_locals_references_common_module_aws_region(api_common_networking_dir):
    """Test that aws_region comes from common module."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "module.common.aws_region" in content


def test_locals_references_common_module_resource_prefix(api_common_networking_dir):
    """Test that resource_prefix comes from common module."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "module.common.resource_prefix" in content


def test_locals_defines_availability_zones_data_source(api_common_networking_dir):
    """Test that locals.tf defines availability zones data source."""
    locals_tf = api_common_networking_dir / "locals.tf"
    content = locals_tf.read_text()
    assert 'data "aws_availability_zones"' in content
