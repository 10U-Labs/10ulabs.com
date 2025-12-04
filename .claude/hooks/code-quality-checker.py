#!/usr/bin/env python3
"""Check code quality: single return per function, no break/continue."""
import ast
import json
import re
import sys


CODE_EXTENSIONS = ['.py', '.ts', '.tsx', '.js', '.jsx']


def is_code_file(file_path):
    """Check if file is a code file."""
    result = any(file_path.endswith(ext) for ext in CODE_EXTENSIONS)
    return result


class PythonFunctionAnalyzer(ast.NodeVisitor):
    """Analyze Python functions for violations."""

    def __init__(self):
        self.violations = []

    def visit_FunctionDef(self, node):
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node):
        return_count = 0
        has_break = False
        has_continue = False

        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child is not node:
                    pass
            elif isinstance(child, ast.Return):
                parent_func = self._get_parent_function(node, child)
                if parent_func is node:
                    return_count += 1
            elif isinstance(child, ast.Break):
                has_break = True
            elif isinstance(child, ast.Continue):
                has_continue = True

        if return_count > 1:
            self.violations.append(
                f"Function '{node.name}' has {return_count} return statements (must have 1)"
            )
        if has_break:
            self.violations.append(
                f"Function '{node.name}' uses 'break' statement"
            )
        if has_continue:
            self.violations.append(
                f"Function '{node.name}' uses 'continue' statement"
            )

    def _get_parent_function(self, root, target):
        """Find the immediate parent function of a node."""
        for node in ast.walk(root):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        return node
        return root


def count_returns_in_function(func_body):
    """Count return statements in a function body (for JS/TS)."""
    return_pattern = r'\breturn\b'
    return len(re.findall(return_pattern, func_body))


def check_python(content):
    """Check Python code for violations."""
    violations = []
    try:
        tree = ast.parse(content)
        analyzer = PythonFunctionAnalyzer()
        analyzer.visit(tree)
        violations = analyzer.violations
    except SyntaxError:
        pass
    return violations


def check_javascript_typescript(content):
    """Check JS/TS code for break/continue (return counting is harder without AST)."""
    violations = []

    break_pattern = r'\bbreak\s*;'
    continue_pattern = r'\bcontinue\s*;'

    if re.search(break_pattern, content):
        violations.append("Code contains 'break' statement")
    if re.search(continue_pattern, content):
        violations.append("Code contains 'continue' statement")

    return violations


def check_content(content, file_path):
    """Check content for code quality violations."""
    violations = []

    if not is_code_file(file_path):
        return violations

    if file_path.endswith('.py'):
        violations.extend(check_python(content))
    elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
        violations.extend(check_javascript_typescript(content))

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
        print("BLOCKED: Code quality violations detected:")
        for violation in violations:
            print(f"  - {violation}")
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
