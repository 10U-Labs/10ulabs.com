#!/usr/bin/env python3
"""Check test standards: single assert per test, proper variable naming."""
import ast
import os
import re

from hook_utils import run_file_content_hook


TEST_FILE_PATTERNS = [
    'test_', '_test.py', '.test.ts', '.test.tsx',
    '.test.js', '.spec.ts', '.spec.tsx', '.spec.js'
]

VERB_INDICATORS = [
    'is', 'are', 'was', 'were', 'has', 'have', 'had',
    'does', 'do', 'did', 'can', 'could', 'will', 'would',
    'should', 'must', 'exists', 'exist', 'contains', 'contain',
    'matches', 'match', 'equals', 'equal', 'returns', 'return',
    'raises', 'raise', 'throws', 'throw', 'includes', 'include',
    'starts', 'ends', 'created', 'updated', 'deleted', 'found',
    'loaded', 'saved', 'valid', 'invalid', 'empty', 'present',
    'absent', 'enabled', 'disabled', 'active', 'inactive',
    'successful', 'failed', 'passed', 'completed', 'finished',
]

ASSERT_METHODS = [
    'assertEqual', 'assertTrue', 'assertFalse', 'assertIs',
    'assertIsNot', 'assertIsNone', 'assertIsNotNone',
    'assertIn', 'assertNotIn', 'assertRaises'
]

VAGUE_TEST_NAMES = [
    r'^test_works$',
    r'^test_it_works$',
    r'^test_should_work$',
    r'^test_\d+$',
    r'^test_foo$',
    r'^test_bar$',
    r'^test_something$',
    r'^test_stuff$',
    r'^test_[a-z]$',
]

PRE_DEPLOYMENT_INTEGRATION_FILES = [
    'test_01_authentication.py',
    'test_02_authorization.py',
    'test_03_existence.py',
    'test_04_configuration.py',
    'test_05_capability.py',
    'conftest.py',
    '__init__.py',
]

POST_DEPLOYMENT_INTEGRATION_FILES = [
    'test_01_existence.py',
    'test_02_configuration.py',
    'test_03_wiring.py',
    'conftest.py',
    '__init__.py',
]


def is_test_file(file_path):
    """Check if file is a test file."""
    result = any(pattern in file_path for pattern in TEST_FILE_PATTERNS)
    return result


def check_integration_file_naming(file_path):
    """Check integration test files follow naming conventions."""
    violations = []

    if 'pre_deployment/integration/' in file_path:
        filename = os.path.basename(file_path)
        if filename not in PRE_DEPLOYMENT_INTEGRATION_FILES:
            valid_tests = ', '.join(PRE_DEPLOYMENT_INTEGRATION_FILES[:5])
            violations.append(
                f"Pre-deployment integration file '{filename}' invalid. "
                f"Must be one of: {valid_tests}"
            )

    elif 'post_deployment/integration/' in file_path:
        filename = os.path.basename(file_path)
        if filename not in POST_DEPLOYMENT_INTEGRATION_FILES:
            valid_tests = ', '.join(POST_DEPLOYMENT_INTEGRATION_FILES[:3])
            violations.append(
                f"Post-deployment integration file '{filename}' invalid. "
                f"Must be one of: {valid_tests}"
            )

    return violations


def check_descriptive_test_name(func_name):
    """Check test name is descriptive, not vague."""
    for pattern in VAGUE_TEST_NAMES:
        if re.match(pattern, func_name, re.IGNORECASE):
            return f"Test '{func_name}' has vague name - be descriptive"
    return None


def check_e2e_docstring(file_path, func_node):
    """Check e2e test has proper docstring documenting user journey."""
    if '/e2e/' not in file_path:
        return []

    violations = []
    docstring = ast.get_docstring(func_node) or ""

    has_journey = 'user journey' in docstring.lower()
    has_when_then = 'when:' in docstring.lower() and 'then:' in docstring.lower()

    if not has_journey and not has_when_then:
        violations.append(
            f"E2E test '{func_node.name}' must document user journey. "
            f"Add 'User Journey:' or 'When:/Then:' to docstring"
        )

    return violations


def is_valid_assert_variable_name(name):
    """Check if variable name follows the required format."""
    parts = name.split('_')
    if len(parts) < 2:
        return False
    has_verb = any(part.lower() in VERB_INDICATORS for part in parts)
    return has_verb


def check_assert_variable_format(test_name, assert_node):
    """Check that assert uses a single variable with proper naming."""
    violations = []
    test_expr = assert_node.test

    if isinstance(test_expr, ast.Name):
        var_name = test_expr.id
        if not is_valid_assert_variable_name(var_name):
            violations.append(
                f"Test '{test_name}': assert variable '{var_name}' must follow "
                f"{{noun_phrase}}_{{verb}} or {{noun_phrase}}_{{verb}}_{{adj/adv}} format"
            )
    elif isinstance(test_expr, ast.Compare):
        pass
    elif isinstance(test_expr, ast.Call):
        pass
    else:
        violations.append(
            f"Test '{test_name}': assert should use a single descriptive variable"
        )

    return violations


def check_test_function(node, file_path):
    """Check a single test function for violations."""
    violations = []
    assert_count = 0
    assert_nodes = []

    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            assert_count += 1
            assert_nodes.append(child)
        elif isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                method_name = child.func.attr
                if method_name.startswith('assert') or method_name in ASSERT_METHODS:
                    assert_count += 1
            elif isinstance(child.func, ast.Name):
                if child.func.id in ['assert_that', 'expect']:
                    assert_count += 1

    if assert_count > 1:
        violations.append(
            f"Test '{node.name}' has {assert_count} assertions (must have 1)"
        )

    for assert_node in assert_nodes:
        violations.extend(check_assert_variable_format(node.name, assert_node))

    name_violation = check_descriptive_test_name(node.name)
    if name_violation:
        violations.append(name_violation)

    violations.extend(check_e2e_docstring(file_path, node))

    return violations


def analyze_python_tests(tree, file_path):
    """Analyze all test functions in a Python AST for violations."""
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('test_'):
                violations.extend(check_test_function(node, file_path))
    return violations


def check_javascript_typescript_tests(content):
    """Check JS/TS test files for multiple assertions per test."""
    violations = []

    # Pattern to match test('name', () => { ... }) or it('name', async () => { ... })
    test_pattern = (
        r'(it|test)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*'
        r'(async\s*)?\([^)]*\)\s*=>\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    )

    for match in re.finditer(test_pattern, content, re.DOTALL):
        test_name = match.group(2)
        test_body = match.group(4)

        assert_patterns = [
            r'\bexpect\s*\(',
            r'\bassert\s*\.',
            r'\bassert\s*\(',
        ]

        assert_count = sum(len(re.findall(p, test_body)) for p in assert_patterns)

        if assert_count > 1:
            violations.append(
                f"Test '{test_name}' has {assert_count} assertions (must have 1)"
            )

    return violations


def check_python_tests(content, file_path=""):
    """Check Python test files for violations."""
    violations = []
    try:
        tree = ast.parse(content)
        violations = analyze_python_tests(tree, file_path)
    except SyntaxError:
        pass
    return violations


def check_content(content, file_path):
    """Check content for test standard violations."""
    violations = []

    if not is_test_file(file_path):
        return violations

    violations.extend(check_integration_file_naming(file_path))

    if file_path.endswith('.py'):
        violations.extend(check_python_tests(content, file_path))
    elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
        violations.extend(check_javascript_typescript_tests(content))

    return violations


def main():
    """Check test files for test standard violations."""
    run_file_content_hook(check_content, "Test standard violations detected:")


if __name__ == '__main__':
    main()
