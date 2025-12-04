#!/usr/bin/env python3
"""Block lint disable comments in code."""
import json
import re
import sys


LINT_DISABLE_PATTERNS = [
    (r'eslint-disable', 'eslint-disable comment'),
    (r'eslint-disable-next-line', 'eslint-disable-next-line comment'),
    (r'eslint-disable-line', 'eslint-disable-line comment'),
    (r'@ts-ignore', '@ts-ignore comment'),
    (r'@ts-nocheck', '@ts-nocheck comment'),
    (r'@ts-expect-error', '@ts-expect-error comment'),
    (r'# noqa', 'noqa comment'),
    (r'#noqa', 'noqa comment'),
    (r'# type:\s*ignore', 'type: ignore comment'),
    (r'#type:\s*ignore', 'type: ignore comment'),
    (r'# pylint:\s*disable', 'pylint: disable comment'),
    (r'#pylint:\s*disable', 'pylint: disable comment'),
    (r'# pragma:\s*no\s*cover', 'pragma: no cover comment'),
    (r'# flake8:\s*noqa', 'flake8: noqa comment'),
    (r'# noinspection', 'noinspection comment'),
    (r'// nolint', 'nolint comment (Go)'),
    (r'//nolint', 'nolint comment (Go)'),
    (r'#\s*rubocop:disable', 'rubocop:disable comment'),
    (r'// NOLINT', 'NOLINT comment (C++)'),
    (r'//NOLINT', 'NOLINT comment (C++)'),
    (r'# shellcheck\s+disable', 'shellcheck disable comment'),
    (r'<!-- markdownlint-disable', 'markdownlint-disable comment'),
    (r'# yamllint\s+disable', 'yamllint disable comment'),
    (r'stylelint-disable', 'stylelint-disable comment'),
]


def check_content(content):
    """Check content for lint disable patterns."""
    violations = []
    for pattern, description in LINT_DISABLE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            violations.append(description)
    return violations


def main():
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        tool_input = data.get('tool_input', {})
    except json.JSONDecodeError:
        sys.exit(0)

    content = tool_input.get('content', '')
    new_string = tool_input.get('new_string', '')

    text_to_check = content or new_string
    if not text_to_check:
        sys.exit(0)

    violations = check_content(text_to_check)

    if violations:
        print("BLOCKED: Lint disable comments are not allowed:")
        for violation in set(violations):
            print(f"  - {violation}")
        print("\nFix the actual code instead of disabling lint checks.")
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
