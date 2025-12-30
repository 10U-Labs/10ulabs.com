"""Pre-deployment unit tests for api/shared/parameters Terraform structure."""


def test_backend_tf_exists(api_shared_parameters_dir):
    """Test that backend.tf exists."""
    backend_tf = api_shared_parameters_dir / "backend.tf"
    assert backend_tf.exists()


def test_providers_tf_exists(api_shared_parameters_dir):
    """Test that providers.tf exists."""
    providers_tf = api_shared_parameters_dir / "providers.tf"
    assert providers_tf.exists()


def test_shared_tf_exists(api_shared_parameters_dir):
    """Test that shared.tf exists."""
    shared_tf = api_shared_parameters_dir / "shared.tf"
    assert shared_tf.exists()


def test_locals_tf_exists(api_shared_parameters_dir):
    """Test that locals.tf exists."""
    locals_tf = api_shared_parameters_dir / "locals.tf"
    assert locals_tf.exists()


def test_ssm_tf_exists(api_shared_parameters_dir):
    """Test that ssm.tf exists."""
    ssm_tf = api_shared_parameters_dir / "ssm.tf"
    assert ssm_tf.exists()


def test_outputs_tf_exists(api_shared_parameters_dir):
    """Test that outputs.tf exists."""
    outputs_tf = api_shared_parameters_dir / "outputs.tf"
    assert outputs_tf.exists()


def test_backend_uses_s3(api_shared_parameters_dir):
    """Test that backend uses S3."""
    backend_tf = api_shared_parameters_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'backend "s3"' in content


def test_backend_state_key_is_correct(api_shared_parameters_dir):
    """Test that backend state key follows naming convention."""
    backend_tf = api_shared_parameters_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'key          = "api/shared/parameters/terraform.tfstate"' in content


def test_shared_module_is_referenced(api_shared_parameters_dir):
    """Test that shared module is referenced."""
    shared_tf = api_shared_parameters_dir / "shared.tf"
    content = shared_tf.read_text()
    assert 'module "shared"' in content


def test_locals_uses_shared_aws_region(api_shared_parameters_dir):
    """Test that locals uses aws_region from shared module."""
    locals_tf = api_shared_parameters_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "module.shared.aws_region" in content


def test_locals_uses_shared_resource_prefix(api_shared_parameters_dir):
    """Test that locals uses resource_prefix from shared module."""
    locals_tf = api_shared_parameters_dir / "locals.tf"
    content = locals_tf.read_text()
    assert "module.shared.resource_prefix" in content
