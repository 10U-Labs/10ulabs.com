"""Tests for test_standards_checker hook."""


def test_is_test_file_returns_true_for_test_prefix(test_standards_checker):
    """Test that Is file returns true for prefix."""
    test_prefix_file_is_test = test_standards_checker.is_test_file('test_main.py')
    assert test_prefix_file_is_test


def test_is_test_file_returns_true_for_test_suffix(test_standards_checker):
    """Test that Is file returns true for suffix."""
    test_suffix_file_is_test = test_standards_checker.is_test_file('main_test.py')
    assert test_suffix_file_is_test


def test_is_test_file_returns_true_for_spec_ts(test_standards_checker):
    """Test that Is file returns true for spec ts."""
    spec_ts_file_is_test = test_standards_checker.is_test_file('main.spec.ts')
    assert spec_ts_file_is_test


def test_is_test_file_returns_true_for_test_ts(test_standards_checker):
    """Test that Is file returns true for ts."""
    test_ts_file_is_test = test_standards_checker.is_test_file('main.test.ts')
    assert test_ts_file_is_test


def test_is_test_file_returns_true_for_spec_js(test_standards_checker):
    """Test that Is file returns true for spec js."""
    spec_js_file_is_test = test_standards_checker.is_test_file('main.spec.js')
    assert spec_js_file_is_test


def test_is_test_file_returns_false_for_regular_py(test_standards_checker):
    """Test that Is file returns false for regular py."""
    regular_py_file_is_not_test = not test_standards_checker.is_test_file('main.py')
    assert regular_py_file_is_not_test


def test_is_test_file_returns_false_for_regular_ts(test_standards_checker):
    """Test that Is file returns false for regular ts."""
    regular_ts_file_is_not_test = not test_standards_checker.is_test_file('main.ts')
    assert regular_ts_file_is_not_test


def test_check_python_tests_detects_multiple_asserts(test_standards_checker):
    """Test that Check python tests detects multiple asserts."""
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_python_tests(content)
    multiple_asserts_is_detected = len(violations) > 0
    assert multiple_asserts_is_detected


def test_check_python_tests_allows_single_assert(test_standards_checker):
    """Test that Check python tests allows single assert."""
    content = '''
def test_example():
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(content)
    single_assert_is_allowed = len(violations) == 0
    assert single_assert_is_allowed


def test_check_python_tests_detects_invalid_variable_name(test_standards_checker):
    """Test that Check python tests detects invalid variable name."""
    content = '''
def test_example():
    x = True
    assert x
'''
    violations = test_standards_checker.check_python_tests(content)
    invalid_variable_name_is_detected = len(violations) > 0
    assert invalid_variable_name_is_detected


def test_check_python_tests_allows_valid_variable_name_with_verb(test_standards_checker):
    """Test that Check python tests allows valid variable name with verb."""
    content = '''
def test_example():
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(content)
    valid_variable_name_with_verb_is_allowed = len(violations) == 0
    assert valid_variable_name_with_verb_is_allowed


def test_check_python_tests_allows_variable_name_with_exists(test_standards_checker):
    """Test that Check python tests allows variable name with exists."""
    content = '''
def test_example():
    file_exists = True
    assert file_exists
'''
    violations = test_standards_checker.check_python_tests(content)
    variable_name_with_exists_is_allowed = len(violations) == 0
    assert variable_name_with_exists_is_allowed


def test_check_python_tests_allows_variable_name_with_contains(test_standards_checker):
    """Test that Check python tests allows variable name with contains."""
    content = '''
def test_example():
    list_contains_item = True
    assert list_contains_item
'''
    violations = test_standards_checker.check_python_tests(content)
    variable_name_with_contains_is_allowed = len(violations) == 0
    assert variable_name_with_contains_is_allowed


def test_check_python_tests_skips_non_test_functions(test_standards_checker):
    """Test that Check python tests skips non functions."""
    content = '''
def helper():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_python_tests(content)
    non_test_function_is_skipped = len(violations) == 0
    assert non_test_function_is_skipped


def test_check_javascript_typescript_tests_detects_multiple_expects(test_standards_checker):
    """Test that Check javascript typescript tests detects multiple expects."""
    content = '''
it('should work', () => {
  expect(1).toBe(1);
  expect(2).toBe(2);
});
'''
    violations = test_standards_checker.check_javascript_typescript_tests(content)
    multiple_expects_is_detected = len(violations) > 0
    assert multiple_expects_is_detected


def test_check_javascript_typescript_tests_allows_single_expect(test_standards_checker):
    """Test that Check javascript typescript tests allows single expect."""
    content = '''
it('should work', () => {
  expect(result).toBe(true);
});
'''
    violations = test_standards_checker.check_javascript_typescript_tests(content)
    single_expect_is_allowed = len(violations) == 0
    assert single_expect_is_allowed


def test_check_content_skips_non_test_files(test_standards_checker):
    """Test that Check content skips non files."""
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_content(content, 'main.py')
    non_test_file_is_skipped = len(violations) == 0
    assert non_test_file_is_skipped


def test_check_content_processes_test_file(test_standards_checker):
    """Test that Check content processes file."""
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_content(content, 'test_main.py')
    test_file_is_processed = len(violations) > 0
    assert test_file_is_processed


def test_check_content_processes_spec_file(test_standards_checker):
    """Test that Check content processes spec file."""
    content = '''
it('should work', () => {
  expect(1).toBe(1);
  expect(2).toBe(2);
});
'''
    violations = test_standards_checker.check_content(content, 'main.spec.ts')
    spec_file_is_processed = len(violations) > 0
    assert spec_file_is_processed


def test_pre_deployment_integration_rejects_invalid_filename(test_standards_checker):
    """Test that Pre-deployment integration rejects invalid filename."""
    file_path = 'test/api/pre_deployment/integration/test_my_custom_file.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    invalid_filename_is_rejected = len(violations) > 0
    assert invalid_filename_is_rejected


def test_pre_deployment_integration_allows_valid_authentication(test_standards_checker):
    """Test that Pre-deployment integration allows valid authentication file."""
    file_path = 'test/api/pre_deployment/integration/test_01_authentication.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    valid_filename_is_allowed = len(violations) == 0
    assert valid_filename_is_allowed


def test_pre_deployment_integration_allows_conftest(test_standards_checker):
    """Test that Pre-deployment integration allows conftest."""
    file_path = 'test/api/pre_deployment/integration/conftest.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    conftest_is_allowed = len(violations) == 0
    assert conftest_is_allowed


def test_post_deployment_integration_rejects_invalid_filename(test_standards_checker):
    """Test that Post-deployment integration rejects invalid filename."""
    file_path = 'test/api/post_deployment/integration/test_my_custom_file.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    invalid_filename_is_rejected = len(violations) > 0
    assert invalid_filename_is_rejected


def test_post_deployment_integration_allows_valid_existence(test_standards_checker):
    """Test that Post-deployment integration allows valid existence file."""
    file_path = 'test/api/post_deployment/integration/test_01_existence.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    valid_filename_is_allowed = len(violations) == 0
    assert valid_filename_is_allowed


def test_post_deployment_integration_allows_valid_wiring(test_standards_checker):
    """Test that Post-deployment integration allows valid wiring file."""
    file_path = 'test/api/post_deployment/integration/test_03_wiring.py'
    violations = test_standards_checker.check_integration_file_naming(file_path)
    valid_filename_is_allowed = len(violations) == 0
    assert valid_filename_is_allowed


def test_vague_test_name_test_works_is_rejected(test_standards_checker):
    """Test that Vague name test_works is rejected."""
    violation = test_standards_checker.check_descriptive_test_name('test_works')
    vague_name_is_rejected = violation is not None
    assert vague_name_is_rejected


def test_vague_test_name_test_1_is_rejected(test_standards_checker):
    """Test that Vague name test_1 is rejected."""
    violation = test_standards_checker.check_descriptive_test_name('test_1')
    vague_name_is_rejected = violation is not None
    assert vague_name_is_rejected


def test_vague_test_name_test_foo_is_rejected(test_standards_checker):
    """Test that Vague name test_foo is rejected."""
    violation = test_standards_checker.check_descriptive_test_name('test_foo')
    vague_name_is_rejected = violation is not None
    assert vague_name_is_rejected


def test_descriptive_test_name_is_allowed(test_standards_checker):
    """Test that Descriptive name is allowed."""
    violation = test_standards_checker.check_descriptive_test_name(
        'test_user_creation_returns_valid_id'
    )
    descriptive_name_is_allowed = violation is None
    assert descriptive_name_is_allowed


def test_e2e_without_docstring_is_rejected(test_standards_checker):
    """Test that E2e without docstring is rejected."""
    content = '''
def test_webhook_flow():
    pass
'''
    violations = test_standards_checker.check_python_tests(
        content, 'test/api/e2e/test_happy_path.py'
    )
    missing_docstring_is_rejected = any('user journey' in v.lower() for v in violations)
    assert missing_docstring_is_rejected


def test_e2e_with_user_journey_docstring_is_allowed(test_standards_checker):
    """Test that E2e with user journey docstring is allowed."""
    content = '''
def test_webhook_flow():
    """
    User Journey: GitHub webhook triggers runner provisioning.
    """
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(
        content, 'test/api/e2e/test_happy_path.py'
    )
    user_journey_docstring_is_allowed = not any('user journey' in v.lower() for v in violations)
    assert user_journey_docstring_is_allowed


def test_e2e_with_when_then_docstring_is_allowed(test_standards_checker):
    """Test that E2e with when then docstring is allowed."""
    content = '''
def test_webhook_flow():
    """
    When: A webhook arrives.
    Then: A runner is created.
    """
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(
        content, 'test/api/e2e/test_happy_path.py'
    )
    when_then_docstring_is_allowed = not any('user journey' in v.lower() for v in violations)
    assert when_then_docstring_is_allowed


def test_non_e2e_test_does_not_require_journey_docstring(test_standards_checker):
    """Test that Non-e2e test does not require journey docstring."""
    content = '''
def test_simple_function():
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(
        content, 'test/api/pre_deployment/unit/test_utils.py'
    )
    non_e2e_does_not_require_journey = not any('user journey' in v.lower() for v in violations)
    assert non_e2e_does_not_require_journey
