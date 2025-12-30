"""Comprehensive tests for naming_conventions module."""
import pytest

from naming_conventions import (
    is_pascalcase,
    validate_name,
    find_violations,
    extract_iam_role_names_from_terraform,
    extract_lambda_function_names_from_terraform,
    resolve_terraform_interpolation,
)


# === is_pascalcase Function ===


class TestIsPascalcase:
    """Tests for is_pascalcase function."""

    def test_valid_pascalcase_simple(self):
        """is_pascalcase returns True for simple PascalCase."""
        assert is_pascalcase("MyFunction") is True

    def test_valid_pascalcase_with_numbers(self):
        """is_pascalcase returns True for PascalCase with numbers."""
        assert is_pascalcase("TenULabs123") is True

    def test_valid_pascalcase_single_word(self):
        """is_pascalcase returns True for single capitalized word."""
        assert is_pascalcase("Function") is True

    def test_valid_pascalcase_all_caps(self):
        """is_pascalcase returns True for all caps (still valid PascalCase)."""
        assert is_pascalcase("API") is True

    def test_invalid_empty_string(self):
        """is_pascalcase returns False for empty string."""
        assert is_pascalcase("") is False

    def test_invalid_lowercase_start(self):
        """is_pascalcase returns False when starting with lowercase."""
        assert is_pascalcase("myFunction") is False

    def test_invalid_with_dash(self):
        """is_pascalcase returns False for names with dashes."""
        assert is_pascalcase("My-Function") is False

    def test_invalid_with_underscore(self):
        """is_pascalcase returns False for names with underscores."""
        assert is_pascalcase("My_Function") is False

    def test_invalid_with_space(self):
        """is_pascalcase returns False for names with spaces."""
        assert is_pascalcase("My Function") is False

    def test_invalid_number_start(self):
        """is_pascalcase returns False when starting with number."""
        assert is_pascalcase("123Function") is False


# === validate_name Function ===


class TestValidateName:
    """Tests for validate_name function."""

    def test_valid_name_returns_none(self):
        """validate_name returns None for valid names."""
        assert validate_name("TenULabsMyFunction") is None

    def test_empty_name_returns_error(self):
        """validate_name returns error for empty name."""
        result = validate_name("")
        assert result == "Name is empty"

    def test_lowercase_start_returns_error(self):
        """validate_name returns error for lowercase start."""
        result = validate_name("myFunction")
        assert "must start with uppercase" in result

    def test_dash_error_contains_dash_message(self):
        """validate_name error for dashes contains 'contains dash'."""
        result = validate_name("My-Function")
        assert "contains dash" in result

    def test_dash_error_mentions_pascalcase(self):
        """validate_name error for dashes mentions PascalCase."""
        result = validate_name("My-Function")
        assert "PascalCase" in result

    def test_underscore_error_contains_underscore_message(self):
        """validate_name error for underscores contains 'contains underscore'."""
        result = validate_name("My_Function")
        assert "contains underscore" in result

    def test_underscore_error_mentions_pascalcase(self):
        """validate_name error for underscores mentions PascalCase."""
        result = validate_name("My_Function")
        assert "PascalCase" in result

    def test_space_error_contains_space_message(self):
        """validate_name error for spaces contains 'contains space'."""
        result = validate_name("My Function")
        assert "contains space" in result

    def test_space_error_mentions_pascalcase(self):
        """validate_name error for spaces mentions PascalCase."""
        result = validate_name("My Function")
        assert "PascalCase" in result

    def test_non_alphanumeric_returns_error(self):
        """validate_name returns error for non-alphanumeric chars."""
        result = validate_name("My@Function")
        assert "non-alphanumeric" in result

    def test_error_priority_lowercase_over_special_chars(self):
        """validate_name checks lowercase start first."""
        result = validate_name("my-function")
        assert "must start with uppercase" in result


# === find_violations Function ===


class TestFindViolations:
    """Tests for find_violations function."""

    def test_no_violations_returns_empty(self):
        """find_violations returns empty list when all valid."""
        result = find_violations(["ValidName", "AnotherValid"])
        assert result == []

    def test_single_violation_returns_one_item(self):
        """find_violations returns list with one item for single violation."""
        result = find_violations(["ValidName", "Invalid-Name"])
        assert len(result) == 1

    def test_single_violation_contains_invalid_name(self):
        """find_violations result contains the invalid name."""
        result = find_violations(["ValidName", "Invalid-Name"])
        assert result[0][0] == "Invalid-Name"

    def test_single_violation_error_mentions_dash(self):
        """find_violations result error message mentions dash."""
        result = find_violations(["ValidName", "Invalid-Name"])
        assert "contains dash" in result[0][1]

    def test_multiple_violations_returns_correct_count(self):
        """find_violations returns correct count for multiple violations."""
        result = find_violations(["bad-name", "also_bad", "GoodName"])
        assert len(result) == 2

    def test_multiple_violations_includes_dash_name(self):
        """find_violations result includes name with dash."""
        result = find_violations(["bad-name", "also_bad", "GoodName"])
        names = [v[0] for v in result]
        assert "bad-name" in names

    def test_multiple_violations_includes_underscore_name(self):
        """find_violations result includes name with underscore."""
        result = find_violations(["bad-name", "also_bad", "GoodName"])
        names = [v[0] for v in result]
        assert "also_bad" in names

    def test_empty_list_returns_empty(self):
        """find_violations returns empty list for empty input."""
        result = find_violations([])
        assert result == []


# === extract_iam_role_names_from_terraform Function ===


class TestExtractIamRoleNamesFromTerraform:
    """Tests for extract_iam_role_names_from_terraform function."""

    def test_extracts_simple_role_returns_one_item(self):
        """extract_iam_role_names_from_terraform returns one item for simple role."""
        content = '''
resource "aws_iam_role" "my_role" {
  name = "TenULabsMyRole"
  assume_role_policy = "{}"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert len(result) == 1

    def test_extracts_simple_role_correct_tuple(self):
        """extract_iam_role_names_from_terraform extracts correct role tuple."""
        content = '''
resource "aws_iam_role" "my_role" {
  name = "TenULabsMyRole"
  assume_role_policy = "{}"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert result[0] == ("my_role", "TenULabsMyRole")

    def test_extracts_multiple_roles_returns_correct_count(self):
        """extract_iam_role_names_from_terraform returns correct count."""
        content = '''
resource "aws_iam_role" "role_one" {
  name = "RoleOne"
}

resource "aws_iam_role" "role_two" {
  name = "RoleTwo"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert len(result) == 2

    def test_extracts_multiple_roles_includes_role_one(self):
        """extract_iam_role_names_from_terraform includes first role."""
        content = '''
resource "aws_iam_role" "role_one" {
  name = "RoleOne"
}

resource "aws_iam_role" "role_two" {
  name = "RoleTwo"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert ("role_one", "RoleOne") in result

    def test_extracts_multiple_roles_includes_role_two(self):
        """extract_iam_role_names_from_terraform includes second role."""
        content = '''
resource "aws_iam_role" "role_one" {
  name = "RoleOne"
}

resource "aws_iam_role" "role_two" {
  name = "RoleTwo"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert ("role_two", "RoleTwo") in result

    def test_no_roles_returns_empty(self):
        """extract_iam_role_names_from_terraform returns empty for no roles."""
        content = '''
resource "aws_lambda_function" "my_func" {
  function_name = "MyFunction"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert result == []

    def test_empty_content_returns_empty(self):
        """extract_iam_role_names_from_terraform returns empty for empty content."""
        result = extract_iam_role_names_from_terraform("")
        assert result == []

    def test_role_without_name_returns_empty(self):
        """extract_iam_role_names_from_terraform skips roles without name attribute."""
        content = '''
resource "aws_iam_role" "my_role" {
  assume_role_policy = "{}"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert result == []

    def test_handles_interpolation_returns_one_item(self):
        """extract_iam_role_names_from_terraform returns one item for interpolated name."""
        content = '''
resource "aws_iam_role" "my_role" {
  name = "${local.resource_prefix}MyRole"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert len(result) == 1

    def test_handles_interpolation_preserves_interpolation_syntax(self):
        """extract_iam_role_names_from_terraform preserves interpolation syntax."""
        content = '''
resource "aws_iam_role" "my_role" {
  name = "${local.resource_prefix}MyRole"
}
'''
        result = extract_iam_role_names_from_terraform(content)
        assert result[0] == ("my_role", "${local.resource_prefix}MyRole")


# === extract_lambda_function_names_from_terraform Function ===


class TestExtractLambdaFunctionNamesFromTerraform:
    """Tests for extract_lambda_function_names_from_terraform function."""

    def test_extracts_simple_function_returns_one_item(self):
        """extract_lambda_function_names_from_terraform returns one item."""
        content = '''
resource "aws_lambda_function" "my_func" {
  function_name = "TenULabsMyFunction"
  handler       = "index.handler"
  runtime       = "python3.11"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert len(result) == 1

    def test_extracts_simple_function_correct_tuple(self):
        """extract_lambda_function_names_from_terraform extracts correct tuple."""
        content = '''
resource "aws_lambda_function" "my_func" {
  function_name = "TenULabsMyFunction"
  handler       = "index.handler"
  runtime       = "python3.11"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert result[0] == ("my_func", "TenULabsMyFunction")

    def test_extracts_multiple_functions_returns_correct_count(self):
        """extract_lambda_function_names_from_terraform returns correct count."""
        content = '''
resource "aws_lambda_function" "func_one" {
  function_name = "FuncOne"
}

resource "aws_lambda_function" "func_two" {
  function_name = "FuncTwo"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert len(result) == 2

    def test_extracts_multiple_functions_includes_func_one(self):
        """extract_lambda_function_names_from_terraform includes first function."""
        content = '''
resource "aws_lambda_function" "func_one" {
  function_name = "FuncOne"
}

resource "aws_lambda_function" "func_two" {
  function_name = "FuncTwo"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert ("func_one", "FuncOne") in result

    def test_extracts_multiple_functions_includes_func_two(self):
        """extract_lambda_function_names_from_terraform includes second function."""
        content = '''
resource "aws_lambda_function" "func_one" {
  function_name = "FuncOne"
}

resource "aws_lambda_function" "func_two" {
  function_name = "FuncTwo"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert ("func_two", "FuncTwo") in result

    def test_skips_variable_references(self):
        """extract_lambda_function_names_from_terraform skips var references."""
        content = '''
resource "aws_lambda_function" "my_func" {
  function_name = var.function_name
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert result == []

    def test_no_functions_returns_empty(self):
        """extract_lambda_function_names_from_terraform returns empty for none."""
        content = '''
resource "aws_iam_role" "my_role" {
  name = "MyRole"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert result == []

    def test_empty_content_returns_empty(self):
        """extract_lambda_function_names_from_terraform returns empty for empty content."""
        result = extract_lambda_function_names_from_terraform("")
        assert result == []

    def test_function_without_name_returns_empty(self):
        """extract_lambda_function_names_from_terraform skips functions without name."""
        content = '''
resource "aws_lambda_function" "my_func" {
  runtime = "python3.11"
  handler = "index.handler"
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert result == []

    def test_handles_unquoted_name(self):
        """extract_lambda_function_names_from_terraform handles unquoted names."""
        content = '''
resource "aws_lambda_function" "my_func" {
  function_name = local.function_name
}
'''
        result = extract_lambda_function_names_from_terraform(content)
        assert len(result) == 1


# === resolve_terraform_interpolation Function ===


class TestResolveTerraformInterpolation:
    """Tests for resolve_terraform_interpolation function."""

    def test_resolves_braced_interpolation(self):
        """resolve_terraform_interpolation resolves ${local.resource_prefix}."""
        result = resolve_terraform_interpolation(
            "${local.resource_prefix}MyFunction",
            {},
            resource_prefix="TenULabs",
        )
        assert result == "TenULabsMyFunction"

    def test_resolves_unbraced_interpolation(self):
        """resolve_terraform_interpolation resolves local.resource_prefix."""
        result = resolve_terraform_interpolation(
            "local.resource_prefixMyFunction",
            {},
            resource_prefix="TenULabs",
        )
        assert result == "TenULabsMyFunction"

    def test_uses_locals_dict_prefix(self):
        """resolve_terraform_interpolation uses prefix from locals dict."""
        result = resolve_terraform_interpolation(
            "${local.resource_prefix}MyFunction",
            {"resource_prefix": "CustomPrefix"},
            resource_prefix="TenULabs",
        )
        assert result == "CustomPrefixMyFunction"

    def test_no_interpolation_unchanged(self):
        """resolve_terraform_interpolation returns unchanged if no interpolation."""
        result = resolve_terraform_interpolation(
            "TenULabsMyFunction",
            {},
            resource_prefix="TenULabs",
        )
        assert result == "TenULabsMyFunction"

    def test_multiple_interpolations(self):
        """resolve_terraform_interpolation resolves multiple occurrences."""
        result = resolve_terraform_interpolation(
            "${local.resource_prefix}Func${local.resource_prefix}",
            {},
            resource_prefix="TenU",
        )
        assert result == "TenUFuncTenU"

    def test_preserves_separator_characters(self):
        """resolve_terraform_interpolation preserves separators."""
        result = resolve_terraform_interpolation(
            "${local.resource_prefix}-my-function",
            {},
            resource_prefix="TenULabs",
        )
        assert result == "TenULabs-my-function"
