#!/usr/bin/env python3
"""Check code quality: single return per function, no break/continue."""
import ast
import re

from hook_utils import run_file_content_hook


CODE_EXTENSIONS = ['.py', '.ts', '.tsx', '.js', '.jsx']


def is_code_file(file_path):
    """Check if file is a code file."""
    result = any(file_path.endswith(ext) for ext in CODE_EXTENSIONS)
    return result


def get_parent_function(root, target):
    """Find the immediate parent function of a node."""
    for node in ast.walk(root):
        for child in ast.iter_child_nodes(node):
            if child is target:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return node
    return root


def check_function(node):
    """Check a single function for violations."""
    violations = []
    return_count = 0
    has_break = False
    has_continue = False

    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child is not node:
                pass
        elif isinstance(child, ast.Return):
            parent_func = get_parent_function(node, child)
            if parent_func is node:
                return_count += 1
        elif isinstance(child, ast.Break):
            has_break = True
        elif isinstance(child, ast.Continue):
            has_continue = True

    if return_count > 1:
        violations.append(
            f"Function '{node.name}' has {return_count} return statements (must have 1)"
        )
    if has_break:
        violations.append(f"Function '{node.name}' uses 'break' statement")
    if has_continue:
        violations.append(f"Function '{node.name}' uses 'continue' statement")

    return violations


def analyze_python_functions(tree):
    """Analyze all functions in a Python AST for violations."""
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(check_function(node))
    return violations


def count_returns_in_function(func_body):
    """Count return statements in a function body (for JS/TS)."""
    return_pattern = r'\breturn\b'
    return len(re.findall(return_pattern, func_body))


def check_python(content):
    """Check Python code for violations."""
    violations = []
    try:
        tree = ast.parse(content)
        violations = analyze_python_functions(tree)
    except SyntaxError:
        pass
    return violations


def check_javascript_typescript(content):
    """Check JS/TS code for break/continue (return counting harder without AST)."""
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
    """Check file content for code quality violations."""
    run_file_content_hook(check_content, "Code quality violations detected:")


if __name__ == '__main__':
    main()
