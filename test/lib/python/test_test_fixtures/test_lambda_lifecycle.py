"""Unit tests for test_fixtures.lambda_lifecycle module."""
from pathlib import Path

import pytest

from test_fixtures.lambda_lifecycle import (
    extract_block_content,
    check_lambda_lifecycle_rules,
    create_lambda_lifecycle_tests,
)


class TestExtractBlockContentSimpleBlocks:
    """Tests for extract_block_content with simple blocks."""

    def test_extracts_empty_block(self):
        """Test that empty block is extracted correctly."""
        content = "{}"
        result = extract_block_content(content, 0)
        assert result == "{}"

    def test_extracts_block_with_single_key_value(self):
        """Test that block with single key-value is extracted."""
        content = "{ key = value }"
        result = extract_block_content(content, 0)
        assert result == "{ key = value }"

    def test_extracts_block_with_whitespace(self):
        """Test that block with whitespace is extracted."""
        content = "{\n  key = value\n}"
        result = extract_block_content(content, 0)
        assert result == "{\n  key = value\n}"

    def test_extracts_block_from_middle_of_content(self):
        """Test that block starting at non-zero position is extracted."""
        content = "prefix { inner } suffix"
        result = extract_block_content(content, 7)
        assert result == "{ inner }"

    def test_returns_remaining_content_when_unbalanced(self):
        """Test that unbalanced braces return remaining content."""
        content = "{ unclosed"
        result = extract_block_content(content, 0)
        assert result == "{ unclosed"


class TestExtractBlockContentNestedBlocks:
    """Tests for extract_block_content with nested blocks."""

    def test_extracts_single_nested_block(self):
        """Test that single nested block is extracted correctly."""
        content = "{ outer { inner } }"
        result = extract_block_content(content, 0)
        assert result == "{ outer { inner } }"

    def test_extracts_deeply_nested_blocks(self):
        """Test that deeply nested blocks are extracted."""
        content = "{ a { b { c } } }"
        result = extract_block_content(content, 0)
        assert result == "{ a { b { c } } }"

    def test_extracts_multiple_nested_blocks_at_same_level(self):
        """Test that multiple nested blocks at same level are extracted."""
        content = "{ first { } second { } }"
        result = extract_block_content(content, 0)
        assert result == "{ first { } second { } }"

    def test_extracts_terraform_style_nested_blocks(self):
        """Test extraction of Terraform-style nested blocks."""
        content = """{
  environment {
    variables = {}
  }
  lifecycle {
    replace_triggered_by = []
  }
}"""
        result = extract_block_content(content, 0)
        assert result == content

    def test_extracts_inner_block_when_starting_at_inner_position(self):
        """Test that starting at inner block position extracts inner block."""
        content = "outer { inner { data } } end"
        result = extract_block_content(content, 14)
        assert result == "{ data }"


class TestCheckLambdaLifecycleRulesPass:
    """Tests for check_lambda_lifecycle_rules when Lambda has proper lifecycle rules."""

    def test_passes_for_lambda_with_lifecycle_and_replace_triggered_by(self, tmp_path):
        """Test that Lambda with lifecycle and replace_triggered_by passes."""
        tf_content = '''
resource "aws_lambda_function" "my_lambda" {
  function_name = "my-function"
  environment {
    variables = { KEY = "value" }
  }
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_role.id]
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        check_lambda_lifecycle_rules(tf_file)

    def test_passes_for_lambda_without_environment_variables(self, tmp_path):
        """Test that Lambda without environment variables passes."""
        tf_content = '''
resource "aws_lambda_function" "simple_lambda" {
  function_name = "simple-function"
  handler       = "index.handler"
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        check_lambda_lifecycle_rules(tf_file)

    def test_passes_for_multiple_lambdas_all_with_lifecycle(self, tmp_path):
        """Test that multiple Lambdas with proper lifecycle rules pass."""
        tf_content = '''
resource "aws_lambda_function" "lambda_one" {
  function_name = "lambda-one"
  environment {
    variables = { KEY = "value" }
  }
  lifecycle {
    replace_triggered_by = [aws_iam_role.role_one.id]
  }
}

resource "aws_lambda_function" "lambda_two" {
  function_name = "lambda-two"
  environment {
    variables = { OTHER = "data" }
  }
  lifecycle {
    replace_triggered_by = [aws_iam_role.role_two.id]
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        check_lambda_lifecycle_rules(tf_file)

    def test_passes_for_empty_file(self, tmp_path):
        """Test that empty terraform file passes."""
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text("")
        check_lambda_lifecycle_rules(tf_file)

    def test_passes_for_file_with_no_lambda_resources(self, tmp_path):
        """Test that file with no Lambda resources passes."""
        tf_content = '''
resource "aws_s3_bucket" "my_bucket" {
  bucket = "my-bucket"
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        check_lambda_lifecycle_rules(tf_file)


class TestCheckLambdaLifecycleRulesFail:
    """Tests for check_lambda_lifecycle_rules when Lambda is missing lifecycle rules."""

    def test_fails_for_lambda_with_env_vars_but_no_lifecycle(self, tmp_path):
        """Test that Lambda with env vars but no lifecycle fails."""
        tf_content = '''
resource "aws_lambda_function" "missing_lifecycle" {
  function_name = "missing-lifecycle"
  environment {
    variables = { KEY = "value" }
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        with pytest.raises(AssertionError):
            check_lambda_lifecycle_rules(tf_file)

    def test_fails_for_lambda_with_lifecycle_but_no_replace_triggered_by(self, tmp_path):
        """Test that Lambda with lifecycle but no replace_triggered_by fails."""
        tf_content = '''
resource "aws_lambda_function" "incomplete_lifecycle" {
  function_name = "incomplete"
  environment {
    variables = { KEY = "value" }
  }
  lifecycle {
    create_before_destroy = true
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        with pytest.raises(AssertionError):
            check_lambda_lifecycle_rules(tf_file)

    def test_error_message_contains_resource_name(self, tmp_path):
        """Test that error message contains the resource name."""
        tf_content = '''
resource "aws_lambda_function" "my_failing_lambda" {
  function_name = "failing"
  environment {
    variables = { KEY = "value" }
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        with pytest.raises(AssertionError) as exc_info:
            check_lambda_lifecycle_rules(tf_file)
        assert "my_failing_lambda" in str(exc_info.value)

    def test_error_message_mentions_kms_grants(self, tmp_path):
        """Test that error message mentions KMS grants issue."""
        tf_content = '''
resource "aws_lambda_function" "bad_lambda" {
  function_name = "bad"
  environment {
    variables = { KEY = "value" }
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        with pytest.raises(AssertionError) as exc_info:
            check_lambda_lifecycle_rules(tf_file)
        assert "KMS grants" in str(exc_info.value)

    def test_fails_for_second_lambda_missing_lifecycle(self, tmp_path):
        """Test that second Lambda missing lifecycle fails even if first is correct."""
        tf_content = '''
resource "aws_lambda_function" "good_lambda" {
  function_name = "good"
  environment {
    variables = { KEY = "value" }
  }
  lifecycle {
    replace_triggered_by = [aws_iam_role.role.id]
  }
}

resource "aws_lambda_function" "bad_lambda" {
  function_name = "bad"
  environment {
    variables = { OTHER = "data" }
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        with pytest.raises(AssertionError):
            check_lambda_lifecycle_rules(tf_file)


class TestCheckLambdaLifecycleRulesFileNotFound:
    """Tests for check_lambda_lifecycle_rules when file doesn't exist."""

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.tf"
        with pytest.raises(FileNotFoundError):
            check_lambda_lifecycle_rules(missing_file)


class TestCreateLambdaLifecycleTestsReturnType:
    """Tests for create_lambda_lifecycle_tests return type."""

    def test_returns_class_object(self, tmp_path):
        """Test that factory returns a class object."""
        result = create_lambda_lifecycle_tests(tmp_path)
        assert isinstance(result, type)

    def test_returned_class_has_lifecycle_test_method(self, tmp_path):
        """Test that returned class has test_lambda_with_env_vars_has_lifecycle_rule method."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert hasattr(TestClass, 'test_lambda_with_env_vars_has_lifecycle_rule')

    def test_returned_class_has_configured_test_method(self, tmp_path):
        """Test that returned class has test_terraform_files_configured method."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert hasattr(TestClass, 'test_terraform_files_configured')

    def test_returned_class_name_is_test_lambda_lifecycle(self, tmp_path):
        """Test that returned class is named TestLambdaLifecycle."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert TestClass.__name__ == 'TestLambdaLifecycle'

    def test_returned_class_has_docstring(self, tmp_path):
        """Test that returned class has a docstring."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert TestClass.__doc__ is not None


class TestCreateLambdaLifecycleTestsDefaultTfFiles:
    """Tests for create_lambda_lifecycle_tests with default tf_files."""

    def test_uses_lambda_tf_as_default(self, tmp_path):
        """Test that lambda.tf is used by default when tf_files is None."""
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        instance.test_lambda_with_env_vars_has_lifecycle_rule()

    def test_default_creates_single_tf_path(self, tmp_path):
        """Test that default tf_files creates single path."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        instance.test_terraform_files_configured()


class TestCreateLambdaLifecycleTestsCustomTfFiles:
    """Tests for create_lambda_lifecycle_tests with custom tf_files."""

    def test_accepts_custom_tf_files_list(self, tmp_path):
        """Test that custom tf_files list is accepted."""
        custom_tf = tmp_path / "custom.tf"
        custom_tf.write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["custom.tf"])
        instance = TestClass()
        instance.test_lambda_with_env_vars_has_lifecycle_rule()

    def test_accepts_multiple_tf_files(self, tmp_path):
        """Test that multiple tf_files are accepted."""
        for name in ["first.tf", "second.tf"]:
            (tmp_path / name).write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["first.tf", "second.tf"])
        instance = TestClass()
        instance.test_terraform_files_configured()


class TestCreateLambdaLifecycleTestsTestMethodBehavior:
    """Tests for behavior of methods in the created test class."""

    def test_lifecycle_test_passes_for_valid_lambda(self, tmp_path):
        """Test that lifecycle test passes for valid Lambda configuration."""
        tf_content = '''
resource "aws_lambda_function" "my_lambda" {
  function_name = "my-function"
  environment {
    variables = { KEY = "value" }
  }
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_role.id]
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        instance.test_lambda_with_env_vars_has_lifecycle_rule()

    def test_lifecycle_test_fails_for_invalid_lambda(self, tmp_path):
        """Test that lifecycle test fails for Lambda missing lifecycle rule."""
        tf_content = '''
resource "aws_lambda_function" "my_lambda" {
  function_name = "my-function"
  environment {
    variables = { KEY = "value" }
  }
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_lambda_with_env_vars_has_lifecycle_rule()

    def test_lifecycle_test_skips_nonexistent_files(self, tmp_path):
        """Test that lifecycle test skips files that don't exist."""
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["nonexistent.tf"])
        instance = TestClass()
        instance.test_lambda_with_env_vars_has_lifecycle_rule()

    def test_configured_test_passes_with_default_config(self, tmp_path):
        """Test that terraform_files_configured test passes with default config."""
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        instance.test_terraform_files_configured()

    def test_configured_test_passes_with_custom_files(self, tmp_path):
        """Test that terraform_files_configured test passes with custom files."""
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["a.tf", "b.tf"])
        instance = TestClass()
        instance.test_terraform_files_configured()

    def test_checks_all_configured_tf_files(self, tmp_path):
        """Test that all configured tf files are checked."""
        good_tf = '''
resource "aws_lambda_function" "good" {
  function_name = "good"
  environment { variables = { K = "v" } }
  lifecycle { replace_triggered_by = [aws_iam_role.r.id] }
}
'''
        bad_tf = '''
resource "aws_lambda_function" "bad" {
  function_name = "bad"
  environment { variables = { K = "v" } }
}
'''
        (tmp_path / "good.tf").write_text(good_tf)
        (tmp_path / "bad.tf").write_text(bad_tf)
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["good.tf", "bad.tf"])
        instance = TestClass()
        with pytest.raises(AssertionError):
            instance.test_lambda_with_env_vars_has_lifecycle_rule()
