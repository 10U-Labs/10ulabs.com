#!/usr/bin/env python3
"""Pre-git checks hook that runs static analysis before git commit."""
import ast
import datetime
import json
import os
import re
import subprocess
import sys


DEBUG_LOG = os.path.expanduser('~/.claude/hook_debug.log')
OUTPUT_LINES: list[str] = []


def _allow_tool_use(system_message: str = ""):
    """Allow tool use by outputting JSON with permissionDecision: allow."""
    output: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Auto-approved"
        }
    }
    if system_message:
        output["systemMessage"] = system_message
    print(json.dumps(output))
    sys.exit(0)


def _deny_tool_use(reason: str, system_message: str = ""):
    """Deny tool use by outputting JSON with permissionDecision: deny."""
    output: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }
    if system_message:
        output["systemMessage"] = system_message
    print(json.dumps(output))
    sys.exit(0)


def capture_print(message=""):
    """Capture output for later inclusion in hook response JSON."""
    OUTPUT_LINES.append(message)


def get_system_message():
    """Get the captured output as a system message string."""
    return "\n".join(OUTPUT_LINES) if OUTPUT_LINES else ""


def allow_tool_use():
    """Allow tool use, including captured output as system message."""
    _allow_tool_use(get_system_message())


def deny_tool_use(reason):
    """Deny tool use, including captured output as system message."""
    _deny_tool_use(reason, get_system_message())


def log_debug(message):
    """Append debug message to log file for diagnosing hook issues."""
    try:
        with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"[{timestamp}] {message}\n")
    except (IOError, OSError):
        pass


def get_changed_files(command=''):
    """Get list of changed files from git staging area, working tree, or last commit."""
    files = set()

    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--no-ext-diff'],
        capture_output=True, text=True, check=False
    )
    staged = result.stdout.strip().split('\n') if result.stdout.strip() else []
    log_debug(f"git diff --cached returned {len(staged)} files: {staged[:5]}...")
    files.update(f for f in staged if f)

    if 'git add' in command:
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--no-ext-diff'],
            capture_output=True, text=True, check=False
        )
        unstaged = result.stdout.strip().split('\n') if result.stdout.strip() else []
        log_debug(f"git diff (unstaged) returned {len(unstaged)} files: {unstaged[:5]}...")
        files.update(f for f in unstaged if f)

        if re.search(r'git add\s+(-A|\.)', command):
            result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                capture_output=True, text=True, check=False
            )
            untracked = result.stdout.strip().split('\n') if result.stdout.strip() else []
            log_debug(f"git ls-files (untracked) returned {len(untracked)} files")
            files.update(f for f in untracked if f)

    if not files:
        log_debug("No staged/unstaged files, falling back to HEAD~1")
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', '--name-only', '--no-ext-diff'],
            capture_output=True, text=True, check=False
        )
        fallback = result.stdout.strip().split('\n') if result.stdout.strip() else []
        log_debug(f"git diff HEAD~1 returned {len(fallback)} files: {fallback[:5]}...")
        files.update(f for f in fallback if f)

    return [f for f in files if f]


def count_asserts_in_function(func_node):
    """Count the number of assert statements in a function node."""
    return sum(1 for node in ast.walk(func_node) if isinstance(node, ast.Assert))


def check_file_for_single_assert(file_path):
    """Check a test file for functions with multiple asserts."""
    if not file_path.endswith('.py'):
        return []

    if not (file_path.startswith('test/') or '/test_' in file_path
            or file_path.startswith('tests/')):
        return []

    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, encoding='utf-8') as f:
            source = f.read()
    except (OSError, IOError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('test_'):
                continue

            assert_count = count_asserts_in_function(node)

            if assert_count > 1:
                violations.append((
                    file_path,
                    node.lineno,
                    node.name,
                    assert_count
                ))

    return violations


def run_single_assert_check(changed_files):
    """Run single-assert-per-test check. Returns True if passed, False if failed."""
    capture_print("\n" + "="*60)
    capture_print("PHASE: SINGLE ASSERT CHECK")
    capture_print("="*60)

    all_violations = []
    for file_path in changed_files:
        violations = check_file_for_single_assert(file_path)
        all_violations.extend(violations)

    if all_violations:
        capture_print("\nSINGLE ASSERT VIOLATIONS FOUND:")
        for file_path, line_num, func_name, count in all_violations:
            msg = f"  {file_path}:{line_num} - {func_name}() has {count} asserts"
            capture_print(msg)
        capture_print("\n" + "="*60)
        capture_print("SINGLE ASSERT CHECK FAILED")
        capture_print("Each test function should have exactly one assert.")
        capture_print("Split tests with multiple asserts into separate test functions.")
        capture_print("="*60)
        print("SINGLE ASSERT CHECK FAILED", file=sys.stderr)
        return False

    capture_print("All test functions have single asserts.")
    return True


def parse_command_from_stdin():
    """Parse the bash command from Claude Code hook stdin JSON."""
    input_data = sys.stdin.read()
    log_debug(f"pre_git_checks: stdin received {len(input_data)} bytes")
    if not input_data:
        log_debug("pre_git_checks: WARNING - stdin was empty!")
        print("WARNING: pre_git_checks received empty stdin", file=sys.stderr)
    try:
        data = json.loads(input_data)
        command = data.get('tool_input', {}).get('command', '')
        log_debug(f"pre_git_checks: parsed command: {command[:100]}...")
        return command
    except json.JSONDecodeError as e:
        log_debug(f"pre_git_checks: JSON decode error: {e}")
        return ''


def run_file_level_checks(changed_files):
    """Run all file-level checks. Calls deny_tool_use on failure."""
    if not run_single_assert_check(changed_files):
        log_debug("SINGLE ASSERT CHECK FAILED - denying tool use")
        deny_tool_use("SINGLE ASSERT CHECK FAILED - Split into separate tests")


def main():
    """Main entry point for the pre-git checks hook."""
    command = parse_command_from_stdin()
    if not command or not re.search(r'\bgit\s+(?:[\w-]+\s+\S+\s+)*commit\b', command):
        log_debug(f"pre_git_checks: skipping - not a git commit (command: {command[:50]}...)")
        allow_tool_use()

    log_debug("pre_git_checks: starting static analysis checks")
    capture_print("Running static analysis before git commit...")
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '.')
    os.chdir(project_dir)

    changed_files = get_changed_files(command)
    if not changed_files:
        log_debug("No changed files found - allowing")
        capture_print("No changed files.")
        allow_tool_use()

    log_debug(f"Found {len(changed_files)} changed files: {changed_files}")
    capture_print(f"Changed files ({len(changed_files)}):")
    for f in changed_files:
        capture_print(f"  - {f}")

    run_file_level_checks(changed_files)

    log_debug("ALL CHECKS PASSED - exiting with code 0")
    capture_print("\n" + "="*60)
    capture_print("ALL CHECKS PASSED")
    capture_print("="*60)
    allow_tool_use()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, TypeError, OSError, IOError) as e:
        log_debug(f"UNHANDLED EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        log_debug(f"Traceback: {traceback.format_exc()}")
        deny_tool_use(f"Hook crashed: {e}")
