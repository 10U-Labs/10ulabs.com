"""Pre-deployment Layer 1 contract tests for api/common/networking.

Contract tests verify that local files that must work together are compatible.
These tests catch mismatches between files before deployment - no AWS calls.

Layer 1: Contracts - Local files are compatible
"""
from pathlib import Path

from repo_utils import REPO_ROOT


API_COMMON_NETWORKING_DIR = REPO_ROOT / "src" / "api" / "common" / "networking"
LIB_TERRAFORM_COMMON_DIR = REPO_ROOT / "lib" / "terraform" / "common"


class TestLocalsOutputsContract:
    """Verify locals.tf and outputs.tf are compatible."""

    def test_vpc_id_output_references_existing_vpc_resource(self):
        """Verify vpc_id output references aws_vpc.main which is defined in vpc.tf."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        outputs_content = outputs_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # Output references aws_vpc.main.id
        assert "aws_vpc.main.id" in outputs_content

        # vpc.tf must define aws_vpc.main
        assert 'resource "aws_vpc" "main"' in vpc_content

    def test_public_subnets_output_references_existing_subnet_resource(self):
        """Verify public_subnets_ids output references aws_subnet.public."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        outputs_content = outputs_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # Output references aws_subnet.public
        assert "aws_subnet.public" in outputs_content

        # vpc.tf must define aws_subnet.public
        assert 'resource "aws_subnet" "public"' in vpc_content

    def test_security_group_output_references_existing_sg_resource(self):
        """Verify security_group_id_for_runners references aws_security_group.runner."""
        outputs_tf = API_COMMON_NETWORKING_DIR / "outputs.tf"
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"

        outputs_content = outputs_tf.read_text()
        sg_content = sg_tf.read_text()

        # Output references aws_security_group.runner.id
        assert "aws_security_group.runner.id" in outputs_content

        # security_groups.tf must define aws_security_group.runner
        assert 'resource "aws_security_group" "runner"' in sg_content


class TestLocalsVpcContract:
    """Verify locals.tf and vpc.tf are compatible."""

    def test_vpc_uses_local_vpc_cidr(self):
        """Verify vpc.tf uses local.vpc_cidr defined in locals.tf."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        locals_content = locals_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # locals.tf defines vpc_cidr
        assert "vpc_cidr" in locals_content

        # vpc.tf uses local.vpc_cidr
        assert "local.vpc_cidr" in vpc_content

    def test_vpc_uses_local_vpc_name(self):
        """Verify vpc.tf uses local.vpc_name defined in locals.tf."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        locals_content = locals_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # locals.tf defines vpc_name
        assert "vpc_name" in locals_content

        # vpc.tf uses local.vpc_name
        assert "local.vpc_name" in vpc_content

    def test_vpc_uses_local_vpc_azs(self):
        """Verify vpc.tf uses local.vpc_azs defined in locals.tf."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        locals_content = locals_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # locals.tf defines vpc_azs
        assert "vpc_azs" in locals_content

        # vpc.tf uses local.vpc_azs
        assert "local.vpc_azs" in vpc_content


class TestLocalsSecurityGroupContract:
    """Verify locals.tf and security_groups.tf are compatible."""

    def test_security_group_uses_local_common_tags(self):
        """Verify security_groups.tf uses local.common_tags."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"

        locals_content = locals_tf.read_text()
        sg_content = sg_tf.read_text()

        # locals.tf defines common_tags
        assert "common_tags" in locals_content

        # security_groups.tf uses local.common_tags
        assert "local.common_tags" in sg_content

    def test_security_group_references_vpc_resource(self):
        """Verify security_groups.tf references aws_vpc.main from vpc.tf."""
        sg_tf = API_COMMON_NETWORKING_DIR / "security_groups.tf"
        vpc_tf = API_COMMON_NETWORKING_DIR / "vpc.tf"

        sg_content = sg_tf.read_text()
        vpc_content = vpc_tf.read_text()

        # security_groups.tf references aws_vpc.main.id
        assert "aws_vpc.main.id" in sg_content

        # vpc.tf must define aws_vpc.main
        assert 'resource "aws_vpc" "main"' in vpc_content


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
        content = outputs_tf.read_text()
        assert 'output "aws_region"' in content

    def test_shared_module_exports_resource_prefix(self):
        """Verify lib/terraform/common exports resource_prefix."""
        outputs_tf = LIB_TERRAFORM_COMMON_DIR / "outputs.tf"
        content = outputs_tf.read_text()
        assert 'output "resource_prefix"' in content

    def test_locals_uses_shared_module_aws_region(self):
        """Verify locals.tf uses module.common.aws_region."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        content = locals_tf.read_text()
        assert "module.common.aws_region" in content

    def test_locals_uses_shared_module_resource_prefix(self):
        """Verify locals.tf uses module.common.resource_prefix."""
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"
        content = locals_tf.read_text()
        assert "module.common.resource_prefix" in content


class TestBackendContract:
    """Verify backend.tf configuration is consistent."""

    def test_backend_state_key_matches_module_path(self):
        """Verify backend state key matches the module's path in repo."""
        backend_tf = API_COMMON_NETWORKING_DIR / "backend.tf"
        content = backend_tf.read_text()

        # The state key should reflect the module's location
        assert "api/common/networking/terraform.tfstate" in content

    def test_backend_region_matches_shared_module_region(self):
        """Verify backend region matches the shared module's aws_region."""
        backend_tf = API_COMMON_NETWORKING_DIR / "backend.tf"
        common_locals = LIB_TERRAFORM_COMMON_DIR / "locals.tf"

        backend_content = backend_tf.read_text()
        common_content = common_locals.read_text()

        # Both should use us-east-2
        assert 'region       = "us-east-2"' in backend_content
        assert 'aws_region' in common_content
        assert '"us-east-2"' in common_content


class TestProviderContract:
    """Verify providers.tf is consistent with locals.tf."""

    def test_provider_uses_local_aws_region(self):
        """Verify AWS provider uses local.aws_region."""
        providers_tf = API_COMMON_NETWORKING_DIR / "providers.tf"
        locals_tf = API_COMMON_NETWORKING_DIR / "locals.tf"

        providers_content = providers_tf.read_text()
        locals_content = locals_tf.read_text()

        # locals.tf defines aws_region
        assert "aws_region" in locals_content

        # providers.tf uses local.aws_region
        assert "local.aws_region" in providers_content
