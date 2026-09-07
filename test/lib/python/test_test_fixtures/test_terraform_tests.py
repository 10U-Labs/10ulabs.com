import re
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock
from unittest.mock import patch, mock_open

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import (
    API_COMMON_ROUTING_OUTPUTS_FILE,
    DEPENDENT_WAIT_JOB,
    _block_named,
    _braced_block,
    _environment_variables_read,
    _environment_variables_supplied,
    _get_api_common_routing_outputs,
    _job_block,
    _packaged_handler_source_path,
    create_lambda_source_contract_tests,
    create_remote_state_contract_tests,
    create_remote_state_config_tests,
    create_routing_wait_contract_tests,
    create_state_lock_contract_tests,
)
from test_fixtures.outcomes import accepted


@patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
def test_returns_set() -> None:
    result = _get_api_common_routing_outputs()
    assert isinstance(result, set)


@patch(
    'test_fixtures.terraform_tests.open',
    mock_open(read_data='output "foo" {\n  value = "bar"\n}\n')
)
def test_extracts_single_output() -> None:
    result = _get_api_common_routing_outputs()
    assert "foo" in result


@patch('test_fixtures.terraform_tests.open', mock_open(
    read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
))
def test_extracts_multiple_outputs() -> None:
    result = _get_api_common_routing_outputs()
    assert len(result) == 2


@patch('test_fixtures.terraform_tests.open', mock_open(
    read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
))
def test_extracts_first_output_from_multiple() -> None:
    result = _get_api_common_routing_outputs()
    assert "api_gateway_id" in result


@patch('test_fixtures.terraform_tests.open', mock_open(
    read_data='output "api_gateway_id" {\n}\noutput "lambda_arn" {\n}\n'
))
def test_extracts_second_output_from_multiple() -> None:
    result = _get_api_common_routing_outputs()
    assert "lambda_arn" in result


@patch('test_fixtures.terraform_tests.open', mock_open(read_data=''))
def test_returns_empty_set_for_no_outputs() -> None:
    result = _get_api_common_routing_outputs()
    assert result == set()


@patch('test_fixtures.terraform_tests.open', mock_open(read_data='# output "commented" {\n}\n'))
def test_extracts_commented_output() -> None:
    result = _get_api_common_routing_outputs()
    assert "commented" in result


@patch('test_fixtures.terraform_tests.open', mock_open(
    read_data='output "snake_case_name" {\n  value = "test"\n}\n'
))
def test_extracts_snake_case_output_names() -> None:
    result = _get_api_common_routing_outputs()
    assert "snake_case_name" in result


def test_create_remote_state_contract_tests_returns_class(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    assert isinstance(result, type)


def test_create_remote_state_contract_tests_returned_class_name(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    assert result.__name__ == "TestRemoteStateContract"


def test_class_has_lambda_file_exists_method(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_lambda_file_exists")


def test_class_has_api_remote_state_references_method(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    assert hasattr(
        result, "test_all_api_remote_state_references_exist_in_api_common_routing_outputs"
    )


def test_custom_lambda_file_name(tmp_path: Path) -> None:
    custom_file = tmp_path / "custom_lambda.tf"
    custom_file.write_text("")
    result = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", lambda_file="custom_lambda.tf"
    )
    assert result is not None


def test_adds_dynamic_test_for_required_output(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["api_gateway_id"]
    )
    assert hasattr(result, "test_api_gateway_id_output_exists_in_api_common_routing")


def test_adds_multiple_dynamic_tests_for_required_outputs(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
    )
    assert hasattr(result, "test_output_one_output_exists_in_api_common_routing")


def test_adds_second_dynamic_test_for_required_outputs(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    result = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["output_one", "output_two"]
    )
    assert hasattr(result, "test_output_two_output_exists_in_api_common_routing")


def test_lambda_file_exists_test_passes_when_file_exists(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("# Lambda configuration")
    TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_lambda_file_exists)


def test_lambda_file_exists_test_fails_when_file_missing(tmp_path: Path) -> None:
    TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_lambda_file_exists()


@patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
def test_remote_state_references_test_passes_when_all_exist(
    mock_outputs: MagicMock,
    tmp_path: Path
) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text('data.terraform_remote_state.api.outputs.api_gateway_id')
    mock_outputs.return_value = {"api_gateway_id"}
    TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(
        instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs
    )


@patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
def test_remote_state_references_test_fails_when_missing(
    mock_outputs: MagicMock,
    tmp_path: Path
) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text('data.terraform_remote_state.api.outputs.missing_output')
    mock_outputs.return_value = {"other_output"}
    TestClass = create_remote_state_contract_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()


@patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
def test_required_output_test_passes_when_exists(mock_outputs: MagicMock, tmp_path: Path) -> None:
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
def test_required_output_test_fails_when_missing(mock_outputs: MagicMock, tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    mock_outputs.return_value = {"other_output"}
    TestClass = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["required_output"]
    )
    instance = TestClass()
    with pytest.raises(AssertionError):
        getattr(instance, "test_required_output_output_exists_in_api_common_routing")()


def test_create_remote_state_config_tests_returns_class(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert isinstance(result, type)


def test_create_remote_state_config_tests_returned_class_name(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert result.__name__ == "TestRemoteStateConfig"


def test_class_has_data_tf_exists_method(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_data_tf_exists")


def test_class_has_no_hardcoded_bucket_method(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_no_hardcoded_bucket_name")


def test_class_has_no_hardcoded_region_method(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_no_hardcoded_region")


def test_class_has_old_state_key_method(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_does_not_use_the_old_api_state_key")


def test_class_has_api_state_key_method(tmp_path: Path) -> None:
    result = create_remote_state_config_tests(tmp_path, "test_endpoint")
    assert hasattr(result, "test_uses_the_api_state_key")


def test_data_tf_exists_test_passes_when_file_exists(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text("# Data configuration")
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_data_tf_exists)


def test_data_tf_exists_test_fails_when_file_missing(tmp_path: Path) -> None:
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_data_tf_exists()


def test_no_hardcoded_bucket_passes_with_dynamic_bucket(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('bucket = module.common.name_for_terraform_state_bucket')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_no_hardcoded_bucket_name)


def test_no_hardcoded_bucket_fails_with_terraform_state_pattern(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('bucket = "mycompany-terraform-state"')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_no_hardcoded_bucket_name()


def test_no_hardcoded_bucket_fails_with_tenulabs_pattern(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('bucket = "tenulabs-something"')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_no_hardcoded_bucket_name()


def test_no_hardcoded_bucket_fails_with_10ulabs_pattern(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('bucket = "10ulabs-something"')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_no_hardcoded_bucket_name()


def test_no_hardcoded_region_passes_with_local_region(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('region = local.aws_region')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_no_hardcoded_region)


def test_no_hardcoded_region_fails_with_hardcoded_region(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('region = "us-east-1"')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_no_hardcoded_region()


def test_no_hardcoded_region_fails_with_eu_region(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('region = "eu-west-2"')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_no_hardcoded_region()


def test_old_state_key_passes_without_remote_state(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('# No remote state config')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_does_not_use_the_old_api_state_key)


def test_api_state_key_passes_without_remote_state(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('# No remote state config')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_uses_the_api_state_key)


CORRECT_API_KEY_TF = '''
terraform_remote_state "api" {
  key = "api/terraform.tfstate"
}
'''


def test_old_state_key_passes_with_correct_api_key(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text(CORRECT_API_KEY_TF)
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_does_not_use_the_old_api_state_key)


def test_api_state_key_passes_with_correct_api_key(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text(CORRECT_API_KEY_TF)
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    assert accepted(instance.test_uses_the_api_state_key)


def test_state_key_fails_with_wrong_api_key(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('''
terraform_remote_state "api" {
  key = "api_common_routing/terraform.tfstate"
}
''')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_does_not_use_the_old_api_state_key()


def test_state_key_fails_when_api_key_missing_but_api_remote_state_present(tmp_path: Path) -> None:
    data_file = tmp_path / "data.tf"
    data_file.write_text('''
terraform_remote_state "api" {
  key = "wrong/terraform.tfstate"
}
''')
    TestClass = create_remote_state_config_tests(tmp_path, "test_endpoint")
    instance = TestClass()
    with pytest.raises(AssertionError):
        instance.test_uses_the_api_state_key()


def test_extracts_remote_state_references_from_lambda_file(tmp_path: Path) -> None:
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
        assert accepted(
            instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs
        )


def test_fails_when_referenced_output_missing_from_api_common_routing_outputs(
    tmp_path: Path
) -> None:
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


def test_required_output_test_has_docstring(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    TestClass = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["my_output"]
    )
    test_method = getattr(TestClass, "test_my_output_output_exists_in_api_common_routing")
    assert test_method.__doc__ is not None


def test_required_output_test_docstring_mentions_output_name(tmp_path: Path) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text("")
    TestClass = create_remote_state_contract_tests(
        tmp_path, "test_endpoint", required_outputs=["my_output"]
    )
    test_method = getattr(TestClass, "test_my_output_output_exists_in_api_common_routing")
    assert "my_output" in test_method.__doc__


@patch('test_fixtures.terraform_tests._get_api_common_routing_outputs')
def test_missing_required_output_message_names_outputs_file(
    mock_outputs: MagicMock,
    tmp_path: Path
) -> None:
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
def test_dangling_reference_message_names_outputs_file(
    mock_outputs: MagicMock,
    tmp_path: Path
) -> None:
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text('data.terraform_remote_state.api.outputs.dangling_output')
    mock_outputs.return_value = {"present_output"}
    instance = create_remote_state_contract_tests(tmp_path, "message_endpoint")()
    expected = re.escape(str(API_COMMON_ROUTING_OUTPUTS_FILE.relative_to(REPO_ROOT)))
    with pytest.raises(AssertionError, match=expected):
        instance.test_all_api_remote_state_references_exist_in_api_common_routing_outputs()

TRACKER_TF = '''
data "archive_file" "handler" {
  source_file = "${path.module}/lambda/tracker/handler.py"
  output_path = "${path.module}/.terraform/handler.zip"
}

resource "aws_lambda_function" "handler" {
  filename = data.archive_file.handler.output_path
  handler  = "handler.lambda_handler"

  environment {
    variables = {
      SESSION_EVENTS_TABLE = aws_dynamodb_table.events.name
    }
  }

  tags = merge(local.common_tags, {
    Name = "Tracker"
  })
}
'''

EXPORTER_TF = '''
data "archive_file" "export_lambda" {
  output_path = "${path.module}/.terraform/export_lambda.zip"

  source {
    content  = file("${path.module}/lambda/tracker/handler.py")
    filename = "handler.py"
  }
}

resource "aws_lambda_function" "handler" {
  filename = data.archive_file.export_lambda.output_path
  handler  = "handler.lambda_handler"
}
'''

ARCHIVE_REFERENCE = "filename = data.archive_file.handler.output_path"
DEFINES_LAMBDA_HANDLER = "def lambda_handler(event, context):\n    return event\n"
READS_THE_TABLE = (
    "def lambda_handler(event, context):\n"
    "    return os.environ['SESSION_EVENTS_TABLE']\n"
)
DEFINES_HANDLE = "def handle(event, context):\n    return event\n"


def _endpoint_with_handler(tmp_path: Path, tf_content: str, handler_content: str) -> Path:
    (tmp_path / "lambda.tf").write_text(tf_content)
    handler_directory = tmp_path / "lambda" / "tracker"
    handler_directory.mkdir(parents=True, exist_ok=True)
    (handler_directory / "handler.py").write_text(handler_content)
    return tmp_path


def _contract_for(endpoint: Path) -> Any:
    return create_lambda_source_contract_tests(endpoint, "lambda.tf", "handler")()


def _handler_check(endpoint: Path) -> Callable[[], None]:
    return _contract_for(endpoint).test_handler_attribute_names_a_function_the_source_defines


def _environment_check(endpoint: Path) -> Callable[[], None]:
    return _contract_for(endpoint).test_environment_variables_supplied_are_the_ones_read


def test_returns_the_inner_text_of_a_block() -> None:
    assert _braced_block("prefix {inner} suffix", 7) == "inner"


def test_returns_the_inner_text_spanning_a_nested_block() -> None:
    assert _braced_block("{outer {nested} tail}", 0) == "outer {nested} tail"


def test_returns_the_remainder_when_the_block_is_never_closed() -> None:
    assert _braced_block("{unterminated", 0) == "unterminated"


def test_finds_the_body_of_the_named_block() -> None:
    content = 'resource "aws_lambda_function" "handler" {\n  timeout = 10\n}\n'
    assert "timeout = 10" in _block_named(content, "resource", "aws_lambda_function", "handler")


def test_returns_empty_string_when_the_block_is_absent() -> None:
    content = 'resource "aws_lambda_function" "other" {\n}\n'
    assert _block_named(content, "resource", "aws_lambda_function", "handler") == ""


def test_returns_the_names_the_block_supplies() -> None:
    block = "environment {\n  variables = {\n    TABLE = local.table\n  }\n}"
    assert _environment_variables_supplied(block) == {"TABLE"}


def test_returns_empty_set_when_the_block_supplies_none() -> None:
    assert _environment_variables_supplied("timeout = 10") == set()


def test_reads_past_a_value_that_interpolates_a_brace() -> None:
    block = 'variables = {\n  FIRST = "${local.a}"\n  SECOND = "plain"\n}'
    assert _environment_variables_supplied(block) == {"FIRST", "SECOND"}


def test_reads_the_subscript_form() -> None:
    assert _environment_variables_read("os.environ['TABLE']") == {"TABLE"}


def test_reads_the_get_form() -> None:
    assert _environment_variables_read('os.environ.get("CONTACT_EMAIL")') == {"CONTACT_EMAIL"}


def test_returns_empty_set_when_the_source_reads_none() -> None:
    assert _environment_variables_read(DEFINES_LAMBDA_HANDLER) == set()


def test_returns_none_when_the_resource_names_no_archive_file() -> None:
    assert _packaged_handler_source_path(TRACKER_TF, "filename = local.zip") is None


def test_reads_the_path_from_source_file() -> None:
    found = _packaged_handler_source_path(TRACKER_TF, ARCHIVE_REFERENCE)
    assert found == "lambda/tracker/handler.py"


def test_reads_the_path_from_a_file_call_in_a_source_block() -> None:
    reference = "filename = data.archive_file.export_lambda.output_path"
    assert _packaged_handler_source_path(EXPORTER_TF, reference) == "lambda/tracker/handler.py"


def test_returns_none_when_the_archive_file_names_no_source() -> None:
    content = 'data "archive_file" "handler" {\n  type = "zip"\n}\n'
    assert _packaged_handler_source_path(content, ARCHIVE_REFERENCE) is None


def test_returns_a_class(tmp_path: Path) -> None:
    result = create_lambda_source_contract_tests(tmp_path, "lambda.tf", "handler")
    assert isinstance(result, type)


def test_create_lambda_source_contract_tests_returned_class_name(tmp_path: Path) -> None:
    result = create_lambda_source_contract_tests(tmp_path, "lambda.tf", "handler")
    assert result.__name__ == "TestLambdaSourceContract"


def test_handler_contract_passes_when_the_source_defines_it(tmp_path: Path) -> None:
    endpoint = _endpoint_with_handler(tmp_path, TRACKER_TF, DEFINES_LAMBDA_HANDLER)
    assert accepted(_handler_check(endpoint))


def test_handler_contract_passes_when_the_archive_uses_a_file_call(tmp_path: Path) -> None:
    endpoint = _endpoint_with_handler(tmp_path, EXPORTER_TF, DEFINES_LAMBDA_HANDLER)
    assert accepted(_handler_check(endpoint))


def test_handler_contract_fails_when_the_source_defines_another_name(tmp_path: Path) -> None:
    endpoint = _endpoint_with_handler(tmp_path, TRACKER_TF, DEFINES_HANDLE)
    with pytest.raises(AssertionError, match="lambda_handler"):
        _handler_check(endpoint)()


def test_handler_contract_fails_when_the_resource_has_no_handler_attribute(tmp_path: Path) -> None:
    without_handler = TRACKER_TF.replace('handler  = "handler.lambda_handler"', "")
    endpoint = _endpoint_with_handler(tmp_path, without_handler, DEFINES_LAMBDA_HANDLER)
    with pytest.raises(AssertionError, match="defines no function"):
        _handler_check(endpoint)()


def test_handler_contract_fails_when_the_terraform_file_is_absent(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="lambda.tf configures"):
        _handler_check(tmp_path)()


def test_handler_contract_names_the_archive_it_could_not_read(tmp_path: Path) -> None:
    without_archive = TRACKER_TF.replace("data.archive_file.handler.output_path", "local.zip")
    endpoint = _endpoint_with_handler(tmp_path, without_archive, DEFINES_LAMBDA_HANDLER)
    with pytest.raises(AssertionError, match="no archive_file in lambda.tf names"):
        _handler_check(endpoint)()


def test_handler_contract_fails_when_the_packaged_source_is_missing(tmp_path: Path) -> None:
    (tmp_path / "lambda.tf").write_text(TRACKER_TF)
    with pytest.raises(AssertionError, match="lambda/tracker/handler.py"):
        _handler_check(tmp_path)()


def test_environment_contract_passes_when_the_two_sets_match(tmp_path: Path) -> None:
    endpoint = _endpoint_with_handler(tmp_path, TRACKER_TF, READS_THE_TABLE)
    assert accepted(_environment_check(endpoint))


def test_environment_contract_fails_on_a_variable_terraform_does_not_supply(
    tmp_path: Path
) -> None:
    source = READS_THE_TABLE + "    prefix = os.environ['S3_PREFIX']\n"
    endpoint = _endpoint_with_handler(tmp_path, TRACKER_TF, source)
    with pytest.raises(AssertionError, match=r"does not supply.*\['S3_PREFIX'\]"):
        _environment_check(endpoint)()


def test_environment_contract_fails_on_a_variable_the_handler_never_reads(tmp_path: Path) -> None:
    endpoint = _endpoint_with_handler(tmp_path, TRACKER_TF, DEFINES_LAMBDA_HANDLER)
    with pytest.raises(AssertionError, match=r"never reads: \['SESSION_EVENTS_TABLE'\]"):
        _environment_check(endpoint)()


def _state_lock_stack(tmp_path: Path, key: str, group: str) -> Path:
    stack_src = tmp_path / "stack"
    stack_src.mkdir()
    (stack_src / "backend.tf").write_text(
        'terraform {\n  backend "s3" {\n' + key + '\n  }\n}\n'
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "a_stack.yml").write_text(
        "name: a_stack\nconcurrency:\n" + group + "\n  cancel-in-progress: false\n"
    )
    return stack_src


def _state_lock_test(tmp_path: Path, key: str, group: str) -> Callable[[], None]:
    stack_src = _state_lock_stack(tmp_path, key, group)
    with patch("test_fixtures.terraform_tests.REPO_ROOT", tmp_path):
        return create_state_lock_contract_tests(stack_src, "a_stack.yml")


ALIGNED_KEY = '    key = "api/operational/health/terraform.tfstate"'
ALIGNED_GROUP = "  group: api/operational/health/terraform.tfstate"


def test_create_state_lock_contract_tests_returns_callable(tmp_path: Path) -> None:
    assert callable(_state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP))


def test_create_state_lock_contract_tests_returned_test_name(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP)
    assert returned.__name__ == "test_group_names_the_state_file"


def test_state_lock_passes_when_key_and_group_agree(tmp_path: Path) -> None:
    assert accepted(_state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP))


def test_state_lock_fails_when_group_names_another_state_file(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, ALIGNED_KEY, "  group: api/operational/diagnostics/terraform.tfstate"
    )
    with pytest.raises(AssertionError):
        returned()


def test_state_lock_fails_when_key_names_another_state_file(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, '    key = "www/common/terraform.tfstate"', ALIGNED_GROUP
    )
    with pytest.raises(AssertionError):
        returned()


def test_state_lock_fails_when_backend_declares_no_key(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, '    region = "us-east-1"', ALIGNED_GROUP)
    with pytest.raises(AssertionError, match="backend.tf declares no key"):
        returned()


def test_state_lock_fails_when_workflow_declares_no_group(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, ALIGNED_KEY, "  cancel-in-progress: true")
    with pytest.raises(AssertionError, match="a_stack.yml declares no concurrency group"):
        returned()


def test_state_lock_message_calls_the_equality_a_naming_convention(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, ALIGNED_KEY, "  group: www/common/terraform.tfstate"
    )
    with pytest.raises(AssertionError, match="naming convention"):
        returned()


WAIT_JOB_DECLARED = (
    f"  {DEPENDENT_WAIT_JOB}:\n"
    "    runs-on: ubuntu-latest\n"
)

RECONCILIATION_ORDERED = (
    "  reconciliation:\n"
    "    if: >-\n"
    f"      needs.{DEPENDENT_WAIT_JOB}.outputs.apply == 'true'\n"
    "    needs:\n"
    "      - unit-tests-module\n"
    f"      - {DEPENDENT_WAIT_JOB}\n"
    "      - yamllint\n"
    "    runs-on: ubuntu-latest\n"
)

RECONCILIATION_UNORDERED = (
    "  reconciliation:\n"
    "    needs:\n"
    "      - unit-tests-module\n"
    "      - yamllint\n"
    "    runs-on: ubuntu-latest\n"
)

WORKFLOW_TRAILER = "name: a_stack\n"


def _routing_wait_contract(tmp_path: Path, jobs: str) -> Any:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "a_stack.yml").write_text("jobs:\n" + jobs + WORKFLOW_TRAILER)
    with patch("test_fixtures.terraform_tests.REPO_ROOT", tmp_path):
        return create_routing_wait_contract_tests("a_stack.yml")()


def _ordered_contract(tmp_path: Path) -> Any:
    return _routing_wait_contract(
        tmp_path, RECONCILIATION_ORDERED + WAIT_JOB_DECLARED
    )


def _unordered_contract(tmp_path: Path) -> Any:
    return _routing_wait_contract(tmp_path, RECONCILIATION_UNORDERED)


def test_job_block_reads_the_last_job_to_the_end_of_the_file() -> None:
    workflow = "jobs:\n  only-job:\n    runs-on: ubuntu-latest\n"
    assert _job_block(workflow, "only-job") == "    runs-on: ubuntu-latest\n"


def test_job_block_is_empty_when_the_workflow_declares_no_such_job() -> None:
    assert _job_block("jobs:\n  only-job:\n", "another-job") == ""


def test_routing_wait_passes_when_the_workflow_declares_the_wait_job(tmp_path: Path) -> None:
    contract = _ordered_contract(tmp_path)
    assert accepted(contract.test_the_workflow_declares_the_wait_job)


def test_routing_wait_fails_when_the_workflow_declares_no_wait_job(tmp_path: Path) -> None:
    contract = _unordered_contract(tmp_path)
    with pytest.raises(AssertionError, match="declares no wait-for-api-common-routing job"):
        contract.test_the_workflow_declares_the_wait_job()


def test_routing_wait_passes_when_reconciliation_needs_the_wait_job(tmp_path: Path) -> None:
    contract = _ordered_contract(tmp_path)
    assert accepted(contract.test_reconciliation_needs_the_wait_job)


def test_routing_wait_fails_when_reconciliation_does_not_need_the_wait_job(tmp_path: Path) -> None:
    contract = _unordered_contract(tmp_path)
    with pytest.raises(AssertionError, match="does not name wait-for-api-common-routing in needs"):
        contract.test_reconciliation_needs_the_wait_job()


def test_routing_wait_passes_when_reconciliation_reads_the_apply_output(tmp_path: Path) -> None:
    contract = _ordered_contract(tmp_path)
    assert accepted(
        contract.test_reconciliation_applies_only_on_the_conclusion_the_wait_job_reports
    )


def test_routing_wait_fails_when_reconciliation_ignores_the_apply_output(tmp_path: Path) -> None:
    contract = _unordered_contract(tmp_path)
    with pytest.raises(AssertionError, match="does not require"):
        contract.test_reconciliation_applies_only_on_the_conclusion_the_wait_job_reports()
