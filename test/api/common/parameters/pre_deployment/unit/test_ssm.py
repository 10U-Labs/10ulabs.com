"""Pre-deployment unit tests for api/common/parameters SSM configuration."""
import re


def test_ssm_tf_defines_ssm_parameter(api_common_parameters_dir):
    """Test that ssm.tf defines the SSM parameter resource."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    content = ssm_tf.read_text()
    pattern = r'resource\s+"aws_ssm_parameter"\s+"ec2_runner_ami_latest"'
    assert re.search(pattern, content) is not None


def test_ssm_parameter_uses_local_name(api_common_parameters_dir):
    """Test that SSM parameter uses the local variable for its name."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    content = ssm_tf.read_text()
    assert "local.ssm_ec2_runner_ami_latest" in content


def test_ssm_parameter_type_is_string(api_common_parameters_dir):
    """Test that SSM parameter type is String."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    content = ssm_tf.read_text()
    assert 'type  = "String"' in content


def test_ssm_parameter_has_lifecycle_ignore_value(api_common_parameters_dir):
    """Test that SSM parameter ignores value changes (updated by workflow)."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    content = ssm_tf.read_text()
    assert "ignore_changes = [value]" in content


def test_ssm_parameter_has_tags(api_common_parameters_dir):
    """Test that SSM parameter has tags defined."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    content = ssm_tf.read_text()
    assert "tags = merge(local.common_tags" in content
