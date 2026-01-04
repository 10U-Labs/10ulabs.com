"""Tests for pre_git_checks hook."""
import ast


def test_check_file_for_single_assert_detects_multiple_asserts(pre_git_checks, tmp_path):
    """Test that check_file_for_single_assert detects multiple asserts."""
    test_file = tmp_path / 'test_example.py'
    test_file.write_text('''
def test_something():
    assert 1 == 1
    assert 2 == 2
''')
    result = pre_git_checks.check_file_for_single_assert(str(test_file))
    assert len(result) == 1


def test_check_file_for_single_assert_allows_single_assert(pre_git_checks, tmp_path):
    """Test that check_file_for_single_assert allows single assert."""
    test_file = tmp_path / 'test_example.py'
    test_file.write_text('''
def test_something():
    assert 1 == 1
''')
    result = pre_git_checks.check_file_for_single_assert(str(test_file))
    assert len(result) == 0


def test_check_file_for_single_assert_skips_non_test_functions(pre_git_checks, tmp_path):
    """Test that check_file_for_single_assert skips non-test functions."""
    test_file = tmp_path / 'test_example.py'
    test_file.write_text('''
def helper():
    assert 1 == 1
    assert 2 == 2
''')
    result = pre_git_checks.check_file_for_single_assert(str(test_file))
    assert len(result) == 0


def test_check_file_for_single_assert_skips_non_python_files(pre_git_checks, tmp_path):
    """Test that check_file_for_single_assert skips non-Python files."""
    test_file = tmp_path / 'test_example.js'
    test_file.write_text('console.log("test");')
    result = pre_git_checks.check_file_for_single_assert(str(test_file))
    assert len(result) == 0


def test_check_file_for_single_assert_skips_files_without_test_path(pre_git_checks):
    """Test that check_file_for_single_assert skips files not in test path."""
    result = pre_git_checks.check_file_for_single_assert('src/main.py')
    assert len(result) == 0


def test_count_asserts_in_function_counts_single_assert(pre_git_checks):
    """Test that count_asserts_in_function counts single assert."""
    source = '''
def test_something():
    assert 1 == 1
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    result = pre_git_checks.count_asserts_in_function(func_node)
    assert result == 1


def test_count_asserts_in_function_counts_multiple_asserts(pre_git_checks):
    """Test that count_asserts_in_function counts multiple asserts."""
    source = '''
def test_something():
    assert 1 == 1
    assert 2 == 2
    assert 3 == 3
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    result = pre_git_checks.count_asserts_in_function(func_node)
    assert result == 3


def test_count_asserts_in_function_counts_zero_asserts(pre_git_checks):
    """Test that count_asserts_in_function counts zero asserts."""
    source = '''
def test_something():
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    result = pre_git_checks.count_asserts_in_function(func_node)
    assert result == 0
