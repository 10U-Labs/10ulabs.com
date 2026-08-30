from pathlib import Path
from unittest.mock import patch

from terraform_config import (
    TEST_AWS_REGION,
    _parse_map_block,
    _resolve_all_refs,
    _resolve_lambda_function_name,
    _resolve_local_interpolations,
    _resolve_prefix_refs,
    extract_lambda_function_names,
    get_endpoint_local_values,
    get_resource_prefix,
    get_shared_config,
    get_tfvars_values,
    packaged_lambda_archives,
    packaged_lambda_sources,
    parse_lambda_handler_names,
    _parse_locals,
    _parse_outputs,
)


class TestParseMapBlock:
    def test_parses_simple_map(self):
        content = '''
        my_map = {
            key1 = "value1"
            key2 = "value2"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_returns_empty_dict_when_map_not_found(self):
        content = '''
        other_map = {
            key1 = "value1"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert not result

    def test_handles_nested_braces(self):
        content = '''
        lambda_handler_names = {
            webhook = "${local.resource_prefix}WebhookHandler"
            runner  = "${local.resource_prefix}RunnerHandler"
        }
        '''
        result = _parse_map_block(content, "lambda_handler_names")
        assert result == {
            "webhook": "${local.resource_prefix}WebhookHandler",
            "runner": "${local.resource_prefix}RunnerHandler",
        }

    def test_handles_empty_map(self):
        content = '''
        empty_map = {
        }
        '''
        result = _parse_map_block(content, "empty_map")
        assert not result


class TestResolvePrefixRefs:
    def test_resolves_module_shared_resource_prefix(self):
        value = "${module.common.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_local_resource_prefix(self):
        value = "${local.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_multiple_refs(self):
        value = "${local.resource_prefix}-${module.common.resource_prefix}"
        result = _resolve_prefix_refs(value, "Prefix")
        assert result == "Prefix-Prefix"

    def test_returns_unchanged_when_no_refs(self):
        value = "StaticValue"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "StaticValue"


class TestResolveLocalInterpolations:
    def test_resolves_single_local(self):
        value = "${local.my_var}"
        local_values = {"my_var": "resolved_value"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "resolved_value"

    def test_resolves_nested_locals(self):
        value = "${local.outer}"
        local_values = {
            "outer": "${local.inner}",
            "inner": "final_value",
        }
        result = _resolve_local_interpolations(value, local_values)
        assert result == "final_value"

    def test_resolves_deeply_nested_locals(self):
        value = "${local.level1}"
        local_values = {
            "level1": "${local.level2}",
            "level2": "${local.level3}",
            "level3": "final_value",
        }
        result = _resolve_local_interpolations(value, local_values)
        assert result == "final_value"

    def test_returns_unchanged_when_local_not_found(self):
        value = "${local.missing_var}"
        local_values = {"other_var": "value"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "${local.missing_var}"

    def test_resolves_multiple_locals_in_string(self):
        value = "${local.prefix}-${local.suffix}"
        local_values = {"prefix": "start", "suffix": "end"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "start-end"


class TestResolveAllRefs:
    def test_resolves_prefix_and_handler_names(self):
        value = "${module.common.resource_prefix}-${module.common.lambda_handler_names.webhook}"
        handler_names = {"webhook": "TenULabsWebhook"}
        result = _resolve_all_refs(value, "TenULabs", handler_names)
        assert result == "TenULabs-TenULabsWebhook"

    def test_resolves_only_prefix_when_no_handlers(self):
        value = "${module.common.resource_prefix}Function"
        result = _resolve_all_refs(value, "TenULabs", {})
        assert result == "TenULabsFunction"

    def test_returns_unchanged_when_handler_not_found(self):
        value = "${module.common.lambda_handler_names.missing}"
        result = _resolve_all_refs(value, "TenULabs", {"webhook": "Handler"})
        assert result == "${module.common.lambda_handler_names.missing}"


class TestResolveLambdaFunctionName:
    def test_resolves_quoted_string(self):
        block = '''
        function_name = "${module.common.resource_prefix}MyFunction"
        runtime       = "python3.11"
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {})
        assert result == "TenULabsMyFunction"

    def test_resolves_local_reference(self):
        block = '''
        function_name = local.handler_name
        runtime       = "python3.11"
        '''
        locals_map = {"handler_name": "MyHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", locals_map, {}, {})
        assert result == "MyHandler"

    def test_resolves_var_reference(self):
        block = '''
        function_name = var.lambda_name
        runtime       = "python3.11"
        '''
        tfvars = {"lambda_name": "VarHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", {}, tfvars, {})
        assert result == "VarHandler"

    def test_resolves_module_shared_handler_reference(self):
        block = '''
        function_name = module.common.lambda_handler_names.webhook
        runtime       = "python3.11"
        '''
        handlers = {"webhook": "TenULabsWebhookHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, handlers)
        assert result == "TenULabsWebhookHandler"

    def test_returns_none_when_no_function_name(self):
        block = '''
        runtime = "python3.11"
        handler = "index.handler"
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {})
        assert result is None

    def test_returns_none_for_local_not_in_map(self):
        block = '''
        function_name = local.missing_name
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {"other": "value"}, {}, {})
        assert result is None

    def test_returns_none_for_var_not_in_tfvars(self):
        block = '''
        function_name = var.missing_name
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {"other": "value"}, {})
        assert result is None

    def test_returns_none_for_handler_not_in_map(self):
        block = '''
        function_name = module.common.lambda_handler_names.missing
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {"other": "value"})
        assert result is None


class TestParseLocals:
    def test_returns_dict(self):
        result = _parse_locals()
        assert isinstance(result, dict)

    def test_contains_aws_region(self):
        result = _parse_locals()
        assert "aws_region" in result

    def test_contains_resource_prefix(self):
        result = _parse_locals()
        assert "resource_prefix" in result


class TestParseLambdaHandlerNames:
    def test_returns_dict(self):
        result = parse_lambda_handler_names()
        assert isinstance(result, dict)

    def test_values_do_not_contain_unresolved_local_resource_prefix(self):
        result = parse_lambda_handler_names()
        unresolved_values = [v for v in result.values() if "${local.resource_prefix}" in v]
        assert not unresolved_values


def test_parse_outputs_returns_dict():
    result = _parse_outputs()
    assert isinstance(result, dict)


class TestGetSharedConfig:
    def test_returns_dict(self):
        result = get_shared_config()
        assert isinstance(result, dict)

    def test_contains_lambda_handler_names_key(self):
        result = get_shared_config()
        assert "lambda_handler_names" in result

    def test_lambda_handler_names_is_dict(self):
        result = get_shared_config()
        assert isinstance(result["lambda_handler_names"], dict)

    def test_omits_aws_account_id(self):
        result = get_shared_config()
        assert "aws_account_id" not in result


class TestTestAwsRegion:
    def test_is_string(self):
        assert isinstance(TEST_AWS_REGION, str)

    def test_is_valid_region_format(self):
        assert TEST_AWS_REGION.startswith("us-") or TEST_AWS_REGION.startswith("eu-")


class TestGetResourcePrefix:
    def test_returns_string(self):
        result = get_resource_prefix()
        assert isinstance(result, str)

    def test_returns_non_empty(self):
        result = get_resource_prefix()
        assert len(result) > 0


class TestGetTfvarsValues:
    def test_returns_empty_for_nonexistent_dir(self):
        result = get_tfvars_values(Path("/nonexistent/path"))
        assert not result

    def test_parses_string_values(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('my_var = "my_value"\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_var": "my_value"}

    def test_parses_list_values(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('my_list = ["a", "b", "c"]\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_list": ["a", "b", "c"]}

    def test_ignores_comments(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('# This is a comment\nmy_var = "value"\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_var": "value"}


class TestGetEndpointLocalValues:
    def test_returns_empty_for_nonexistent_file(self):
        result = get_endpoint_local_values(Path("/nonexistent/path"))
        assert not result

    def test_parses_local_values(self, tmp_path):
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text('locals {\n  my_local = "my_value"\n}\n')
        result = get_endpoint_local_values(tmp_path)
        assert result.get("my_local") == "my_value"

    def test_parses_module_shared_handler_reference(self, tmp_path):
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text(
            'locals {\n  handler = module.common.lambda_handler_names.webhook\n}\n'
        )
        with patch("terraform_config.parse_lambda_handler_names") as mock_handlers:
            mock_handlers.return_value = {"webhook": "TenULabsWebhook"}
            with patch("terraform_config.get_resource_prefix") as mock_prefix:
                mock_prefix.return_value = "TenULabs"
                result = get_endpoint_local_values(tmp_path)
        assert result.get("handler") == "TenULabsWebhook"


class TestExtractLambdaFunctionNames:
    def test_returns_empty_for_nonexistent_file(self):
        result = extract_lambda_function_names(Path("/nonexistent/file.tf"))
        assert not result

    def test_extracts_quoted_name_returns_single_result(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = "MyFunctionName"
  handler = "index.handler"
  runtime = "python3.11"
}
''')
        result = extract_lambda_function_names(lambda_file)
        assert len(result) == 1

    def test_extracts_quoted_name_returns_correct_tuple(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = "MyFunctionName"
  handler = "index.handler"
  runtime = "python3.11"
}
''')
        result = extract_lambda_function_names(lambda_file)
        assert result[0] == ("my_func", "MyFunctionName")

    def test_with_use_handler_names_returns_single_result(self, tmp_path):
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = "StaticName"
  runtime = "python3.11"
}
''')
        result = extract_lambda_function_names(lambda_file, use_handler_names=True)
        assert len(result) == 1


class TestResolveLocalInterpolationsMaxIterations:
    def test_handles_circular_reference_without_infinite_loop(self):
        value = "${local.a}"
        local_values = {
            "a": "${local.b}",
            "b": "${local.a}",
        }
        result = _resolve_local_interpolations(value, local_values)
        assert result in ["${local.a}", "${local.b}"]

    def test_handles_deep_nesting_beyond_resolution(self):
        value = "${local.level0}"
        local_values = {f"level{i}": f"${{local.level{i+1}}}" for i in range(15)}
        local_values["level15"] = "final"

        result = _resolve_local_interpolations(value, local_values)
        assert "${local." in result or result == "final"


class TestGetTfvarsValuesAdditional:
    def test_parses_string_values(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('region = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("region") == "us-east-1"

    def test_parses_list_values(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('tags = ["tag1", "tag2"]\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("tags") == ["tag1", "tag2"]

    def test_skips_comments_and_empty_lines(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('# comment\n\nregion = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("region") == "us-east-1"

    def test_skips_non_matching_number_lines(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('some_number = 42\nregion = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert "some_number" not in result

    def test_parses_string_after_skipping_number(self, tmp_path):
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('some_number = 42\nregion = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("region") == "us-east-1"

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        result = get_tfvars_values(tmp_path)
        assert not result


class TestGetSharedConfigDomainName:
    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_sets_api_fqdn_when_domain_name_present(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        mock_locals.return_value = {"domain_name": "example.com"}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert result.get("api_fqdn") == "api.example.com"

    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_empty(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        mock_locals.return_value = {"domain_name": ""}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result

    @patch('terraform_config._parse_locals')
    @patch('terraform_config._parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_missing(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        mock_locals.return_value = {}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result


class TestResolveLocalInterpolationsMaxIterationsExhaustion:
    def test_exhausts_max_iterations_leaves_unresolved_reference(self):
        value = "${local.a}"
        local_values = {"a": "x${local.a}y"}

        result = _resolve_local_interpolations(value, local_values)
        assert "${local.a}" in result

    def test_exhausts_max_iterations_adds_prefix_each_iteration(self):
        value = "${local.a}"
        local_values = {"a": "x${local.a}y"}

        result = _resolve_local_interpolations(value, local_values)
        assert result.count("x") == 10

    def test_exhausts_max_iterations_adds_suffix_each_iteration(self):
        value = "${local.a}"
        local_values = {"a": "x${local.a}y"}

        result = _resolve_local_interpolations(value, local_values)
        assert result.count("y") == 10


def test_get_endpoint_local_values_skips_an_unknown_handler(tmp_path):
    locals_file = tmp_path / "locals.tf"
    locals_file.write_text(
        'locals {\n  handler = module.common.lambda_handler_names.nonexistent\n}\n'
    )
    with patch("terraform_config.parse_lambda_handler_names") as mock_handlers:
        mock_handlers.return_value = {"webhook": "WebhookHandler"}
        with patch("terraform_config.get_resource_prefix") as mock_prefix:
            mock_prefix.return_value = "TenULabs"
            result = get_endpoint_local_values(tmp_path)
    assert "handler" not in result


def test_extract_lambda_function_names_skips_an_unresolvable_name(tmp_path):
    lambda_file = tmp_path / "lambda.tf"
    lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = data.aws_caller_identity.current.account_id
  handler = "index.handler"
  runtime = "python3.11"
}
''')
    (tmp_path / "locals.tf").write_text("")
    (tmp_path / "terraform.tfvars").write_text("")
    result = extract_lambda_function_names(lambda_file)
    assert len(result) == 0


def test_packaged_lambda_sources_reads_a_single_packaged_file(tmp_path):
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/handler.py"]


def test_packaged_lambda_sources_reads_a_named_archive_entry(tmp_path):
    tf_file = tmp_path / "analytics.tf"
    tf_file.write_text("""
data "archive_file" "export" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/exporter/handler.py")
    filename = "handler.py"
  }
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/exporter/handler.py"]


def test_packaged_lambda_sources_omits_a_file_from_outside_the_stack(tmp_path):
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/lambda_http/__init__.py")
    filename = "lambda_http.py"
  }
}
""")
    assert packaged_lambda_sources(tf_file) == ["lambda/handler.py"]


def test_packaged_lambda_archives_reads_the_archive_a_package_is_written_to(tmp_path):
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/handler.zip"
}
""")
    assert packaged_lambda_archives(tf_file) == [
        ".terraform/lambda_packages/handler.zip"
    ]


def test_packaged_lambda_archives_reads_every_package_a_file_declares(tmp_path):
    tf_file = tmp_path / "lambda.tf"
    tf_file.write_text("""
data "archive_file" "tracker" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/tracker.zip"
}

data "archive_file" "exporter" {
  type        = "zip"
  output_path = "${path.module}/.terraform/lambda_packages/exporter.zip"
}
""")
    assert packaged_lambda_archives(tf_file) == [
        ".terraform/lambda_packages/tracker.zip",
        ".terraform/lambda_packages/exporter.zip",
    ]


def test_packaged_lambda_archives_reads_nothing_from_a_file_that_packages_nothing(
    tmp_path,
):
    tf_file = tmp_path / "dynamodb.tf"
    tf_file.write_text("""
resource "aws_dynamodb_table" "sessions" {
  name = "sessions"
}
""")
    assert not packaged_lambda_archives(tf_file)
