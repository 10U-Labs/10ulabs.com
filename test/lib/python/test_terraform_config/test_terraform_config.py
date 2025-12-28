"""Unit tests for terraform_config module."""
import pytest

from terraform_config import (
    _parse_map_block,
    _resolve_prefix_refs,
    _resolve_local_interpolations,
    _resolve_all_refs,
    _resolve_lambda_function_name,
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
        """Test resolves module.shared.resource_prefix."""
        value = "${module.shared.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_local_resource_prefix(self):
        """Test resolves local.resource_prefix."""
        value = "${local.resource_prefix}MyFunction"
        result = _resolve_prefix_refs(value, "TenULabs")
        assert result == "TenULabsMyFunction"

    def test_resolves_multiple_refs(self):
        """Test resolves multiple references in same string."""
        value = "${local.resource_prefix}-${module.shared.resource_prefix}"
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
        value = "${module.shared.resource_prefix}-${module.shared.lambda_handler_names.webhook}"
        handler_names = {"webhook": "TenULabsWebhook"}
        result = _resolve_all_refs(value, "TenULabs", handler_names)
        assert result == "TenULabs-TenULabsWebhook"

    def test_resolves_only_prefix_when_no_handlers(self):
        """Test resolves prefix when handler_names is empty."""
        value = "${module.shared.resource_prefix}Function"
        result = _resolve_all_refs(value, "TenULabs", {})
        assert result == "TenULabsFunction"

    def test_returns_unchanged_when_handler_not_found(self):
        """Test returns partial resolution when handler not in dict."""
        value = "${module.shared.lambda_handler_names.missing}"
        result = _resolve_all_refs(value, "TenULabs", {"webhook": "Handler"})
        assert result == "${module.shared.lambda_handler_names.missing}"


class TestResolveLambdaFunctionName:
    """Tests for _resolve_lambda_function_name function."""

    def test_resolves_quoted_string(self):
        """Test resolves function_name from quoted string."""
        block = '''
        function_name = "${module.shared.resource_prefix}MyFunction"
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
        """Test resolves function_name from module.shared.lambda_handler_names."""
        block = '''
        function_name = module.shared.lambda_handler_names.webhook
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
