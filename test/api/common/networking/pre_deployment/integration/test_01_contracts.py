"""Pre-deployment Layer 1 contract tests for api/common/networking.

Contract tests verify that local files that must work together are compatible.
These tests catch mismatches between files before deployment - no AWS calls.

Layer 1: Contracts - Local files are compatible
"""
from repo_utils import REPO_ROOT


API_COMMON_NETWORKING_DIR = REPO_ROOT / "src" / "api" / "common" / "networking"
LIB_TERRAFORM_COMMON_DIR = REPO_ROOT / "lib" / "terraform" / "common"


class TestOutputsReferencesExist:
    """Verify outputs.tf references exist in source files."""

    def test_vpc_resource_exists_for_vpc_id_output(self):
        """Verify aws_vpc.main exists for vpc_id output."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert 'resource "aws_vpc" "main"' in vpc_tf.read_text()

    def test_outputs_references_vpc_main_id(self):
        """Verify vpc_id output references aws_vpc.main.id."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        assert "aws_vpc.main.id" in outputs_tf.read_text()

    def test_subnet_resource_exists_for_public_subnets_output(self):
        """Verify aws_subnet.public exists for public_subnets_ids output."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert 'resource "aws_subnet" "public"' in vpc_tf.read_text()

    def test_outputs_references_subnet_public(self):
        """Verify public_subnets_ids output references aws_subnet.public."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        assert "aws_subnet.public" in outputs_tf.read_text()

    def test_security_group_resource_exists_for_sg_output(self):
        """Verify aws_security_group.runner exists for security group output."""
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"
        assert 'resource "aws_security_group" "runner"' in sg_tf.read_text()

    def test_outputs_references_security_group_runner_id(self):
        """Verify security_group_id_for_runners references aws_security_group.runner.id."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        assert "aws_security_group.runner.id" in outputs_tf.read_text()


class TestLocalsVpcContract:
    """Verify locals.tf defines values used by vpc.tf."""

    def test_locals_defines_vpc_cidr(self):
        """Verify locals.tf defines vpc_cidr."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "vpc_cidr" in locals_tf.read_text()

    def test_vpc_uses_local_vpc_cidr(self):
        """Verify vpc.tf uses local.vpc_cidr."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert "local.vpc_cidr" in vpc_tf.read_text()

    def test_locals_defines_vpc_name(self):
        """Verify locals.tf defines vpc_name."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "vpc_name" in locals_tf.read_text()

    def test_vpc_uses_local_vpc_name(self):
        """Verify vpc.tf uses local.vpc_name."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert "local.vpc_name" in vpc_tf.read_text()

    def test_locals_defines_vpc_azs(self):
        """Verify locals.tf defines vpc_azs."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "vpc_azs" in locals_tf.read_text()

    def test_vpc_uses_local_vpc_azs(self):
        """Verify vpc.tf uses local.vpc_azs."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert "local.vpc_azs" in vpc_tf.read_text()


class TestLocalsSecurityGroupContract:
    """Verify locals.tf and security_groups.tf are compatible."""

    def test_locals_defines_common_tags(self):
        """Verify locals.tf defines common_tags."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "common_tags" in locals_tf.read_text()

    def test_security_group_uses_local_common_tags(self):
        """Verify security_groups.tf uses local.common_tags."""
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"
        assert "local.common_tags" in sg_tf.read_text()

    def test_vpc_resource_exists_for_security_group(self):
        """Verify aws_vpc.main exists for security group vpc_id reference."""
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"
        assert 'resource "aws_vpc" "main"' in vpc_tf.read_text()

    def test_security_group_references_vpc_main_id(self):
        """Verify security_groups.tf references aws_vpc.main.id."""
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"
        assert "aws_vpc.main.id" in sg_tf.read_text()


class TestSharedModuleContract:
    """Verify shared.tf and lib/terraform/common are compatible."""

    def test_shared_module_source_exists(self):
        """Verify the common module directory exists."""
        assert LIB_TERRAFORM_COMMON_DIR.exists()

    def test_shared_module_has_locals_tf(self):
        """Verify lib/terraform/common has locals.tf."""
        locals_tf = LIB_TERRAFORM_COMMON_DIR / "locals.tf"
        assert locals_tf.exists()

    def test_shared_module_has_outputs_tf(self):
        """Verify lib/terraform/common has outputs.tf."""
        outputs_tf = LIB_TERRAFORM_COMMON_DIR / "outputs.tf"
        assert outputs_tf.exists()

    def test_shared_module_exports_aws_region(self):
        """Verify lib/terraform/common exports aws_region."""
        outputs_tf = LIB_TERRAFORM_COMMON_DIR / "outputs.tf"
        assert 'output "aws_region"' in outputs_tf.read_text()

    def test_shared_module_exports_resource_prefix(self):
        """Verify lib/terraform/common exports resource_prefix."""
        outputs_tf = LIB_TERRAFORM_COMMON_DIR / "outputs.tf"
        assert 'output "resource_prefix"' in outputs_tf.read_text()

    def test_locals_uses_shared_module_aws_region(self):
        """Verify locals.tf uses module.common.aws_region."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "module.common.aws_region" in locals_tf.read_text()

    def test_locals_uses_shared_module_resource_prefix(self):
        """Verify locals.tf uses module.common.resource_prefix."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "module.common.resource_prefix" in locals_tf.read_text()


class TestBackendContract:
    """Verify backend.tf configuration is consistent."""

    def test_backend_state_key_matches_module_path(self):
        """Verify backend state key matches the module's path in repo."""
        backend_tf = API_COMMON_NETWORKING_DIR / "backend.tf"
        assert "api/common/networking/terraform.tfstate" in backend_tf.read_text()

    def test_backend_region_is_us_east_2(self):
        """Verify backend region is us-east-2."""
        backend_tf = API_COMMON_NETWORKING_DIR / "backend.tf"
        assert 'region       = "us-east-2"' in backend_tf.read_text()

    def test_shared_module_aws_region_is_us_east_2(self):
        """Verify shared module aws_region is us-east-2."""
        common_locals = LIB_TERRAFORM_COMMON_DIR / "locals.tf"
        assert '"us-east-2"' in common_locals.read_text()


class TestProviderContract:
    """Verify providers.tf is consistent with locals.tf."""

    def test_locals_defines_aws_region(self):
        """Verify locals.tf defines aws_region."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        assert "aws_region" in locals_tf.read_text()

    def test_provider_uses_local_aws_region(self):
        """Verify AWS provider uses local.aws_region."""
        providers_tf = API_COMMON_NETWORKING_DIR / "providers.tf"
        assert "local.aws_region" in providers_tf.read_text()
