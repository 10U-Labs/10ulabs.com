#!/usr/bin/env python3
"""Block lint disable comments in code and workflow lint bypasses."""
import re
import sys

from hook_utils import get_tool_input, get_file_content, LINT_DISABLE_PATTERNS

LINT_KEYWORDS = [
    'lint', 'linting', 'eslint', 'pylint', 'flake8', 'mypy', 'ruff',
    'yamllint', 'shellcheck', 'rubocop', 'golangci', 'staticcheck',
    'prettier', 'black', 'isort', 'stylelint', 'markdownlint',
    'static.analysis', 'static-analysis', 'static_analysis',
]

WORKFLOW_LINT_BYPASS_PATTERNS = [
    (r'\|\|\s*true\b', 'suppressing lint failure with "|| true"'),
    (r'\|\|\s*exit\s+0', 'suppressing lint failure with "|| exit 0"'),
    (r'\|\|\s*:', 'suppressing lint failure with "|| :"'),
    (r'continue-on-error:\s*true', 'continue-on-error: true on lint step'),
    (r'if:\s*false', 'skipping lint step with "if: false"'),
    (r'if:\s*\$\{\{\s*false\s*\}\}', 'skipping lint step with "if: ${{ false }}"'),
]


def is_workflow_file(file_path):
    """Check if the file is a GitHub Actions workflow."""
    return '.github/workflows/' in file_path and file_path.endswith('.yml')


def check_inline_lint_disables(content):
    """Check content for inline lint disable patterns."""
    violations = []
    for pattern, description in LINT_DISABLE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(description)
    return violations


def check_workflow_lint_bypasses(content):
    """Check workflow content for lint bypass patterns."""
    violations = []
    content_lower = content.lower()

    has_lint_context = any(kw in content_lower for kw in LINT_KEYWORDS)
    if not has_lint_context:
        return violations

    for pattern, description in WORKFLOW_LINT_BYPASS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(description)

    return violations


def main():
    """Block code containing lint disable comments or workflow lint bypasses."""
    tool_input = get_tool_input()
    file_path, text_to_check = get_file_content(tool_input)

    if not text_to_check:
        sys.exit(0)

    violations = []

    violations.extend(check_inline_lint_disables(text_to_check))

    if file_path and is_workflow_file(file_path):
        violations.extend(check_workflow_lint_bypasses(text_to_check))

    if violations:
        print("BLOCKED: Lint disable patterns are not allowed:")
        for violation in set(violations):
            print(f"  - {violation}")
        print("\nFix the actual code instead of disabling lint checks.")
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
