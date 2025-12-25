"""Tests for pre_git_checks hook."""


def test_run_blocked_lint_config_check_blocks_pylintrc(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .pylintrc files."""
    pylintrc = tmp_path / '.pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')
    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_pylintrc_no_dot(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks pylintrc files without dot."""
    pylintrc = tmp_path / 'pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')
    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_flake8(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .flake8 files."""
    flake8 = tmp_path / '.flake8'
    flake8.write_text('[flake8]\nmax-line-length = 999\n')
    changed_files = [str(flake8)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_mypy_ini(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .mypy.ini files."""
    mypy_ini = tmp_path / '.mypy.ini'
    mypy_ini.write_text('[mypy]\nignore_missing_imports = True\n')
    changed_files = [str(mypy_ini)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_tox_ini(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks tox.ini files."""
    tox_ini = tmp_path / 'tox.ini'
    tox_ini.write_text('[flake8]\nmax-line-length = 999\n')
    changed_files = [str(tox_ini)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_allows_regular_files(pre_git_checks):
    """Test that run_blocked_lint_config_check allows regular Python files."""
    changed_files = ['src/main.py', 'test/test_main.py', 'README.md']
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True


def test_run_blocked_lint_config_check_allows_empty_list(pre_git_checks):
    """Test that run_blocked_lint_config_check handles empty file list."""
    changed_files = []
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True


def test_run_blocked_lint_config_check_blocks_nested_pylintrc(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .pylintrc in nested paths."""
    nested_dir = tmp_path / 'deeply' / 'nested' / 'path'
    nested_dir.mkdir(parents=True)
    pylintrc = nested_dir / '.pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')

    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_allows_deleted_pylintrc(pre_git_checks):
    """Test that run_blocked_lint_config_check allows deletion of .pylintrc."""
    changed_files = ['nonexistent/path/.pylintrc']
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True


def test_should_skip_lint_check_skips_lint_blocker_tests(pre_git_checks):
    """Test that should_skip_lint_check skips test files for lint blocker."""
    result = pre_git_checks.should_skip_lint_check('test/test_lint_disable_blocker.py')
    assert result is True


def test_should_skip_lint_check_skips_hook_files(pre_git_checks):
    """Test that should_skip_lint_check skips hook files."""
    result = pre_git_checks.should_skip_lint_check('.claude/hooks/lint_disable_blocker.py')
    assert result is True


def test_should_skip_lint_check_does_not_skip_regular_files(pre_git_checks):
    """Test that should_skip_lint_check does not skip regular files."""
    result = pre_git_checks.should_skip_lint_check('src/main.py')
    assert result is False


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
    import ast
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
    import ast
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
    import ast
    source = '''
def test_something():
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    result = pre_git_checks.count_asserts_in_function(func_node)
    assert result == 0
