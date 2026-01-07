"""Unit tests for test_fixtures.terraform_tests module."""
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from test_fixtures.terraform_tests import (
    get_api_common_routing_outputs,
    create_remote_state_contract_tests,
    create_naming_conventions_tests,
    create_remote_state_config_tests,
)


class TestGetApiCommonRoutingOutputs:
    """Tests for get_api_common_routing_outputs function."""

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
    def test_returns_set(self):
        """Test that function returns a set."""
        result = get_api_common_routing_outputs()
        assert isinstance(result, set)

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data='output "foo" {\n  value = "bar"\n}\n'))
    def test_extracts_single_output(self):
        """Test that function extracts a single output name."""
        result = get_api_common_routing_outputs()
        assert "foo" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_multiple_outputs(self):
        """Test that function extracts multiple output names."""
        result = get_api_common_routing_outputs()
        assert len(result) == 2

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_first_output_from_multiple(self):
        """Test that function extracts first output from multiple."""
        result = get_api_common_routing_outputs()
        assert "api_gateway_id" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_second_output_from_multiple(self):
        """Test that function extracts second output from multiple."""
        result = get_api_common_routing_outputs()
        assert "lambda_arn" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
    def test_returns_empty_set_for_no_outputs(self):
        """Test that function returns empty set when no outputs defined."""
        result = get_api_common_routing_outputs()
        assert result == set()

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data='# output "commented" {\n}\n'))
    def test_extracts_commented_output(self):
        """Test that function extracts output even in comments (regex limitation)."""
        # Note: The regex doesn't filter comments, this tests actual behavior
        result = get_api_common_routing_outputs()
        assert "commented" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "snake_case_name" {\n  value = "test"\n}\n'
    ))
    def test_extracts_snake_case_output_names(self):
        """Test that function extracts snake_case output names."""
        result = get_api_common_routing_outputs()
        assert "snake_case_name" in result


class TestCreateRemoteStateContractTests:
    """Tests for create_remote_state_contract_tests factory function."""

    def test_returns_class(self, tmp_path):
        """Test that factory returns a class."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert isinstance(result, type)

    def test_returned_class_name(self, tmp_path):
        """Test that returned class has expected name."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert result.__name__ == "TestRemoteStateContract"

    def test_class_has_lambda_file_exists_method(self, tmp_path):
        """Test that returned class has test_lambda_file_exists method."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_lambda_file_exists")

    def test_class_has_api_remote_state_references_method(self, tmp_path):
        """Test that returned class has test_all_api_remote_state_references_exist_in_backend_outputs method."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_all_api_remote_state_references_exist_in_backend_outputs")

    def test_custom_lambda_file_name(self, tmp_path):
        """Test that factory accepts custom lambda file name."""
        custom_file = tmp_path / "custom_lambda.tf"
        custom_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", lambda_file="custom_lambda.tf"
        )
        assert result is not None

    def test_adds_dynamic_test_for_required_output(self, tmp_path):
        """Test that factory adds dynamic test method for required output."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["api_gateway_id"]
        )
        assert hasattr(result, "test_api_gateway_id_output_exists_in_backend")

    def test_adds_multiple_dynamic_tests_for_required_outputs(self, tmp_path):
        """Test that factory adds multiple dynamic test methods."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
        )
        assert hasattr(result, "test_output_one_output_exists_in_backend")

    def test_adds_second_dynamic_test_for_required_outputs(self, tmp_path):
        """Test that factory adds second dynamic test method."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
        )
        assert hasattr(result, "test_output_two_output_exists_in_backend")

    def test_lambda_file_exists_test_passes_when_file_exists(self, tmp_path):
        """Test that test_lambda_file_exists passes when file exists."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("# Lambda configuration")
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_lambda_file_exists() is None

    def test_lambda_file_exists_test_fails_when_file_missing(self, tmp_path):
        """Test that test_lambda_file_exists fails when file missing."""
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_lambda_file_exists()

    @patch('test_fixtures.terraform_tests.get_api_common_routing_outputs')
    def test_remote_state_references_test_passes_when_all_exist(self, mock_outputs, tmp_path):
        """Test that remote state references test passes when all outputs exist."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('data.terraform_remote_state.api.outputs.api_gateway_id')
        mock_outputs.return_value = {"api_gateway_id"}
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_all_api_remote_state_references_exist_in_backend_outputs() is None

    @patch('test_fixtures.terraform_tests.get_api_common_routing_outputs')
    def test_remote_state_references_test_fails_when_missing(self, mock_outputs, tmp_path):
        """Test that remote state references test fails when output missing."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('data.terraform_remote_state.api.outputs.missing_output')
        mock_outputs.return_value = {"other_output"}
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_all_api_remote_state_references_exist_in_backend_outputs()

    @patch('test_fixtures.terraform_tests.get_api_common_routing_outputs')
    def test_required_output_test_passes_when_exists(self, mock_outputs, tmp_path):
        """Test that required output test passes when output exists."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        mock_outputs.return_value = {"required_output"}
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["required_output"]
        )
        instance = TestClass()
        assert instance.test_required_output_output_exists_in_backend() is None

    @patch('test_fixtures.terraform_tests.get_api_common_routing_outputs')
    def test_required_output_test_fails_when_missing(self, mock_outputs, tmp_path):
        """Test that required output test fails when output missing."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        mock_outputs.return_value = {"other_output"}
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["required_output"]
        )
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_required_output_output_exists_in_backend()


class TestCreateNamingConventionsTests:
    """Tests for create_naming_conventions_tests factory function."""

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_returns_tuple(self, mock_lambda, mock_iam, tmp_path):
        """Test that factory returns a tuple."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        result = create_naming_conventions_tests(tmp_path)
        assert isinstance(result, tuple)

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_returns_tuple_of_length_two(self, mock_lambda, mock_iam, tmp_path):
        """Test that factory returns tuple of length 2."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        result = create_naming_conventions_tests(tmp_path)
        assert len(result) == 2

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_first_element_is_class(self, mock_lambda, mock_iam, tmp_path):
        """Test that first element of tuple is a class."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        assert isinstance(iam_class, type)

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_second_element_is_class(self, mock_lambda, mock_iam, tmp_path):
        """Test that second element of tuple is a class."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        assert isinstance(lambda_class, type)

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_class_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM class has expected name."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        assert iam_class.__name__ == "TestIAMRoleNamingConventions"

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_class_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda class has expected name."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        assert lambda_class.__name__ == "TestLambdaFunctionNamingConventions"

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_class_has_pascalcase_test(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM class has test_iam_role_name_is_pascalcase method."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        assert hasattr(iam_class, "test_iam_role_name_is_pascalcase")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_class_has_no_dashes_test(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM class has test_no_iam_role_names_contain_dashes method."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        assert hasattr(iam_class, "test_no_iam_role_names_contain_dashes")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_class_has_pascalcase_test(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda class has test_lambda_function_name_is_pascalcase method."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        assert hasattr(lambda_class, "test_lambda_function_name_is_pascalcase")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_class_has_no_dashes_test(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda class has test_no_lambda_function_names_contain_dashes method."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        assert hasattr(lambda_class, "test_no_lambda_function_names_contain_dashes")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_uses_custom_iam_file(self, mock_lambda, mock_iam, tmp_path):
        """Test that factory uses custom IAM file path."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        create_naming_conventions_tests(tmp_path, iam_file="custom_iam.tf")
        assert mock_iam.call_args[0][0] == tmp_path / "custom_iam.tf"

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_uses_custom_lambda_file(self, mock_lambda, mock_iam, tmp_path):
        """Test that factory uses custom Lambda file path."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        create_naming_conventions_tests(tmp_path, lambda_file="custom_lambda.tf")
        assert mock_lambda.call_args[0][0] == tmp_path / "custom_lambda.tf"

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_passes_use_handler_names_flag(self, mock_lambda, mock_iam, tmp_path):
        """Test that factory passes use_handler_names flag."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        create_naming_conventions_tests(tmp_path, use_handler_names=True)
        assert mock_lambda.call_args[1]["use_handler_names"] is True

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_no_dashes_test_passes_with_valid_names(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM no dashes test passes with valid names."""
        mock_iam.return_value = [("role1", "ValidRoleName"), ("role2", "AnotherValidName")]
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        instance = iam_class()
        assert instance.test_no_iam_role_names_contain_dashes() is None

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_no_dashes_test_fails_with_dashes(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM no dashes test fails with dashed names."""
        mock_iam.return_value = [("role1", "Invalid-Role-Name")]
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        instance = iam_class()
        with pytest.raises(AssertionError):
            instance.test_no_iam_role_names_contain_dashes()

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_no_dashes_test_passes_with_valid_names(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda no dashes test passes with valid names."""
        mock_iam.return_value = []
        mock_lambda.return_value = [("func1", "ValidFuncName"), ("func2", "AnotherValidName")]
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        instance = lambda_class()
        assert instance.test_no_lambda_function_names_contain_dashes() is None

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_no_dashes_test_fails_with_dashes(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda no dashes test fails with dashed names."""
        mock_iam.return_value = []
        mock_lambda.return_value = [("func1", "Invalid-Func-Name")]
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        instance = lambda_class()
        with pytest.raises(AssertionError):
            instance.test_no_lambda_function_names_contain_dashes()


class TestCreateRemoteStateConfigTests:
    """Tests for create_remote_state_config_tests factory function."""

    def test_returns_class(self, tmp_path):
        """Test that factory returns a class."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert isinstance(result, type)

    def test_returned_class_name(self, tmp_path):
        """Test that returned class has expected name."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert result.__name__ == "TestRemoteStateConfig"

    def test_class_has_data_tf_exists_method(self, tmp_path):
        """Test that returned class has test_data_tf_exists method."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_data_tf_exists")

    def test_class_has_no_hardcoded_bucket_method(self, tmp_path):
        """Test that returned class has test_no_hardcoded_bucket_name method."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_no_hardcoded_bucket_name")

    def test_class_has_no_hardcoded_region_method(self, tmp_path):
        """Test that returned class has test_no_hardcoded_region method."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_no_hardcoded_region")

    def test_class_has_correct_state_key_method(self, tmp_path):
        """Test that returned class has test_uses_correct_state_key_pattern method."""
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_uses_correct_state_key_pattern")

    def test_data_tf_exists_test_passes_when_file_exists(self, tmp_path):
        """Test that test_data_tf_exists passes when file exists."""
        data_file = tmp_path / "data.tf"
        data_file.write_text("# Data configuration")
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_data_tf_exists() is None

    def test_data_tf_exists_test_fails_when_file_missing(self, tmp_path):
        """Test that test_data_tf_exists fails when file missing."""
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_data_tf_exists()

    def test_no_hardcoded_bucket_passes_with_dynamic_bucket(self, tmp_path):
        """Test that no hardcoded bucket test passes with dynamic bucket."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = module.common.name_for_terraform_state_bucket')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_no_hardcoded_bucket_name() is None

    def test_no_hardcoded_bucket_fails_with_terraform_state_pattern(self, tmp_path):
        """Test that no hardcoded bucket test fails with hardcoded terraform-state bucket."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "mycompany-terraform-state"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_bucket_fails_with_tenulabs_pattern(self, tmp_path):
        """Test that no hardcoded bucket test fails with tenulabs- bucket pattern."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "tenulabs-something"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_bucket_fails_with_10ulabs_pattern(self, tmp_path):
        """Test that no hardcoded bucket test fails with 10ulabs- bucket pattern."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "10ulabs-something"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_region_passes_with_local_region(self, tmp_path):
        """Test that no hardcoded region test passes with local.aws_region."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = local.aws_region')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_no_hardcoded_region() is None

    def test_no_hardcoded_region_fails_with_hardcoded_region(self, tmp_path):
        """Test that no hardcoded region test fails with hardcoded region."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = "us-east-1"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_region()

    def test_no_hardcoded_region_fails_with_eu_region(self, tmp_path):
        """Test that no hardcoded region test fails with EU hardcoded region."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = "eu-west-2"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_region()

    def test_state_key_passes_without_remote_state(self, tmp_path):
        """Test that state key test passes when no terraform_remote_state present."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('# No remote state config')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_uses_correct_state_key_pattern() is None

    def test_state_key_passes_with_correct_api_key(self, tmp_path):
        """Test that state key test passes with correct api state key."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('''
terraform_remote_state "api" {
  key = "api/terraform.tfstate"
}
''')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_uses_correct_state_key_pattern() is None

    def test_state_key_fails_with_wrong_api_key(self, tmp_path):
        """Test that state key test fails with wrong api state key path."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('''
terraform_remote_state "api" {
  key = "api_common_routing/terraform.tfstate"
}
''')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_uses_correct_state_key_pattern()

    def test_state_key_fails_when_api_key_missing_but_api_remote_state_present(self, tmp_path):
        """Test that state key test fails when api remote state has no correct key."""
        data_file = tmp_path / "data.tf"
        data_file.write_text('''
terraform_remote_state "api" {
  key = "wrong/terraform.tfstate"
}
''')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_uses_correct_state_key_pattern()


class TestCreateRemoteStateContractTestsIntegration:
    """Integration tests for create_remote_state_contract_tests with file operations."""

    def test_extracts_remote_state_references_from_lambda_file(self, tmp_path):
        """Test that references are extracted from lambda file content."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = "MyFunc"
  environment {
    variables = {
      API_URL = data.terraform_remote_state.api.outputs.api_endpoint
      API_ID  = data.terraform_remote_state.api.outputs.api_gateway_id
    }
  }
}
''')
        with patch('test_fixtures.terraform_tests.get_api_common_routing_outputs') as mock_outputs:
            mock_outputs.return_value = {"api_endpoint", "api_gateway_id"}
            TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
            instance = TestClass()
            assert instance.test_all_api_remote_state_references_exist_in_backend_outputs() is None

    def test_fails_when_referenced_output_missing_from_backend(self, tmp_path):
        """Test that test fails when referenced output doesn't exist in backend."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
API_URL = data.terraform_remote_state.api.outputs.nonexistent_output
''')
        with patch('test_fixtures.terraform_tests.get_api_common_routing_outputs') as mock_outputs:
            mock_outputs.return_value = {"other_output"}
            TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
            instance = TestClass()
            with pytest.raises(AssertionError):
                instance.test_all_api_remote_state_references_exist_in_backend_outputs()


class TestCreateNamingConventionsTestsParameterization:
    """Tests for parametrized test methods in create_naming_conventions_tests."""

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_parametrize_uses_none_marker_when_no_roles(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM test uses NONE marker when no roles found."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        # The parametrize decorator should have [("NONE", "NONE")] as default
        test_method = getattr(iam_class, "test_iam_role_name_is_pascalcase")
        # Check that the method has pytest.mark.parametrize
        assert hasattr(test_method, "pytestmark")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_parametrize_uses_none_marker_when_no_functions(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda test uses NONE marker when no functions found."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        test_method = getattr(lambda_class, "test_lambda_function_name_is_pascalcase")
        assert hasattr(test_method, "pytestmark")


class TestDynamicTestMethodDocstrings:
    """Tests for dynamically generated test method docstrings."""

    def test_required_output_test_has_docstring(self, tmp_path):
        """Test that dynamically created required output test has docstring."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["my_output"]
        )
        test_method = getattr(TestClass, "test_my_output_output_exists_in_backend")
        assert test_method.__doc__ is not None

    def test_required_output_test_docstring_mentions_output_name(self, tmp_path):
        """Test that required output test docstring mentions output name."""
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["my_output"]
        )
        test_method = getattr(TestClass, "test_my_output_output_exists_in_backend")
        assert "my_output" in test_method.__doc__


class TestNamingConventionsNoneCase:
    """Tests for naming conventions NONE case handling."""

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_pascalcase_fails_with_none_marker(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM pascalcase test fails with NONE marker."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        instance = iam_class()
        with pytest.raises(pytest.fail.Exception, match="No IAM roles found"):
            instance.test_iam_role_name_is_pascalcase("NONE", "NONE")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_pascalcase_fails_with_none_marker(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda pascalcase test fails with NONE marker."""
        mock_iam.return_value = []
        mock_lambda.return_value = []
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        instance = lambda_class()
        with pytest.raises(pytest.fail.Exception, match="No Lambda functions found"):
            instance.test_lambda_function_name_is_pascalcase("NONE", "NONE")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_pascalcase_passes_with_valid_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM pascalcase test passes with valid PascalCase name."""
        mock_iam.return_value = [("test_role", "ValidRoleName")]
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        instance = iam_class()
        assert instance.test_iam_role_name_is_pascalcase("test_role", "ValidRoleName") is None

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_iam_pascalcase_fails_with_invalid_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that IAM pascalcase test fails with invalid dashed name."""
        mock_iam.return_value = [("test_role", "Invalid-Role-Name")]
        mock_lambda.return_value = []
        iam_class, _ = create_naming_conventions_tests(tmp_path)
        instance = iam_class()
        with pytest.raises(AssertionError, match="Invalid-Role-Name"):
            instance.test_iam_role_name_is_pascalcase("test_role", "Invalid-Role-Name")

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_pascalcase_passes_with_valid_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda pascalcase test passes with valid PascalCase name."""
        mock_iam.return_value = []
        mock_lambda.return_value = [("test_func", "ValidFunctionName")]
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        instance = lambda_class()
        assert instance.test_lambda_function_name_is_pascalcase("test_func", "ValidFunctionName") is None

    @patch('test_fixtures.terraform_tests.extract_iam_role_names')
    @patch('test_fixtures.terraform_tests.extract_lambda_function_names')
    def test_lambda_pascalcase_fails_with_invalid_name(self, mock_lambda, mock_iam, tmp_path):
        """Test that Lambda pascalcase test fails with invalid dashed name."""
        mock_iam.return_value = []
        mock_lambda.return_value = [("test_func", "Invalid-Function-Name")]
        _, lambda_class = create_naming_conventions_tests(tmp_path)
        instance = lambda_class()
        with pytest.raises(AssertionError, match="Invalid-Function-Name"):
            instance.test_lambda_function_name_is_pascalcase("test_func", "Invalid-Function-Name")
