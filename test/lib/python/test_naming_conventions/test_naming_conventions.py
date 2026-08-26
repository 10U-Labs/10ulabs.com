from naming_conventions import (
    validate_name,
    validate_kebab_name,
)


class TestValidateName:
    def test_valid_name_returns_none(self):
        assert validate_name("TenULabsMyFunction") is None

    def test_empty_name_returns_error(self):
        result = validate_name("")
        assert result == "Name is empty"

    def test_lowercase_start_returns_error(self):
        result = validate_name("myFunction")
        assert "must start with uppercase" in result

    def test_dash_error_contains_dash_message(self):
        result = validate_name("My-Function")
        assert "contains dash" in result

    def test_dash_error_mentions_pascalcase(self):
        result = validate_name("My-Function")
        assert "PascalCase" in result

    def test_underscore_error_contains_underscore_message(self):
        result = validate_name("My_Function")
        assert "contains underscore" in result

    def test_underscore_error_mentions_pascalcase(self):
        result = validate_name("My_Function")
        assert "PascalCase" in result

    def test_space_error_contains_space_message(self):
        result = validate_name("My Function")
        assert "contains space" in result

    def test_space_error_mentions_pascalcase(self):
        result = validate_name("My Function")
        assert "PascalCase" in result

    def test_non_alphanumeric_returns_error(self):
        result = validate_name("My@Function")
        assert "non-alphanumeric" in result

    def test_error_priority_lowercase_over_special_chars(self):
        result = validate_name("my-function")
        assert "must start with uppercase" in result


class TestValidateKebabName:
    def test_valid_name_returns_none(self):
        assert validate_kebab_name("TenULabs-my-resource") is None

    def test_valid_name_multiple_words_returns_none(self):
        assert validate_kebab_name("TenULabs-rack-configurations-backup") is None

    def test_empty_name_returns_error(self):
        result = validate_kebab_name("")
        assert result == "Name is empty"

    def test_no_hyphen_returns_error(self):
        result = validate_kebab_name("TenULabsResource")
        assert "must contain hyphens" in result

    def test_lowercase_prefix_returns_error(self):
        result = validate_kebab_name("tenulabs-resource")
        assert "prefix must be PascalCase" in result

    def test_non_alphanumeric_prefix_returns_error(self):
        result = validate_kebab_name("Ten-U-resource")
        assert "suffix must be lowercase" in result

    def test_uppercase_suffix_returns_error(self):
        result = validate_kebab_name("TenULabs-MyResource")
        assert "suffix must be lowercase" in result

    def test_empty_suffix_returns_error(self):
        result = validate_kebab_name("TenULabs-")
        assert "suffix must be lowercase" in result

    def test_special_chars_in_suffix_returns_error(self):
        result = validate_kebab_name("TenULabs-resource_name")
        assert "suffix must be lowercase" in result

    def test_empty_prefix_returns_error(self):
        result = validate_kebab_name("-resource")
        assert "prefix must be PascalCase" in result
