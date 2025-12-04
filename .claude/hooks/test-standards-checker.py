#!/usr/bin/env python3
"""Check test standards: single assert per test, proper variable naming."""
import ast
import json
import re
import sys


TEST_FILE_PATTERNS = ['test_', '_test.py', '.test.ts', '.test.tsx', '.test.js', '.spec.ts', '.spec.tsx', '.spec.js']


def is_test_file(file_path):
    """Check if file is a test file."""
    result = any(pattern in file_path for pattern in TEST_FILE_PATTERNS)
    return result


class TestAssertAnalyzer(ast.NodeVisitor):
    """Analyze Python test functions for assertion violations."""

    def __init__(self):
        self.violations = []

    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            self._check_test_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if node.name.startswith('test_'):
            self._check_test_function(node)
        self.generic_visit(node)

    def _check_test_function(self, node):
        assert_count = 0
        assert_nodes = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assert_count += 1
                assert_nodes.append(child)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    method_name = child.func.attr
                    if method_name.startswith('assert') or method_name in ['assertEqual', 'assertTrue', 'assertFalse', 'assertIs', 'assertIsNot', 'assertIsNone', 'assertIsNotNone', 'assertIn', 'assertNotIn', 'assertRaises']:
                        assert_count += 1
                elif isinstance(child.func, ast.Name):
                    if child.func.id in ['assert_that', 'expect']:
                        assert_count += 1

        if assert_count > 1:
            self.violations.append(
                f"Test '{node.name}' has {assert_count} assertions (must have 1)"
            )

        for assert_node in assert_nodes:
            self._check_assert_variable_format(node.name, assert_node)

    def _check_assert_variable_format(self, test_name, assert_node):
        """Check that assert uses a single variable with proper naming."""
        test_expr = assert_node.test

        if isinstance(test_expr, ast.Name):
            var_name = test_expr.id
            if not self._is_valid_assert_variable_name(var_name):
                self.violations.append(
                    f"Test '{test_name}': assert variable '{var_name}' must follow "
                    f"{{noun_phrase}}_{{verb}} or {{noun_phrase}}_{{verb}}_{{adj/adv}} format"
                )
        elif isinstance(test_expr, ast.Compare):
            pass
        elif isinstance(test_expr, ast.Call):
            pass
        else:
            self.violations.append(
                f"Test '{test_name}': assert should use a single descriptive variable"
            )

    def _is_valid_assert_variable_name(self, name):
        """Check if variable name follows the required format."""
        parts = name.split('_')
        if len(parts) < 2:
            return False

        verb_indicators = [
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

        has_verb = any(part.lower() in verb_indicators for part in parts)

        return has_verb


def check_javascript_typescript_tests(content):
    """Check JS/TS test files for multiple assertions per test."""
    violations = []

    test_pattern = r'(it|test)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(async\s*)?\([^)]*\)\s*=>\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'

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


def check_python_tests(content):
    """Check Python test files for violations."""
    violations = []
    try:
        tree = ast.parse(content)
        analyzer = TestAssertAnalyzer()
        analyzer.visit(tree)
        violations = analyzer.violations
    except SyntaxError:
        pass
    return violations


def check_content(content, file_path):
    """Check content for test standard violations."""
    violations = []

    if not is_test_file(file_path):
        return violations

    if file_path.endswith('.py'):
        violations.extend(check_python_tests(content))
    elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
        violations.extend(check_javascript_typescript_tests(content))

    return violations


def main():
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        tool_input = data.get('tool_input', {})
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = tool_input.get('file_path', '')
    content = tool_input.get('content', '')
    new_string = tool_input.get('new_string', '')

    text_to_check = content or new_string
    if not text_to_check or not file_path:
        sys.exit(0)

    violations = check_content(text_to_check, file_path)

    if violations:
        print("BLOCKED: Test standard violations detected:")
        for violation in violations:
            print(f"  - {violation}")
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
