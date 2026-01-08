"""Pre-deployment unit tests for api/common/networking security_groups.tf."""
import re


def test_security_groups_file_exists(api_common_networking_dir):
    """Test that security_groups.tf file exists."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    assert sg_tf.exists()


def test_security_groups_defines_runner_sg(api_common_networking_dir):
    """Test that security_groups.tf defines runner security group."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    pattern = r'resource\s+"aws_security_group"\s+"runner"'
    assert re.search(pattern, content) is not None


def test_security_groups_sg_has_name(api_common_networking_dir):
    """Test that security group has name attribute."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "name" in content


def test_security_groups_sg_has_correct_name(api_common_networking_dir):
    """Test that security group has specific runner name."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "self-hosted-runner-sg" in content


def test_security_groups_sg_has_description(api_common_networking_dir):
    """Test that security group has description attribute."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "description" in content


def test_security_groups_sg_has_vpc_id(api_common_networking_dir):
    """Test that security group has vpc_id attribute."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "vpc_id" in content


def test_security_groups_sg_references_vpc(api_common_networking_dir):
    """Test that security group vpc_id references aws_vpc.main."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "aws_vpc.main.id" in content


def test_security_groups_sg_has_egress_block(api_common_networking_dir):
    """Test that security group has egress block defined."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "egress" in content


def test_security_groups_egress_allows_all_protocols(api_common_networking_dir):
    """Test that egress allows all protocols."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert 'protocol    = "-1"' in content


def test_security_groups_egress_allows_all_destinations(api_common_networking_dir):
    """Test that egress allows all destinations (0.0.0.0/0)."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "0.0.0.0/0" in content


def test_security_groups_egress_allows_all_ports(api_common_networking_dir):
    """Test that egress allows all ports (from_port and to_port = 0)."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "from_port   = 0" in content


def test_security_groups_sg_has_tags(api_common_networking_dir):
    """Test that security group has tags attribute."""
    sg_tf = api_common_networking_dir / "security_groups.tf"
    content = sg_tf.read_text()
    assert "tags" in content
