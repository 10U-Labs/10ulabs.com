"""Pre-deployment unit tests for api/common/parameters Terraform structure."""


def test_backend_tf_exists(api_common_parameters_dir):
    """Test that backend.tf exists."""
    backend_tf = api_common_parameters_dir / "backend.tf"
    assert backend_tf.exists()


def test_providers_tf_exists(api_common_parameters_dir):
    """Test that providers.tf exists."""
    providers_tf = api_common_parameters_dir / "providers.tf"
    assert providers_tf.exists()


def test_shared_tf_exists(api_common_parameters_dir):
    """Test that shared.tf exists."""
    shared_tf = api_common_parameters_dir / "shared.tf"
    assert shared_tf.exists()


def test_locals_tf_exists(api_common_parameters_dir):
    """Test that locals.tf exists."""
    locals_tf = api_common_parameters_dir / "locals.tf"
    assert locals_tf.exists()


def test_ssm_tf_exists(api_common_parameters_dir):
    """Test that ssm.tf exists."""
    ssm_tf = api_common_parameters_dir / "ssm.tf"
    assert ssm_tf.exists()


def test_outputs_tf_exists(api_common_parameters_dir):
    """Test that outputs.tf exists."""
    outputs_tf = api_common_parameters_dir / "outputs.tf"
    assert outputs_tf.exists()


def test_backend_uses_s3(api_common_parameters_dir):
    """Test that backend uses S3."""
    backend_tf = api_common_parameters_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'backend "s3"' in content


def test_backend_state_key_is_correct(api_common_parameters_dir):
    """Test that backend state key follows naming convention."""
    backend_tf = api_common_parameters_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'key          = "api/common/parameters/terraform.tfstate"' in content


def test_common_module_is_referenced(api_common_parameters_dir):
    """Test that common module is referenced."""
    shared_tf = api_common_parameters_dir / "shared.tf"
    content = shared_tf.read_text()
    assert 'module "common"' in content


def test_locals_uses_common_aws_region(api_common_parameters_dir):
    """Test that locals uses aws_region from common module."""
    locals_tf = api_common_parameters_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "module.common.aws_region" in content
