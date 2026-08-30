import re
from unittest.mock import patch, mock_open

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import (
    API_COMMON_ROUTING_OUTPUTS_FILE,
    _get_api_common_routing_outputs,
    create_remote_state_contract_tests,
    create_remote_state_config_tests,
)


class TestGetApiCommonRoutingOutputs:
    @patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
    def test_returns_set(self):
        result = _get_api_common_routing_outputs()
        assert isinstance(result, set)

    @patch(
        'test_fixtures.terraform_tests.open',
        mock_open(read_data='output "foo" {\n  value = "bar"\n}\n')
    )
    def test_extracts_single_output(self):
        result = _get_api_common_routing_outputs()
        assert "foo" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_multiple_outputs(self):
        result = _get_api_common_routing_outputs()
        assert len(result) == 2

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_first_output_from_multiple(self):
        result = _get_api_common_routing_outputs()
        assert "api_gateway_id" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
    ))
    def test_extracts_second_output_from_multiple(self):
        result = _get_api_common_routing_outputs()
        assert "lambda_arn" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
    def test_returns_empty_set_for_no_outputs(self):
        result = _get_api_common_routing_outputs()
        assert result == set()

    @patch('test_fixtures.terraform_tests.open', mock_open(read_data='# output "commented" {\n}\n'))
    def test_extracts_commented_output(self):
        result = _get_api_common_routing_outputs()
        assert "commented" in result

    @patch('test_fixtures.terraform_tests.open', mock_open(
        read_data='output "snake_case_name" {\n  value = "test"\n}\n'
    ))
    def test_extracts_snake_case_output_names(self):
        result = _get_api_common_routing_outputs()
        assert "snake_case_name" in result


class TestCreateRemoteStateContractTests:
    def test_returns_class(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert isinstance(result, type)

    def test_returned_class_name(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert result.__name__ == "TestRemoteStateContract"

    def test_class_has_lambda_file_exists_method(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_lambda_file_exists")

    def test_class_has_api_remote_state_references_method(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        assert hasattr(
            result, "test_all_api_remote_state_references_exist_in_api_common_routing_outputs"
        )

    def test_custom_lambda_file_name(self, tmp_path):
        custom_file = tmp_path / "custom_lambda.tf"
        custom_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", lambda_file="custom_lambda.tf"
        )
        assert result is not None

    def test_adds_dynamic_test_for_required_output(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["api_gateway_id"]
        )
        assert hasattr(result, "test_api_gateway_id_output_exists_in_api_common_routing")

    def test_adds_multiple_dynamic_tests_for_required_outputs(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
        )
        assert hasattr(result, "test_output_one_output_exists_in_api_common_routing")

    def test_adds_second_dynamic_test_for_required_outputs(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        result = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
        )
        assert hasattr(result, "test_output_two_output_exists_in_api_common_routing")

    def test_lambda_file_exists_test_passes_when_file_exists(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("# Lambda configuration")
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_lambda_file_exists() is None

    def test_lambda_file_exists_test_fails_when_file_missing(self, tmp_path):
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_lambda_file_exists()

    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_remote_state_references_test_passes_when_all_exist(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('data.terraform_remote_state.api.outputs.api_gateway_id')
        mock_outputs.return_value = {"api_gateway_id"}
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert (
            instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()
            is None
        )

    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_remote_state_references_test_fails_when_missing(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('data.terraform_remote_state.api.outputs.missing_output')
        mock_outputs.return_value = {"other_output"}
        TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()

    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_required_output_test_passes_when_exists(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        mock_outputs.return_value = {"required_output"}
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["required_output"]
        )
        instance = TestClass()
        method = getattr(instance, "test_required_output_output_exists_in_api_common_routing")
        assert method() is None

    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_required_output_test_fails_when_missing(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        mock_outputs.return_value = {"other_output"}
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["required_output"]
        )
        instance = TestClass()
        with pytest.raises(AssertionError):
            getattr(instance, "test_required_output_output_exists_in_api_common_routing")()


class TestCreateRemoteStateConfigTests:
    def test_returns_class(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert isinstance(result, type)

    def test_returned_class_name(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert result.__name__ == "TestRemoteStateConfig"

    def test_class_has_data_tf_exists_method(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_data_tf_exists")

    def test_class_has_no_hardcoded_bucket_method(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_no_hardcoded_bucket_name")

    def test_class_has_no_hardcoded_region_method(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_no_hardcoded_region")

    def test_class_has_correct_state_key_method(self, tmp_path):
        result = create_remote_state_config_tests(tmp_path, "test_endpoint")
        assert hasattr(result, "test_uses_correct_state_key_pattern")

    def test_data_tf_exists_test_passes_when_file_exists(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text("# Data configuration")
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_data_tf_exists() is None

    def test_data_tf_exists_test_fails_when_file_missing(self, tmp_path):
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_data_tf_exists()

    def test_no_hardcoded_bucket_passes_with_dynamic_bucket(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = module.common.name_for_terraform_state_bucket')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_no_hardcoded_bucket_name() is None

    def test_no_hardcoded_bucket_fails_with_terraform_state_pattern(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "mycompany-terraform-state"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_bucket_fails_with_tenulabs_pattern(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "tenulabs-something"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_bucket_fails_with_10ulabs_pattern(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('bucket = "10ulabs-something"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_bucket_name()

    def test_no_hardcoded_region_passes_with_local_region(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = local.aws_region')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_no_hardcoded_region() is None

    def test_no_hardcoded_region_fails_with_hardcoded_region(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = "us-east-1"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_region()

    def test_no_hardcoded_region_fails_with_eu_region(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('region = "eu-west-2"')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_no_hardcoded_region()

    def test_state_key_passes_without_remote_state(self, tmp_path):
        data_file = tmp_path / "data.tf"
        data_file.write_text('# No remote state config')
        TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
        instance = TestClass()
        assert instance.test_uses_correct_state_key_pattern() is None

    def test_state_key_passes_with_correct_api_key(self, tmp_path):
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
    def test_extracts_remote_state_references_from_lambda_file(self, tmp_path):
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
        with patch('test_fixtures.terraform_tests._get_api_common_routing_outputs') as mock_outputs:
            mock_outputs.return_value = {"api_endpoint", "api_gateway_id"}
            TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
            instance = TestClass()
            assert (
                instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()
                is None
            )

    def test_fails_when_referenced_output_missing_from_api_common_routing_outputs(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
API_URL = data.terraform_remote_state.api.outputs.nonexistent_output
''')
        with patch('test_fixtures.terraform_tests._get_api_common_routing_outputs') as mock_outputs:
            mock_outputs.return_value = {"other_output"}
            TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
            instance = TestClass()
            with pytest.raises(AssertionError):
                instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()


class TestDynamicTestMethodDocstrings:
    def test_required_output_test_has_docstring(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["my_output"]
        )
        test_method = getattr(TestClass, "test_my_output_output_exists_in_api_common_routing")
        assert test_method.__doc__ is not None

    def test_required_output_test_docstring_mentions_output_name(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        TestClass = create_remote_state_contract_tests(
            tmp_path, "test_endpoint", required_outputs=["my_output"]
        )
        test_method = getattr(TestClass, "test_my_output_output_exists_in_api_common_routing")
        assert "my_output" in test_method.__doc__


class TestRemoteStateContractMessagesNameTheOutputsFile:
    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_missing_required_output_message_names_outputs_file(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text("")
        mock_outputs.return_value = {"unrelated_output"}
        TestClass = create_remote_state_contract_tests(
            tmp_path, "message_endpoint", required_outputs=["needed_output"]
        )
        method = getattr(TestClass(), "test_needed_output_output_exists_in_api_common_routing")
        expected = re.escape(str(API_COMMON_ROUTING_OUTPUTS_FILE.relative_to(REPO_ROOT)))
        with pytest.raises(AssertionError, match=expected):
            method()

    @patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
    def test_dangling_reference_message_names_outputs_file(self, mock_outputs, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('data.terraform_remote_state.api.outputs.dangling_output')
        mock_outputs.return_value = {"present_output"}
        instance = create_remote_state_contract_tests(tmp_path, "message_endpoint")()
        expected = re.escape(str(API_COMMON_ROUTING_OUTPUTS_FILE.relative_to(REPO_ROOT)))
        with pytest.raises(AssertionError, match=expected):
            instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()
