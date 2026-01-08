"""Pre-deployment unit tests for api/common/networking outputs.tf."""


def test_outputs_file_exists(api_common_networking_dir):
    """Test that outputs.tf file exists."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    assert outputs_tf.exists()


def test_outputs_defines_vpc_id(api_common_networking_dir):
    """Test that outputs.tf defines vpc_id output."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert 'output "vpc_id"' in content


def test_outputs_vpc_id_has_description(api_common_networking_dir):
    """Test that vpc_id output has description."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert "description" in content


def test_outputs_vpc_id_references_vpc_resource(api_common_networking_dir):
    """Test that vpc_id output references aws_vpc.main."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert "aws_vpc.main.id" in content


def test_outputs_defines_public_subnets_ids(api_common_networking_dir):
    """Test that outputs.tf defines public_subnets_ids output."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert 'output "public_subnets_ids"' in content


def test_outputs_public_subnets_uses_join(api_common_networking_dir):
    """Test that public_subnets_ids output uses join function."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert "join" in content


def test_outputs_public_subnets_references_subnet_resource(api_common_networking_dir):
    """Test that public_subnets_ids references aws_subnet.public."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert "aws_subnet.public" in content


def test_outputs_defines_security_group_id(api_common_networking_dir):
    """Test that outputs.tf defines security_group_id_for_runners output."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert 'output "security_group_id_for_runners"' in content


def test_outputs_security_group_references_runner_sg(api_common_networking_dir):
    """Test that security_group_id_for_runners references aws_security_group.runner."""
    outputs_tf = api_common_networking_dir / "outputs.tf"
    content = outputs_tf.read_text()
    assert "aws_security_group.runner.id" in content
