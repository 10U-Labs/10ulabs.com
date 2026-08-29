import pytest

from test_fixtures.lambda_lifecycle import (
    _extract_block_content,
    _check_lambda_lifecycle_rules,
    create_lambda_lifecycle_tests,
)


LAMBDA_WITH_LIFECYCLE_TF = '''
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


class TestExtractBlockContentSimpleBlocks:
    def test_extracts_empty_block(self):
        content = "{}"
        result = _extract_block_content(content, 0)
        assert result == "{}"

    def test_extracts_block_with_single_key_value(self):
        content = "{ key = value }"
        result = _extract_block_content(content, 0)
        assert result == "{ key = value }"

    def test_extracts_block_with_whitespace(self):
        content = "{\n  key = value\n}"
        result = _extract_block_content(content, 0)
        assert result == "{\n  key = value\n}"

    def test_extracts_block_from_middle_of_content(self):
        content = "prefix { inner } suffix"
        result = _extract_block_content(content, 7)
        assert result == "{ inner }"

    def test_returns_remaining_content_when_unbalanced(self):
        content = "{ unclosed"
        result = _extract_block_content(content, 0)
        assert result == "{ unclosed"


class TestExtractBlockContentNestedBlocks:
    def test_extracts_single_nested_block(self):
        content = "{ outer { inner } }"
        result = _extract_block_content(content, 0)
        assert result == "{ outer { inner } }"

    def test_extracts_deeply_nested_blocks(self):
        content = "{ a { b { c } } }"
        result = _extract_block_content(content, 0)
        assert result == "{ a { b { c } } }"

    def test_extracts_multiple_nested_blocks_at_same_level(self):
        content = "{ first { } second { } }"
        result = _extract_block_content(content, 0)
        assert result == "{ first { } second { } }"

    def test_extracts_terraform_style_nested_blocks(self):
        content = """{
  environment {
    variables = {}
  }
  lifecycle {
    replace_triggered_by = []
  }
}"""
        result = _extract_block_content(content, 0)
        assert result == content

    def test_extracts_inner_block_when_starting_at_inner_position(self):
        content = "outer { inner { data } } end"
        result = _extract_block_content(content, 14)
        assert result == "{ data }"


class TestCheckLambdaLifecycleRulesPass:
    def test_passes_for_lambda_with_lifecycle_and_replace_triggered_by(self, tmp_path):
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(LAMBDA_WITH_LIFECYCLE_TF)
        assert _check_lambda_lifecycle_rules(tf_file) is None

    def test_passes_for_lambda_without_environment_variables(self, tmp_path):
        tf_content = '''
resource "aws_lambda_function" "simple_lambda" {
  function_name = "simple-function"
  handler       = "index.handler"
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        assert _check_lambda_lifecycle_rules(tf_file) is None

    def test_passes_for_multiple_lambdas_all_with_lifecycle(self, tmp_path):
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
        assert _check_lambda_lifecycle_rules(tf_file) is None

    def test_passes_for_empty_file(self, tmp_path):
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text("")
        assert _check_lambda_lifecycle_rules(tf_file) is None

    def test_passes_for_file_with_no_lambda_resources(self, tmp_path):
        tf_content = '''
resource "aws_s3_bucket" "my_bucket" {
  bucket = "my-bucket"
}
'''
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(tf_content)
        assert _check_lambda_lifecycle_rules(tf_file) is None


class TestCheckLambdaLifecycleRulesFail:
    def test_fails_for_lambda_with_env_vars_but_no_lifecycle(self, tmp_path):
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
            _check_lambda_lifecycle_rules(tf_file)

    def test_fails_for_lambda_with_lifecycle_but_no_replace_triggered_by(self, tmp_path):
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
            _check_lambda_lifecycle_rules(tf_file)

    def test_error_message_contains_resource_name(self, tmp_path):
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
        with pytest.raises(AssertionError, match="my_failing_lambda"):
            _check_lambda_lifecycle_rules(tf_file)

    def test_error_message_mentions_kms_grants(self, tmp_path):
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
        with pytest.raises(AssertionError, match="KMS grants"):
            _check_lambda_lifecycle_rules(tf_file)

    def test_fails_for_second_lambda_missing_lifecycle(self, tmp_path):
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
            _check_lambda_lifecycle_rules(tf_file)


def test_check_lambda_lifecycle_rules_file_not_found(tmp_path):
    missing_file = tmp_path / "nonexistent.tf"
    with pytest.raises(FileNotFoundError):
        _check_lambda_lifecycle_rules(missing_file)


class TestCreateLambdaLifecycleTestsReturnType:
    def test_returns_class_object(self, tmp_path):
        result = create_lambda_lifecycle_tests(tmp_path)
        assert isinstance(result, type)

    def test_returned_class_has_lifecycle_test_method(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert hasattr(TestClass, 'test_lambda_with_env_vars_has_lifecycle_rule')

    def test_returned_class_has_configured_test_method(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert hasattr(TestClass, 'test_terraform_files_configured')

    def test_returned_class_name_is_test_lambda_lifecycle(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        assert TestClass.__name__ == 'TestLambdaLifecycle'


class TestCreateLambdaLifecycleTestsDefaultTfFiles:
    def test_uses_lambda_tf_as_default(self, tmp_path):
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        assert instance.test_lambda_with_env_vars_has_lifecycle_rule() is None

    def test_default_creates_single_tf_path(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        assert instance.test_terraform_files_configured() is None


class TestCreateLambdaLifecycleTestsCustomTfFiles:
    def test_accepts_custom_tf_files_list(self, tmp_path):
        custom_tf = tmp_path / "custom.tf"
        custom_tf.write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["custom.tf"])
        instance = TestClass()
        assert instance.test_lambda_with_env_vars_has_lifecycle_rule() is None

    def test_accepts_multiple_tf_files(self, tmp_path):
        for name in ["first.tf", "second.tf"]:
            (tmp_path / name).write_text('resource "aws_s3_bucket" "b" {}')
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["first.tf", "second.tf"])
        instance = TestClass()
        assert instance.test_terraform_files_configured() is None


class TestCreateLambdaLifecycleTestsTestMethodBehavior:
    def test_lifecycle_test_passes_for_valid_lambda(self, tmp_path):
        tf_file = tmp_path / "lambda.tf"
        tf_file.write_text(LAMBDA_WITH_LIFECYCLE_TF)
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        assert instance.test_lambda_with_env_vars_has_lifecycle_rule() is None

    def test_lifecycle_test_fails_for_invalid_lambda(self, tmp_path):
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
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["nonexistent.tf"])
        instance = TestClass()
        assert instance.test_lambda_with_env_vars_has_lifecycle_rule() is None

    def test_configured_test_passes_with_default_config(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path)
        instance = TestClass()
        assert instance.test_terraform_files_configured() is None

    def test_configured_test_passes_with_custom_files(self, tmp_path):
        TestClass = create_lambda_lifecycle_tests(tmp_path, tf_files=["a.tf", "b.tf"])
        instance = TestClass()
        assert instance.test_terraform_files_configured() is None

    def test_checks_all_configured_tf_files(self, tmp_path):
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
