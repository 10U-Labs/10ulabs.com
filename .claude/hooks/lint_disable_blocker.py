#!/usr/bin/env python3
"""Block lint disable comments in code and workflow lint bypasses."""
import re
import sys

from hook_utils import (
    allow_tool_use,
    get_file_content,
    get_tool_input,
    LINT_DISABLE_PATTERNS,
)


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

LINT_CONFIG_FILES = [
    'pyproject.toml',
    '.pylintrc',
    'pylintrc',
    '.flake8',
    'setup.cfg',
    '.ruff.toml',
    'ruff.toml',
    '.eslintrc',
    '.eslintrc.js',
    '.eslintrc.json',
    '.eslintrc.yml',
    'eslint.config.js',
    'eslint.config.mjs',
    '.stylelintrc',
    '.markdownlint.json',
    '.yamllint',
    '.yamllint.yml',
    '.rubocop.yml',
    '.golangci.yml',
    '.shellcheckrc',
    'mypy.ini',
    '.mypy.ini',
    'tslint.json',
    'biome.json',
]

LINT_CONFIG_PATTERNS = [
    (r'\[tool\.pylint', 'pylint configuration in pyproject.toml'),
    (r'\[tool\.flake8\]', 'flake8 configuration in pyproject.toml'),
    (r'\[tool\.ruff\]', 'ruff configuration in pyproject.toml'),
    (r'\[tool\.ruff\.lint\]', 'ruff lint configuration in pyproject.toml'),
    (r'\[tool\.mypy\]', 'mypy configuration in pyproject.toml'),
    (r'\[tool\.isort\]', 'isort configuration in pyproject.toml'),
    (r'\[tool\.black\]', 'black configuration in pyproject.toml'),
    (r'\[flake8\]', 'flake8 configuration section'),
    (r'\[pylint\b', 'pylint configuration section'),
    (r'\[mypy\b', 'mypy configuration section'),
    (r'disable\s*=\s*\[', 'lint disable list'),
    (r'ignore\s*=\s*\[', 'lint ignore list'),
    (r'extend-ignore\s*=', 'lint extend-ignore'),
    (r'per-file-ignores\s*=', 'per-file-ignores'),
    (r'suppress_warnings\s*=', 'suppress_warnings'),
    (r'"rules"\s*:\s*\{[^}]*"off"', 'eslint rules set to "off"'),
    (r'"rules"\s*:\s*\{[^}]*:\s*0', 'eslint rules set to 0'),
    (r'select\s*=\s*\[\s*\]', 'empty lint select (disables all)'),
]


def is_workflow_file(file_path):
    """Check if the file is a GitHub Actions workflow."""
    return '.github/workflows/' in file_path and file_path.endswith('.yml')


def is_lint_config_file(file_path):
    """Check if the file is a lint configuration file."""
    if not file_path:
        return False
    for config_file in LINT_CONFIG_FILES:
        if file_path.endswith(config_file) or file_path.endswith('/' + config_file):
            return True
    return False


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


def check_lint_config_file(content, file_path):
    """Check if content contains lint configuration/suppression."""
    violations = []

    if not is_lint_config_file(file_path):
        return violations

    for pattern, description in LINT_CONFIG_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(description)

    return violations


def main():
    """Block code containing lint disable comments or workflow lint bypasses."""
    tool_input = get_tool_input()
    file_path, text_to_check = get_file_content(tool_input)

    if not text_to_check:
        allow_tool_use()

    violations = []

    violations.extend(check_inline_lint_disables(text_to_check))

    if file_path and is_workflow_file(file_path):
        violations.extend(check_workflow_lint_bypasses(text_to_check))

    if file_path:
        violations.extend(check_lint_config_file(text_to_check, file_path))

    if violations:
        print("BLOCKED: Lint disable patterns are not allowed:")
        for violation in set(violations):
            print(f"  - {violation}")
        print("\nFix the actual code instead of disabling lint checks.")
        sys.exit(2)

    allow_tool_use()


if __name__ == '__main__':
    main()
