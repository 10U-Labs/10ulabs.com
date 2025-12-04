#!/usr/bin/env python3
"""Block lint disable comments in code."""
import re

from hook_utils import run_content_only_hook


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
    """Block code containing lint disable comments."""
    run_content_only_hook(
        check_content,
        "Lint disable comments are not allowed:",
        "Fix the actual code instead of disabling lint checks."
    )


if __name__ == '__main__':
    main()
