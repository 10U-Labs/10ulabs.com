"""Unit tests for terraform_config module."""
import pytest

from unittest.mock import patch

from terraform_config import (
    _parse_map_block,
    _resolve_prefix_refs,
    _resolve_local_interpolations,
    _resolve_all_refs,
    _resolve_lambda_function_name,
    get_tfvars_values,
    get_shared_config,
)


class TestParseMapBlock:
    """Tests for _parse_map_block function."""

    def test_parses_simple_map(self):
        """Test parsing a simple map block."""
        content = '''
        my_map = {
            key1 = "value1"
            key2 = "value2"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_returns_empty_dict_when_map_not_found(self):
        """Test returns empty dict when map doesn't exist."""
        content = '''
        other_map = {
            key1 = "value1"
        }
        '''
        result = _parse_map_block(content, "my_map")
        assert result == {}

    def test_handles_nested_braces(self):
        """Test handles content with nested braces."""
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
        """Test handles empty map block."""
        content = '''
        empty_map = {
        }
        '''
        result = _parse_map_block(content, "empty_map")
        assert result == {}


class TestResolvePrefixRefs:
    """Tests for _resolve_prefix_refs function."""

    def test_resolves_module_shared_resource_prefix(self):
        """Test resolves module.common.resource_prefix."""
        value = "${module.common.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_local_resource_prefix(self):
        """Test resolves local.resource_prefix."""
        value = "${local.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_multiple_refs(self):
        """Test resolves multiple references in same string."""
        value = "${local.resource_prefix}-${module.common.resource_prefix}"
        result = _resolve_prefix_refs(value, "Prefix")
        assert result == "Prefix-Prefix"

    def test_returns_unchanged_when_no_refs(self):
        """Test returns unchanged when no references present."""
        value = "StaticValue"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "StaticValue"


class TestResolveLocalInterpolations:
    """Tests for _resolve_local_interpolations function."""

    def test_resolves_single_local(self):
        """Test resolves a single local reference."""
        value = "${local.my_var}"
        local_values = {"my_var": "resolved_value"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "resolved_value"

    def test_resolves_nested_locals(self):
        """Test resolves nested local references."""
        value = "${local.outer}"
        local_values = {
            "outer": "${local.inner}",
            "inner": "final_value",
        }
        result = _resolve_local_interpolations(value, local_values)
        assert result == "final_value"

    def test_resolves_deeply_nested_locals(self):
        """Test resolves deeply nested local references requiring multiple iterations."""
        value = "${local.level1}"
        local_values = {
            "level1": "${local.level2}",
            "level2": "${local.level3}",
            "level3": "final_value",
        }
        result = _resolve_local_interpolations(value, local_values)
        assert result == "final_value"

    def test_returns_unchanged_when_local_not_found(self):
        """Test returns unchanged when local not in dict."""
        value = "${local.missing_var}"
        local_values = {"other_var": "value"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "${local.missing_var}"

    def test_resolves_multiple_locals_in_string(self):
        """Test resolves multiple locals in same string."""
        value = "${local.prefix}-${local.suffix}"
        local_values = {"prefix": "start", "suffix": "end"}
        result = _resolve_local_interpolations(value, local_values)
        assert result == "start-end"


class TestResolveAllRefs:
    """Tests for _resolve_all_refs function."""

    def test_resolves_prefix_and_handler_names(self):
        """Test resolves both prefix and handler name references."""
        value = "${module.common.resource_prefix}-${module.common.lambda_handler_names.webhook}"
        handler_names = {"webhook": "TenULabsWebhook"}
        result = _resolve_all_refs(value, "TenULabs", handler_names)
        assert result == "TenULabs-TenULabsWebhook"

    def test_resolves_only_prefix_when_no_handlers(self):
        """Test resolves prefix when handler_names is empty."""
        value = "${module.common.resource_prefix}Function"
        result = _resolve_all_refs(value, "TenULabs", {})
        assert result == "TenULabsFunction"

    def test_returns_unchanged_when_handler_not_found(self):
        """Test returns partial resolution when handler not in dict."""
        value = "${module.common.lambda_handler_names.missing}"
        result = _resolve_all_refs(value, "TenULabs", {"webhook": "Handler"})
        assert result == "${module.common.lambda_handler_names.missing}"


class TestResolveLambdaFunctionName:
    """Tests for _resolve_lambda_function_name function."""

    def test_resolves_quoted_string(self):
        """Test resolves function_name from quoted string."""
        block = '''
        function_name = "${module.common.resource_prefix}MyFunction"
        runtime       = "python3.11"
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {})
        assert result == "TenULabsMyFunction"

    def test_resolves_local_reference(self):
        """Test resolves function_name from local reference."""
        block = '''
        function_name = local.handler_name
        runtime       = "python3.11"
        '''
        locals_map = {"handler_name": "MyHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", locals_map, {}, {})
        assert result == "MyHandler"

    def test_resolves_var_reference(self):
        """Test resolves function_name from var reference."""
        block = '''
        function_name = var.lambda_name
        runtime       = "python3.11"
        '''
        tfvars = {"lambda_name": "VarHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", {}, tfvars, {})
        assert result == "VarHandler"

    def test_resolves_module_shared_handler_reference(self):
        """Test resolves function_name from module.common.lambda_handler_names."""
        block = '''
        function_name = module.common.lambda_handler_names.webhook
        runtime       = "python3.11"
        '''
        handlers = {"webhook": "TenULabsWebhookHandler"}
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, handlers)
        assert result == "TenULabsWebhookHandler"

    def test_returns_none_when_no_function_name(self):
        """Test returns None when function_name not found."""
        block = '''
        runtime = "python3.11"
        handler = "index.handler"
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {})
        assert result is None

    def test_returns_none_for_local_not_in_map(self):
        """Test returns None when local reference not in map."""
        block = '''
        function_name = local.missing_name
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {"other": "value"}, {}, {})
        assert result is None

    def test_returns_none_for_var_not_in_tfvars(self):
        """Test returns None when var reference not in tfvars."""
        block = '''
        function_name = var.missing_name
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {"other": "value"}, {})
        assert result is None

    def test_returns_none_for_handler_not_in_map(self):
        """Test returns None when handler reference not in map."""
        block = '''
        function_name = module.common.lambda_handler_names.missing
        '''
        result = _resolve_lambda_function_name(block, "TenULabs", {}, {}, {"other": "value"})
        assert result is None


# Integration tests using real shared module files
class TestParseLocals:
    """Tests for parse_locals function."""

    def test_returns_dict(self):
        """Test parse_locals returns a dict."""
        from terraform_config import parse_locals
        result = parse_locals()
        assert isinstance(result, dict)

    def test_contains_aws_region(self):
        """Test parse_locals contains aws_region."""
        from terraform_config import parse_locals
        result = parse_locals()
        assert "aws_region" in result

    def test_contains_resource_prefix(self):
        """Test parse_locals contains resource_prefix."""
        from terraform_config import parse_locals
        result = parse_locals()
        assert "resource_prefix" in result


class TestParseLambdaHandlerNames:
    """Tests for parse_lambda_handler_names function."""

    def test_returns_dict(self):
        """Test parse_lambda_handler_names returns a dict."""
        from terraform_config import parse_lambda_handler_names
        result = parse_lambda_handler_names()
        assert isinstance(result, dict)

    def test_values_do_not_contain_unresolved_local_resource_prefix(self):
        """Test handler name values do not contain unresolved local.resource_prefix."""
        from terraform_config import parse_lambda_handler_names
        result = parse_lambda_handler_names()
        unresolved_values = [v for v in result.values() if "${local.resource_prefix}" in v]
        assert unresolved_values == []


class TestParseOutputs:
    """Tests for parse_outputs function."""

    def test_returns_dict(self):
        """Test parse_outputs returns a dict."""
        from terraform_config import parse_outputs
        result = parse_outputs()
        assert isinstance(result, dict)


class TestGetSharedConfig:
    """Tests for get_shared_config function."""

    def test_returns_dict(self):
        """Test get_shared_config returns a dict."""
        from terraform_config import get_shared_config
        result = get_shared_config()
        assert isinstance(result, dict)

    def test_contains_lambda_handler_names_key(self):
        """Test get_shared_config includes lambda_handler_names key."""
        from terraform_config import get_shared_config
        result = get_shared_config()
        assert "lambda_handler_names" in result

    def test_lambda_handler_names_is_dict(self):
        """Test get_shared_config lambda_handler_names value is a dict."""
        from terraform_config import get_shared_config
        result = get_shared_config()
        assert isinstance(result["lambda_handler_names"], dict)


class TestTestAwsRegion:
    """Tests for TEST_AWS_REGION constant."""

    def test_is_string(self):
        """Test TEST_AWS_REGION is a string."""
        from terraform_config import TEST_AWS_REGION
        assert isinstance(TEST_AWS_REGION, str)

    def test_is_valid_region_format(self):
        """Test TEST_AWS_REGION matches AWS region format."""
        from terraform_config import TEST_AWS_REGION
        assert TEST_AWS_REGION.startswith("us-") or TEST_AWS_REGION.startswith("eu-")


class TestGetResourcePrefix:
    """Tests for get_resource_prefix function."""

    def test_returns_string(self):
        """Test get_resource_prefix returns a string."""
        from terraform_config import get_resource_prefix
        result = get_resource_prefix()
        assert isinstance(result, str)

    def test_returns_non_empty(self):
        """Test get_resource_prefix returns non-empty string."""
        from terraform_config import get_resource_prefix
        result = get_resource_prefix()
        assert len(result) > 0


class TestGetRunnersResourceNames:
    """Tests for get_runners_resource_names function."""

    def test_returns_dict(self):
        """Test get_runners_resource_names returns a dict."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names()
        assert isinstance(result, dict)

    def test_contains_idempotency_table_key(self):
        """Test get_runners_resource_names contains idempotency_table key."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names()
        assert "idempotency_table" in result

    def test_contains_circuit_breaker_state_table_key(self):
        """Test get_runners_resource_names contains circuit_breaker_state_table key."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names()
        assert "circuit_breaker_state_table" in result

    def test_contains_job_queue_key(self):
        """Test get_runners_resource_names contains job_queue key."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names()
        assert "job_queue" in result

    def test_contains_job_dlq_key(self):
        """Test get_runners_resource_names contains job_dlq key."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names()
        assert "job_dlq" in result

    def test_custom_prefix_applies_to_circuit_breaker_state_table(self):
        """Test get_runners_resource_names applies custom prefix to circuit_breaker_state_table."""
        from terraform_config import get_runners_resource_names
        result = get_runners_resource_names(prefix="Custom")
        assert result["circuit_breaker_state_table"].startswith("Custom")


class TestGetTfvarsValues:
    """Tests for get_tfvars_values function."""

    def test_returns_empty_for_nonexistent_dir(self):
        """Test returns empty dict for nonexistent directory."""
        from pathlib import Path
        from terraform_config import get_tfvars_values
        result = get_tfvars_values(Path("/nonexistent/path"))
        assert result == {}

    def test_parses_string_values(self, tmp_path):
        """Test parses string values from tfvars."""
        from terraform_config import get_tfvars_values
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('my_var = "my_value"\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_var": "my_value"}

    def test_parses_list_values(self, tmp_path):
        """Test parses list values from tfvars."""
        from terraform_config import get_tfvars_values
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('my_list = ["a", "b", "c"]\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_list": ["a", "b", "c"]}

    def test_ignores_comments(self, tmp_path):
        """Test ignores comment lines."""
        from terraform_config import get_tfvars_values
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('# This is a comment\nmy_var = "value"\n')
        result = get_tfvars_values(tmp_path)
        assert result == {"my_var": "value"}


class TestGetEndpointLocalValues:
    """Tests for get_endpoint_local_values function."""

    def test_returns_empty_for_nonexistent_file(self):
        """Test returns empty dict when locals.tf doesn't exist."""
        from pathlib import Path
        from terraform_config import get_endpoint_local_values
        result = get_endpoint_local_values(Path("/nonexistent/path"))
        assert result == {}

    def test_parses_local_values(self, tmp_path):
        """Test parses local values from locals.tf."""
        from terraform_config import get_endpoint_local_values
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text('locals {\n  my_local = "my_value"\n}\n')
        result = get_endpoint_local_values(tmp_path)
        assert result.get("my_local") == "my_value"

    def test_parses_module_shared_handler_reference(self, tmp_path):
        """Test parses module.common.lambda_handler_names references."""
        from unittest.mock import patch
        from terraform_config import get_endpoint_local_values
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


class TestExtractIamRoleNames:
    """Tests for extract_iam_role_names function."""

    def test_returns_empty_for_nonexistent_file(self):
        """Test returns empty list when file doesn't exist."""
        from pathlib import Path
        from terraform_config import extract_iam_role_names
        result = extract_iam_role_names(Path("/nonexistent/file.tf"))
        assert result == []

    def test_extracts_quoted_name_returns_single_result(self, tmp_path):
        """Test extracts exactly one role from file with one role definition."""
        from terraform_config import extract_iam_role_names
        iam_file = tmp_path / "iam.tf"
        iam_file.write_text('''
resource "aws_iam_role" "my_role" {
  name = "MyRoleName"
  assume_role_policy = jsonencode({})
}
''')
        result = extract_iam_role_names(iam_file)
        assert len(result) == 1

    def test_extracts_quoted_name_returns_correct_tuple(self, tmp_path):
        """Test extracts correct resource name and role name tuple."""
        from terraform_config import extract_iam_role_names
        iam_file = tmp_path / "iam.tf"
        iam_file.write_text('''
resource "aws_iam_role" "my_role" {
  name = "MyRoleName"
  assume_role_policy = jsonencode({})
}
''')
        result = extract_iam_role_names(iam_file)
        assert result[0] == ("my_role", "MyRoleName")

    def test_extracts_var_reference_name(self, tmp_path):
        """Test extracts role name from var reference when in tfvars."""
        from terraform_config import extract_iam_role_names
        iam_file = tmp_path / "iam.tf"
        iam_file.write_text('''
resource "aws_iam_role" "my_role" {
  name = var.role_name
  assume_role_policy = jsonencode({})
}
''')
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('role_name = "VarRoleName"\n')
        (tmp_path / "locals.tf").write_text("")
        result = extract_iam_role_names(iam_file)
        assert result[0] == ("my_role", "VarRoleName")

    def test_extracts_local_reference_name(self, tmp_path):
        """Test extracts role name from local reference."""
        from terraform_config import extract_iam_role_names
        iam_file = tmp_path / "iam.tf"
        iam_file.write_text('''
resource "aws_iam_role" "my_role" {
  name = local.role_name
  assume_role_policy = jsonencode({})
}
''')
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text('locals {\n  role_name = "LocalRoleName"\n}\n')
        result = extract_iam_role_names(iam_file)
        assert result[0] == ("my_role", "LocalRoleName")


class TestExtractLambdaFunctionNames:
    """Tests for extract_lambda_function_names function."""

    def test_returns_empty_for_nonexistent_file(self):
        """Test returns empty list when file doesn't exist."""
        from pathlib import Path
        from terraform_config import extract_lambda_function_names
        result = extract_lambda_function_names(Path("/nonexistent/file.tf"))
        assert result == []

    def test_extracts_quoted_name_returns_single_result(self, tmp_path):
        """Test extracts exactly one function from file with one function definition."""
        from terraform_config import extract_lambda_function_names
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
        """Test extracts correct resource name and function name tuple."""
        from terraform_config import extract_lambda_function_names
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
        """Test with use_handler_names=True returns exactly one result."""
        from terraform_config import extract_lambda_function_names
        lambda_file = tmp_path / "lambda.tf"
        lambda_file.write_text('''
resource "aws_lambda_function" "my_func" {
  function_name = "StaticName"
  runtime = "python3.11"
}
''')
        result = extract_lambda_function_names(lambda_file, use_handler_names=True)
        assert len(result) == 1


class TestExtractSqsQueueNames:
    """Tests for extract_sqs_queue_names function."""

    def test_returns_empty_for_nonexistent_file(self):
        """Test returns empty list when file doesn't exist."""
        from pathlib import Path
        from terraform_config import extract_sqs_queue_names
        result = extract_sqs_queue_names(Path("/nonexistent/file.tf"))
        assert result == []

    def test_extracts_quoted_name_returns_single_result(self, tmp_path):
        """Test extracts exactly one queue from file with one queue definition."""
        from terraform_config import extract_sqs_queue_names
        (tmp_path / "locals.tf").write_text("")  # Empty locals
        sqs_file = tmp_path / "sqs.tf"
        sqs_file.write_text('''
resource "aws_sqs_queue" "my_queue" {
  name = "MyQueueName"
}
''')
        result = extract_sqs_queue_names(sqs_file)
        assert len(result) == 1

    def test_extracts_quoted_name_returns_correct_tuple(self, tmp_path):
        """Test extracts correct resource name and queue name tuple."""
        from terraform_config import extract_sqs_queue_names
        (tmp_path / "locals.tf").write_text("")  # Empty locals
        sqs_file = tmp_path / "sqs.tf"
        sqs_file.write_text('''
resource "aws_sqs_queue" "my_queue" {
  name = "MyQueueName"
}
''')
        result = extract_sqs_queue_names(sqs_file)
        assert result[0] == ("my_queue", "MyQueueName")

    def test_extracts_local_reference_returns_single_result(self, tmp_path):
        """Test extracts exactly one queue when name uses local reference."""
        from terraform_config import extract_sqs_queue_names
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text('locals {\n  queue_name = "LocalQueueName"\n}\n')
        sqs_file = tmp_path / "sqs.tf"
        sqs_file.write_text('''
resource "aws_sqs_queue" "my_queue" {
  name = local.queue_name
}
''')
        result = extract_sqs_queue_names(sqs_file)
        assert len(result) == 1

    def test_extracts_local_reference_returns_correct_tuple(self, tmp_path):
        """Test extracts correct tuple when name uses local reference."""
        from terraform_config import extract_sqs_queue_names
        locals_file = tmp_path / "locals.tf"
        locals_file.write_text('locals {\n  queue_name = "LocalQueueName"\n}\n')
        sqs_file = tmp_path / "sqs.tf"
        sqs_file.write_text('''
resource "aws_sqs_queue" "my_queue" {
  name = local.queue_name
}
''')
        result = extract_sqs_queue_names(sqs_file)
        assert result[0] == ("my_queue", "LocalQueueName")


class TestResolveLocalInterpolationsMaxIterations:
    """Tests for max iterations edge case in _resolve_local_interpolations."""

    def test_handles_circular_reference_without_infinite_loop(self):
        """Test handles circular reference by stopping at max iterations."""
        # Create a circular reference that never resolves
        value = "${local.a}"
        local_values = {
            "a": "${local.b}",
            "b": "${local.a}",  # Circular!
        }
        # Should not hang - returns after max iterations
        result = _resolve_local_interpolations(value, local_values)
        # Result will alternate but won't be fully resolved
        assert result in ["${local.a}", "${local.b}"]

    def test_handles_deep_nesting_beyond_resolution(self):
        """Test handles nesting deeper than max iterations."""
        # Create nesting that requires > 10 iterations
        value = "${local.level0}"
        local_values = {f"level{i}": f"${{local.level{i+1}}}" for i in range(15)}
        local_values["level15"] = "final"

        result = _resolve_local_interpolations(value, local_values)
        # Should stop before fully resolving due to max iterations
        assert "${local." in result or result == "final"


class TestGetTfvarsValuesAdditional:
    """Additional tests for get_tfvars_values function."""

    def test_parses_string_values(self, tmp_path):
        """Test parses string values from tfvars file."""
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('region = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("region") == "us-east-1"

    def test_parses_list_values(self, tmp_path):
        """Test parses list values from tfvars file."""
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('tags = ["tag1", "tag2"]\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("tags") == ["tag1", "tag2"]

    def test_skips_comments_and_empty_lines(self, tmp_path):
        """Test skips comments and empty lines."""
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('# comment\n\nregion = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        assert result.get("region") == "us-east-1"

    def test_skips_non_matching_lines(self, tmp_path):
        """Test skips lines that don't match string or list patterns."""
        tfvars_file = tmp_path / "terraform.tfvars"
        tfvars_file.write_text('some_number = 42\nregion = "us-east-1"\n')

        result = get_tfvars_values(tmp_path)
        # Number assignment doesn't match, but string does
        assert "some_number" not in result
        assert result.get("region") == "us-east-1"

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        """Test returns empty dict when tfvars file doesn't exist."""
        result = get_tfvars_values(tmp_path)
        assert result == {}


class TestGetSharedConfigDomainName:
    """Tests for domain_name handling in get_shared_config."""

    @patch('terraform_config.parse_locals')
    @patch('terraform_config.parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_sets_api_fqdn_when_domain_name_present(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        """Test sets api_fqdn when domain_name is present."""
        mock_locals.return_value = {"domain_name": "example.com"}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert result.get("api_fqdn") == "api.example.com"

    @patch('terraform_config.parse_locals')
    @patch('terraform_config.parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_empty(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        """Test does not set api_fqdn when domain_name is empty."""
        mock_locals.return_value = {"domain_name": ""}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result

    @patch('terraform_config.parse_locals')
    @patch('terraform_config.parse_outputs')
    @patch('terraform_config.parse_lambda_handler_names')
    def test_no_api_fqdn_when_domain_name_missing(
        self, mock_handlers, mock_outputs, mock_locals
    ):
        """Test does not set api_fqdn when domain_name key is missing."""
        mock_locals.return_value = {}
        mock_outputs.return_value = {}
        mock_handlers.return_value = {}

        result = get_shared_config()
        assert "api_fqdn" not in result


class TestResolveLocalInterpolationsMaxIterationsExhaustion:
    """Tests for exhausting max iterations in _resolve_local_interpolations."""

    def test_exhausts_max_iterations_with_growing_pattern(self):
        """Test that loop exhausts all iterations without early break."""
        # Create a self-referencing pattern that grows with each iteration
        # Each iteration replaces ${local.a} with a longer string containing ${local.a}
        # This ensures new_value != value on every iteration, preventing early break
        value = "${local.a}"
        local_values = {"a": "x${local.a}y"}

        result = _resolve_local_interpolations(value, local_values)
        # After 10 iterations, we'll have: x^10 + ${local.a} + y^10
        # The string keeps growing but never fully resolves
        assert "${local.a}" in result
        # Verify it ran all iterations by checking the growth pattern
        assert result.count("x") == 10
        assert result.count("y") == 10


class TestGetEndpointLocalValuesMissingHandler:
    """Tests for handler_key not in handler_names branch."""

    def test_handler_key_not_in_handler_names(self, tmp_path):
        """Test that handler references not in handler_names are skipped."""
        from terraform_config import get_endpoint_local_values
        locals_file = tmp_path / "locals.tf"
        # Reference a handler that won't be in the mocked handler_names
        locals_file.write_text(
            'locals {\n  handler = module.common.lambda_handler_names.nonexistent\n}\n'
        )
        with patch("terraform_config.parse_lambda_handler_names") as mock_handlers:
            mock_handlers.return_value = {"webhook": "WebhookHandler"}  # No "nonexistent"
            with patch("terraform_config.get_resource_prefix") as mock_prefix:
                mock_prefix.return_value = "TenULabs"
                result = get_endpoint_local_values(tmp_path)
        # The "handler" key should not be in result since "nonexistent" wasn't found
        assert "handler" not in result


class TestExtractIamRoleNamesUnmatchedPattern:
    """Tests for IAM role name patterns that don't match any resolution."""

    def test_role_with_unresolvable_expression(self, tmp_path):
        """Test role with name expression that doesn't match any pattern."""
        from terraform_config import extract_iam_role_names
        iam_file = tmp_path / "iam.tf"
        # Use an expression that won't match quoted, local, or var patterns
        iam_file.write_text('''
resource "aws_iam_role" "my_role" {
  name = data.aws_caller_identity.current.account_id
  assume_role_policy = jsonencode({})
}
''')
        (tmp_path / "locals.tf").write_text("")
        (tmp_path / "terraform.tfvars").write_text("")
        result = extract_iam_role_names(iam_file)
        # Role should not be extracted since name doesn't match any pattern
        assert len(result) == 0


class TestExtractLambdaFunctionNamesUnresolvable:
    """Tests for Lambda functions with unresolvable function names."""

    def test_function_with_unresolvable_name(self, tmp_path):
        """Test Lambda function with function_name that can't be resolved."""
        from terraform_config import extract_lambda_function_names
        lambda_file = tmp_path / "lambda.tf"
        # Use an expression that doesn't match any resolution pattern
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
        # Function should not be in result since name couldn't be resolved
        assert len(result) == 0


class TestExtractSqsQueueNamesUnmatchedLocal:
    """Tests for SQS queue names with unresolvable local references."""

    def test_queue_with_local_not_in_values(self, tmp_path):
        """Test SQS queue with local reference that's not in local_values."""
        from terraform_config import extract_sqs_queue_names
        sqs_file = tmp_path / "sqs.tf"
        # Reference a local that won't be in local_values
        sqs_file.write_text('''
resource "aws_sqs_queue" "my_queue" {
  name = local.undefined_queue_name
}
''')
        # Empty locals.tf so undefined_queue_name won't be found
        (tmp_path / "locals.tf").write_text('locals {\n  other_var = "value"\n}\n')
        result = extract_sqs_queue_names(sqs_file)
        # Queue should not be in result since local reference wasn't found
        assert len(result) == 0
