#!/usr/bin/env python3
"""Block creation of linter configuration files."""
import json
import os
import sys


def allow_tool_use():
    """Allow tool use by outputting JSON with permissionDecision: allow."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Auto-approved"
        }
    }
    print(json.dumps(output))
    sys.exit(0)


BLOCKED_FILENAMES = [
    '.eslintrc',
    '.eslintrc.js',
    '.eslintrc.cjs',
    '.eslintrc.json',
    '.eslintrc.yml',
    '.eslintrc.yaml',
    'eslint.config.js',
    'eslint.config.mjs',
    'eslint.config.cjs',
    '.pylintrc',
    'pylintrc',
    '.flake8',
    'setup.cfg',
    'tox.ini',
    '.prettierrc',
    '.prettierrc.js',
    '.prettierrc.cjs',
    '.prettierrc.json',
    '.prettierrc.yml',
    '.prettierrc.yaml',
    'prettier.config.js',
    'prettier.config.cjs',
    '.stylelintrc',
    '.stylelintrc.js',
    '.stylelintrc.json',
    '.stylelintrc.yml',
    '.stylelintrc.yaml',
    'stylelint.config.js',
    '.htmlhintrc',
    '.markdownlint.json',
    '.markdownlint.yaml',
    '.markdownlintrc',
    '.yamllint',
    '.yamllint.yml',
    '.yamllint.yaml',
    '.hadolint.yaml',
    '.hadolint.yml',
    '.tflint.hcl',
    '.rubocop.yml',
    '.rubocop.yaml',
    '.shellcheckrc',
    'mypy.ini',
    '.mypy.ini',
    'ruff.toml',
    '.ruff.toml',
    '.bandit',
    '.bandit.yml',
    'pyproject.toml',
]


def main():
    """Block creation of linter configuration files."""
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        file_path = data.get('tool_input', {}).get('file_path', '')
    except json.JSONDecodeError:
        allow_tool_use()

    if not file_path:
        allow_tool_use()

    filename = os.path.basename(file_path)

    if filename in BLOCKED_FILENAMES:
        print(f"BLOCKED: Cannot create linter configuration file: {filename}")
        print("Fix the actual code instead of configuring linters.")
        sys.exit(2)

    allow_tool_use()


if __name__ == '__main__':
    main()
