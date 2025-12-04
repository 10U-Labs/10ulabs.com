#!/usr/bin/env python3
"""Shared utilities for Claude Code hooks."""
import json
import sys
from typing import Callable


def get_tool_input():
    """Read and parse JSON input from stdin, return tool_input dict."""
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        return data.get('tool_input', {})
    except json.JSONDecodeError:
        return {}


def get_file_content(tool_input):
    """Extract file path and text content from tool input."""
    file_path = tool_input.get('file_path', '')
    content = tool_input.get('content', '')
    new_string = tool_input.get('new_string', '')
    text_to_check = content or new_string
    return file_path, text_to_check


def report_violations_and_exit(violations, blocked_message):
    """Print violations with blocked message and exit appropriately."""
    if violations:
        print(f"BLOCKED: {blocked_message}")
        for violation in violations:
            print(f"  - {violation}")
        sys.exit(2)
    sys.exit(0)


def run_file_content_hook(check_fn: Callable, blocked_message: str):
    """Run a hook that checks file content for violations."""
    tool_input = get_tool_input()
    file_path, text_to_check = get_file_content(tool_input)

    if not text_to_check or not file_path:
        sys.exit(0)

    violations = check_fn(text_to_check, file_path)
    report_violations_and_exit(violations, blocked_message)


def run_content_only_hook(check_fn: Callable, blocked_message: str, extra_message: str = ""):
    """Run a hook that checks content without needing file path."""
    tool_input = get_tool_input()
    _, text_to_check = get_file_content(tool_input)

    if not text_to_check:
        sys.exit(0)

    violations = check_fn(text_to_check)
    if violations:
        print(f"BLOCKED: {blocked_message}")
        for violation in set(violations):
            print(f"  - {violation}")
        if extra_message:
            print(f"\n{extra_message}")
        sys.exit(2)
    sys.exit(0)
