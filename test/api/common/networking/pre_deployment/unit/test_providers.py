"""Pre-deployment unit tests for api/common/networking providers.tf."""


def test_providers_file_exists(api_common_networking_dir):
    """Test that providers.tf file exists."""
    providers_tf = api_common_networking_dir / "providers.tf"
    assert providers_tf.exists()


def test_providers_defines_terraform_block(api_common_networking_dir):
    """Test that providers.tf defines terraform block."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "terraform {" in content


def test_providers_specifies_required_version(api_common_networking_dir):
    """Test that providers.tf specifies required_version."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "required_version" in content


def test_providers_defines_aws_provider(api_common_networking_dir):
    """Test that providers.tf defines AWS provider."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert 'provider "aws"' in content


def test_providers_aws_has_region(api_common_networking_dir):
    """Test that AWS provider has region configured."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "region" in content


def test_providers_aws_uses_local_region(api_common_networking_dir):
    """Test that AWS provider uses local.aws_region."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "local.aws_region" in content




def test_providers_defines_required_providers(api_common_networking_dir):
    """Test that providers.tf defines required_providers block."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "required_providers" in content


def test_providers_requires_aws_provider(api_common_networking_dir):
    """Test that required_providers includes aws."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "aws = {" in content


def test_providers_aws_source_is_hashicorp(api_common_networking_dir):
    """Test that AWS provider source is hashicorp/aws."""
    providers_tf = api_common_networking_dir / "providers.tf"
    content = providers_tf.read_text()
    assert "hashicorp/aws" in content
