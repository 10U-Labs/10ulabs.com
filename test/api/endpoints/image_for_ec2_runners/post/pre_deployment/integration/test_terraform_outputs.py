"""Integration tests for Terraform outputs."""


class TestRequiredTerraformOutputs:
    """Tests for required terraform outputs."""

    def test_terraform_init_succeeds(self, terraform_initialized):
        """Terraform init succeeds."""

        assert terraform_initialized

    def test_ec2_runner_ami_purpose_value_exists(self, terraform_outputs):
        """Ec2 runner ami purpose value exists."""

        has_output = terraform_outputs.get("ec2_runner_ami_purpose_value") != ""
        assert has_output

    def test_ec2_runner_ami_stable_tag_exists(self, terraform_outputs):
        """Ec2 runner ami stable tag exists."""

        has_output = terraform_outputs.get("ec2_runner_ami_stable_tag") != ""
        assert has_output

    def test_runner_security_group_id_exists(self, terraform_outputs):
        """Runner security group id exists."""

        has_output = terraform_outputs.get("runner_security_group_id") != ""
        assert has_output

    def test_ssm_parameter_name_for_latest_ami_exists(self, terraform_outputs):
        """Ssm parameter name for latest ami exists."""

        has_output = terraform_outputs.get("ssm_parameter_name_for_latest_ami") != ""
        assert has_output

    def test_vpc_public_subnet_ids_exists(self, terraform_outputs):
        """Vpc public subnet ids exists."""

        has_output = terraform_outputs.get("vpc_public_subnet_ids") != ""
        assert has_output

    def test_ec2_instance_types_exists(self, terraform_outputs):
        """Ec2 instance types exists."""

        has_output = terraform_outputs.get("ec2_instance_types") != ""
        assert has_output


class TestTerraformOutputFormats:
    """Tests for terraform output formats."""

    def test_security_group_id_format(self, security_group_id):
        """Security group id format."""

        is_valid_format = security_group_id.startswith("sg-")
        assert is_valid_format

    def test_subnet_ids_not_empty(self, subnet_ids):
        """Subnet ids not empty."""

        has_subnets = len(subnet_ids) > 0
        assert has_subnets

    def test_subnet_ids_format(self, subnet_ids):
        """Subnet ids format."""

        all_valid = all(s.startswith("subnet-") for s in subnet_ids)
        assert all_valid

    def test_instance_types_not_empty(self, instance_types):
        """Instance types not empty."""

        has_types = len(instance_types) > 0
        assert has_types
