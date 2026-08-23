"""Comprehensive tests for naming_conventions module."""

from naming_conventions import (
    validate_name,
    validate_kebab_name,
)


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


# === validate_kebab_name Function ===


class TestValidateKebabName:
    """Tests for validate_kebab_name function."""

    def test_valid_name_returns_none(self):
        """validate_kebab_name returns None for valid names."""
        assert validate_kebab_name("TenULabs-my-resource") is None

    def test_valid_name_multiple_words_returns_none(self):
        """validate_kebab_name returns None for multiple words."""
        assert validate_kebab_name("TenULabs-rack-configurations-backup") is None

    def test_empty_name_returns_error(self):
        """validate_kebab_name returns error for empty name."""
        result = validate_kebab_name("")
        assert result == "Name is empty"

    def test_no_hyphen_returns_error(self):
        """validate_kebab_name returns error when no hyphen."""
        result = validate_kebab_name("TenULabsResource")
        assert "must contain hyphens" in result

    def test_lowercase_prefix_returns_error(self):
        """validate_kebab_name returns error for lowercase prefix."""
        result = validate_kebab_name("tenulabs-resource")
        assert "prefix must be PascalCase" in result

    def test_non_alphanumeric_prefix_returns_error(self):
        """validate_kebab_name returns error for non-alphanumeric prefix."""
        result = validate_kebab_name("Ten-U-resource")
        assert "suffix must be lowercase" in result

    def test_uppercase_suffix_returns_error(self):
        """validate_kebab_name returns error for uppercase in suffix."""
        result = validate_kebab_name("TenULabs-MyResource")
        assert "suffix must be lowercase" in result

    def test_empty_suffix_returns_error(self):
        """validate_kebab_name returns error for empty suffix."""
        result = validate_kebab_name("TenULabs-")
        assert "suffix must be lowercase" in result

    def test_special_chars_in_suffix_returns_error(self):
        """validate_kebab_name returns error for special chars in suffix."""
        result = validate_kebab_name("TenULabs-resource_name")
        assert "suffix must be lowercase" in result

    def test_empty_prefix_returns_error(self):
        """validate_kebab_name returns error for empty prefix."""
        result = validate_kebab_name("-resource")
        assert "prefix must be PascalCase" in result
