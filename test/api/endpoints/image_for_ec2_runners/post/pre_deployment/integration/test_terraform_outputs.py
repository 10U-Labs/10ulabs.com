class TestRequiredTerraformOutputs:
    def test_terraform_init_succeeds(self, terraform_initialized):
        assert terraform_initialized

    def test_ec2_runner_ami_purpose_value_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("ec2_runner_ami_purpose_value") != ""
        assert has_output

    def test_ec2_runner_ami_stable_tag_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("ec2_runner_ami_stable_tag") != ""
        assert has_output

    def test_runner_security_group_id_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("runner_security_group_id") != ""
        assert has_output

    def test_ssm_parameter_name_for_latest_ami_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("ssm_parameter_name_for_latest_ami") != ""
        assert has_output

    def test_vpc_public_subnet_ids_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("vpc_public_subnet_ids") != ""
        assert has_output

    def test_ec2_instance_types_exists(self, terraform_outputs):
        has_output = terraform_outputs.get("ec2_instance_types") != ""
        assert has_output


class TestTerraformOutputFormats:
    def test_security_group_id_format(self, security_group_id):
        is_valid_format = security_group_id.startswith("sg-")
        assert is_valid_format

    def test_subnet_ids_not_empty(self, subnet_ids):
        has_subnets = len(subnet_ids) > 0
        assert has_subnets

    def test_subnet_ids_format(self, subnet_ids):
        all_valid = all(s.startswith("subnet-") for s in subnet_ids)
        assert all_valid

    def test_instance_types_not_empty(self, instance_types):
        has_types = len(instance_types) > 0
        assert has_types
