def test_is_test_file_returns_true_for_test_prefix(test_standards_checker):
    test_prefix_file_is_test = test_standards_checker.is_test_file('test_main.py')
    assert test_prefix_file_is_test


def test_is_test_file_returns_true_for_test_suffix(test_standards_checker):
    test_suffix_file_is_test = test_standards_checker.is_test_file('main_test.py')
    assert test_suffix_file_is_test


def test_is_test_file_returns_true_for_spec_ts(test_standards_checker):
    spec_ts_file_is_test = test_standards_checker.is_test_file('main.spec.ts')
    assert spec_ts_file_is_test


def test_is_test_file_returns_true_for_test_ts(test_standards_checker):
    test_ts_file_is_test = test_standards_checker.is_test_file('main.test.ts')
    assert test_ts_file_is_test


def test_is_test_file_returns_true_for_spec_js(test_standards_checker):
    spec_js_file_is_test = test_standards_checker.is_test_file('main.spec.js')
    assert spec_js_file_is_test


def test_is_test_file_returns_false_for_regular_py(test_standards_checker):
    regular_py_file_is_not_test = not test_standards_checker.is_test_file('main.py')
    assert regular_py_file_is_not_test


def test_is_test_file_returns_false_for_regular_ts(test_standards_checker):
    regular_ts_file_is_not_test = not test_standards_checker.is_test_file('main.ts')
    assert regular_ts_file_is_not_test


def test_check_python_tests_detects_multiple_asserts(test_standards_checker):
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_python_tests(content)
    multiple_asserts_is_detected = len(violations) > 0
    assert multiple_asserts_is_detected


def test_check_python_tests_allows_single_assert(test_standards_checker):
    content = '''
def test_example():
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(content)
    single_assert_is_allowed = len(violations) == 0
    assert single_assert_is_allowed


def test_check_python_tests_detects_invalid_variable_name(test_standards_checker):
    content = '''
def test_example():
    x = True
    assert x
'''
    violations = test_standards_checker.check_python_tests(content)
    invalid_variable_name_is_detected = len(violations) > 0
    assert invalid_variable_name_is_detected


def test_check_python_tests_allows_valid_variable_name_with_verb(test_standards_checker):
    content = '''
def test_example():
    result_is_valid = True
    assert result_is_valid
'''
    violations = test_standards_checker.check_python_tests(content)
    valid_variable_name_with_verb_is_allowed = len(violations) == 0
    assert valid_variable_name_with_verb_is_allowed


def test_check_python_tests_allows_variable_name_with_exists(test_standards_checker):
    content = '''
def test_example():
    file_exists = True
    assert file_exists
'''
    violations = test_standards_checker.check_python_tests(content)
    variable_name_with_exists_is_allowed = len(violations) == 0
    assert variable_name_with_exists_is_allowed


def test_check_python_tests_allows_variable_name_with_contains(test_standards_checker):
    content = '''
def test_example():
    list_contains_item = True
    assert list_contains_item
'''
    violations = test_standards_checker.check_python_tests(content)
    variable_name_with_contains_is_allowed = len(violations) == 0
    assert variable_name_with_contains_is_allowed


def test_check_python_tests_skips_non_test_functions(test_standards_checker):
    content = '''
def helper():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_python_tests(content)
    non_test_function_is_skipped = len(violations) == 0
    assert non_test_function_is_skipped


def test_check_javascript_typescript_tests_detects_multiple_expects(test_standards_checker):
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
    content = '''
it('should work', () => {
  expect(result).toBe(true);
});
'''
    violations = test_standards_checker.check_javascript_typescript_tests(content)
    single_expect_is_allowed = len(violations) == 0
    assert single_expect_is_allowed


def test_check_content_skips_non_test_files(test_standards_checker):
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_content(content, 'main.py')
    non_test_file_is_skipped = len(violations) == 0
    assert non_test_file_is_skipped


def test_check_content_processes_test_file(test_standards_checker):
    content = '''
def test_example():
    assert 1 == 1
    assert 2 == 2
'''
    violations = test_standards_checker.check_content(content, 'test_main.py')
    test_file_is_processed = len(violations) > 0
    assert test_file_is_processed


def test_check_content_processes_spec_file(test_standards_checker):
    content = '''
it('should work', () => {
  expect(1).toBe(1);
  expect(2).toBe(2);
});
'''
    violations = test_standards_checker.check_content(content, 'main.spec.ts')
    spec_file_is_processed = len(violations) > 0
    assert spec_file_is_processed
