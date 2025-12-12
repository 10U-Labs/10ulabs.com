#!/usr/bin/env python3
"""Pre-git checks hook that runs static analysis before git commit."""
import ast
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

from hook_utils import LINT_DISABLE_PATTERNS


DEBUG_LOG = os.path.expanduser('~/.claude/hook_debug.log')


def log_debug(message):
    """Append debug message to log file for diagnosing hook issues."""
    try:
        with open(DEBUG_LOG, 'a') as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"[{timestamp}] {message}\n")
    except (IOError, OSError):
        pass  # Don't fail if can't write log


SKIP_LINT_CHECK_PATTERNS = [
    r'test.*lint.*blocker',  # Test files for the lint blocker itself
    r'\.claude/hooks/',  # Hook files (they contain patterns as strings)
]


def get_changed_files():
    """Get list of changed files from git staging area or last commit."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--no-ext-diff'],
        capture_output=True, text=True, check=False
    )
    files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    if not files:
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', '--name-only', '--no-ext-diff'],
            capture_output=True, text=True, check=False
        )
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return [f for f in files if f]


def should_skip_lint_check(file_path):
    """Check if a file should be skipped for lint disable checking."""
    for pattern in SKIP_LINT_CHECK_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True
    return False


def check_file_for_lint_disables(file_path):
    """Check a single file for lint disable patterns. Returns list of violations."""
    if should_skip_lint_check(file_path):
        return []

    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except (OSError, IOError):
        return []

    violations = []
    for pattern, description in LINT_DISABLE_PATTERNS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            violations.append((file_path, line_num, description))

    return violations


def check_changed_files_for_lint_disables(changed_files):
    """Check all changed files for lint disable patterns."""
    all_violations = []
    for file_path in changed_files:
        violations = check_file_for_lint_disables(file_path)
        all_violations.extend(violations)
    return all_violations


def run_lint_disable_check(changed_files):
    """Run lint disable check phase. Returns True if passed, False if failed."""
    print("\n" + "="*60)
    print("PHASE: LINT DISABLE CHECK")
    print("="*60)
    lint_violations = check_changed_files_for_lint_disables(changed_files)
    if lint_violations:
        print("\nLINT DISABLE VIOLATIONS FOUND:")
        for file_path, line_num, description in lint_violations:
            print(f"  {file_path}:{line_num} - {description}")
        print("\n" + "="*60)
        print("LINT DISABLE CHECK FAILED - Remove lint disable comments")
        print("Fix the actual code instead of disabling lint checks.")
        print("="*60)
        print("LINT DISABLE CHECK FAILED", file=sys.stderr)
        return False
    print("No lint disable patterns found in changed files.")
    return True


class AssertCounter(ast.NodeVisitor):
    """AST visitor that counts assert statements in a function."""

    def __init__(self):
        self.count = 0

    def visit_Assert(self, node):  # pylint: disable=invalid-name
        """Count assert statements."""
        self.count += 1
        self.generic_visit(node)


def count_asserts_in_function(func_node):
    """Count the number of assert statements in a function node."""
    counter = AssertCounter()
    counter.visit(func_node)
    return counter.count


def check_file_for_single_assert(file_path):
    """Check a test file for functions with multiple asserts.

    Returns list of violations: (file_path, line_num, function_name, assert_count)
    """
    if not file_path.endswith('.py'):
        return []

    # Only check test files
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
        # Check functions and methods
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only check test functions
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
    print("\n" + "="*60)
    print("PHASE: SINGLE ASSERT CHECK")
    print("="*60)

    all_violations = []
    for file_path in changed_files:
        violations = check_file_for_single_assert(file_path)
        all_violations.extend(violations)

    if all_violations:
        print("\nSINGLE ASSERT VIOLATIONS FOUND:")
        for file_path, line_num, func_name, count in all_violations:
            print(f"  {file_path}:{line_num} - {func_name}() has {count} asserts (should be 1)")
        print("\n" + "="*60)
        print("SINGLE ASSERT CHECK FAILED")
        print("Each test function should have exactly one assert.")
        print("Split tests with multiple asserts into separate test functions.")
        print("="*60)
        print("SINGLE ASSERT CHECK FAILED", file=sys.stderr)
        return False

    print("All test functions have single asserts.")
    return True


def run_workflow_yaml_lint(changed_files):
    """Run yamllint on changed workflow files. Returns True if passed."""
    workflow_files = [
        f for f in changed_files
        if f.startswith('.github/workflows/') and f.endswith('.yml')
    ]

    if not workflow_files:
        return True

    print("\n" + "="*60)
    print("PHASE: WORKFLOW YAML LINT")
    print("="*60)
    print(f"Checking {len(workflow_files)} workflow file(s):")
    for f in workflow_files:
        print(f"  - {f}")

    # Use consistent yamllint config matching workflow standards
    config = (
        "{extends: default, rules: {"
        "empty-lines: {max: 0, max-start: 0, max-end: 1}, "
        "key-ordering: enable, "
        "line-length: disable, "
        "new-line-at-end-of-file: enable, "
        "truthy: {allowed-values: ['true', 'false', 'on']}}}"
    )

    result = subprocess.run(
        ['yamllint', '--strict', '--config-data', config] + workflow_files,
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        print("\nYAMLLINT ERRORS:")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                print(f"  {line}")
        print("\n" + "="*60)
        print("WORKFLOW YAML LINT FAILED")
        print("="*60)
        return False

    print("All workflow files passed yamllint.")
    return True


def path_matches_pattern(file_path, pattern):
    """Check if a file path matches a glob pattern."""
    if pattern.endswith('/**'):
        prefix = pattern[:-3]
        return file_path.startswith(prefix)
    if '**' in pattern:
        regex = pattern.replace('.', r'\.').replace('**', '.*').replace('*', '[^/]*')
        return bool(re.match(f'^{regex}$', file_path))
    return fnmatch.fnmatch(file_path, pattern)


def file_matches_workflow_paths(file_path, paths):
    """Check if a file matches any of the workflow path patterns."""
    for pattern in paths:
        if path_matches_pattern(file_path, pattern):
            return True
    return False


def load_workflow_dependencies(project_dir):
    """Load workflow dependencies from etc/workflow-dependencies.json."""
    deps_file = os.path.join(project_dir, 'etc', 'workflow-dependencies.json')
    if not os.path.exists(deps_file):
        return {}
    with open(deps_file, encoding='utf-8') as f:
        return json.load(f) or {}


def is_static_analysis_step(step_name):
    """Determine if a workflow step is a static analysis check."""
    step_lower = step_name.lower()
    # Skip setup/install steps - they're not actual checks
    skip_keywords = ['install', 'setup', 'checkout', 'configure', 'set up',
                     'cloudfront', 'invalidate', 'cache', 'deploy', 'apply']
    if any(kw in step_lower for kw in skip_keywords):
        return False
    # Look for specific linting/type-checking tool names and patterns
    static_keywords = [
        'lint', 'pylint', 'mypy', 'type check', 'static analysis',
        'format check', 'fmt check', 'hadolint', 'tflint',
        'yamllint', 'jsonlint', 'terraform format'
    ]
    return any(kw in step_lower for kw in static_keywords)


def is_conditional_on_github_hosted(condition):
    """Check if a step condition depends on github-hosted runner."""
    if not condition:
        return False
    return 'github_hosted' in condition or 'github-hosted' in condition


def extract_commands_from_jobs(workflow, step_filter):
    """Extract run commands from workflow jobs that match the step filter."""
    commands = []
    jobs = workflow.get('jobs', {})
    for job_name, job in jobs.items():
        steps = job.get('steps', [])
        for step in steps:
            step_name = step.get('name', '')
            run_cmd = step.get('run', '')
            if not run_cmd:
                continue
            if not step_filter(step_name, run_cmd):
                continue
            condition = step.get('if', '')
            step_env = step.get('env', {})
            commands.append({
                'name': step_name or 'unnamed',
                'run': run_cmd,
                'conditional': is_conditional_on_github_hosted(condition),
                'job': job_name,
                'env': step_env
            })
    return commands


def extract_static_analysis_commands(workflow):
    """Extract static analysis commands from a workflow."""
    return extract_commands_from_jobs(
        workflow, lambda name, _cmd: is_static_analysis_step(name))


def get_workflow_push_paths(workflow):
    """Extract on.push.paths from a workflow file.

    Note: YAML parses 'on' as boolean True, so we check both keys.
    """
    # YAML parses 'on' as boolean True, so check both
    on_trigger = workflow.get('on') or workflow.get(True, {})
    if isinstance(on_trigger, dict):
        push_config = on_trigger.get('push', {})
        if isinstance(push_config, dict):
            return push_config.get('paths', [])
    return []


def find_workflows_by_push_paths(changed_files, workflows_dir, known_workflows):
    """Find workflows whose on.push.paths match changed files.

    This is a fallback for workflows not in workflow-dependencies.json.
    """
    known_names = {w['name'] for w in known_workflows}
    matching = []
    workflows_path = Path(workflows_dir)

    if not workflows_path.exists():
        return []

    for wf_file in workflows_path.glob('*.yml'):
        workflow_name = wf_file.stem
        if workflow_name in known_names:
            continue

        try:
            with open(wf_file, encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
        except yaml.YAMLError:
            continue

        if not workflow:
            continue

        paths = get_workflow_push_paths(workflow)
        if not paths:
            continue

        for changed_file in changed_files:
            if file_matches_workflow_paths(changed_file, paths):
                matching.append({
                    'name': workflow_name,
                    'path': str(wf_file),
                    'workflow': workflow
                })
                break

    return matching


def dedupe_workflows(workflows):
    """Remove duplicate workflows by name, preserving order."""
    seen = set()
    unique = []
    for wf in workflows:
        if wf['name'] not in seen:
            seen.add(wf['name'])
            unique.append(wf)
    return unique


def find_workflows_from_dependencies(changed_files, workflows_dir, project_dir):
    """Find workflows from workflow-dependencies.json that match changed files."""
    matching = []
    deps = load_workflow_dependencies(project_dir)

    for workflow_key, config in deps.items():
        paths = config.get('paths', [])
        if not paths:
            continue
        for changed_file in changed_files:
            if file_matches_workflow_paths(changed_file, paths):
                wf_path = Path(workflows_dir) / f'{workflow_key}.yml'
                if not wf_path.exists():
                    continue
                with open(wf_path, encoding='utf-8') as f:
                    try:
                        workflow = yaml.safe_load(f)
                    except yaml.YAMLError:
                        continue
                if workflow:
                    matching.append({
                        'name': workflow_key,
                        'path': str(wf_path),
                        'workflow': workflow
                    })
                break

    return matching


def find_matching_workflows(changed_files, workflows_dir, project_dir):
    """Find workflows whose path patterns match any of the changed files.

    First checks etc/workflow-dependencies.json for orchestrated workflows,
    then falls back to on.push.paths in workflow files for non-orchestrated
    workflows (like claude.yml).
    """
    from_deps = find_workflows_from_dependencies(
        changed_files, workflows_dir, project_dir)
    unique = dedupe_workflows(from_deps)

    # Fallback: check on.push.paths in workflow files not in workflow-dependencies
    from_push_paths = find_workflows_by_push_paths(
        changed_files, workflows_dir, unique)

    return dedupe_workflows(unique + from_push_paths)


def clean_command(cmd):
    """Clean a command by removing GitHub Actions template variables."""
    cmd = re.sub(r'\$\{\{[^}]+\}\}', '', cmd)
    lines = []
    for line in cmd.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            line = re.sub(r'\s*\\$', '', line)
            lines.append(line)
    result = ' '.join(lines)
    result = re.sub(r'\s+', ' ', result)
    return result.strip()


def clean_script(raw_cmd):
    """Clean a script by removing GitHub Actions variables and comments."""
    cleaned = re.sub(r'\$\{\{[^}]+\}\}', '', raw_cmd)
    lines = []
    for line in cleaned.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            lines.append(line)
    return '\n'.join(lines)


def build_step_env(step_env):
    """Build environment dict with step-level env vars merged with current env."""
    run_env = os.environ.copy()
    for key, value in step_env.items():
        # Clean GitHub Actions template variables from env values
        cleaned_value = re.sub(r'\$\{\{[^}]+\}\}', '', str(value)).strip()
        if cleaned_value:
            run_env[key] = cleaned_value
    return run_env


def run_command(cmd_info, workflow_name):
    """Run a single command and return True if it passes."""
    if cmd_info.get('conditional'):
        print("  [SKIP] Conditional on github-hosted")
        return True

    name = cmd_info['name']
    script = clean_script(cmd_info['run'])

    if not script.strip():
        return True

    print(f"\n[{workflow_name}] {name}")

    first_line = script.split('\n', maxsplit=1)[0].strip()
    print(f"  $ {first_line[:70]}{'...' if len(first_line) > 70 else ''}")

    result = subprocess.run(
        f"set -e\n{script}",
        shell=True,
        cwd=os.environ.get('CLAUDE_PROJECT_DIR', '.'),
        capture_output=True,
        text=True,
        check=False,
        executable='/bin/bash',
        env=build_step_env(cmd_info.get('env', {}))
    )

    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})")
        print("  Full command:")
        for line in script.split('\n'):
            print(f"    {line}")
        if result.stdout:
            print("  Stdout:")
            for out_line in result.stdout.strip().split('\n'):
                print(f"    {out_line}")
        if result.stderr:
            print("  Stderr:")
            for err_line in result.stderr.strip().split('\n'):
                print(f"    {err_line}")
        return False

    print("  PASSED")
    return True


def run_commands(commands, workflow_name):
    """Run all commands and return True if all pass."""
    all_passed = True
    for cmd_info in commands:
        if not run_command(cmd_info, workflow_name):
            all_passed = False
    return all_passed


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


def run_phase(matching_workflows, phase_name, extract_fn):
    """Run a phase of checks (static analysis or tests) on matching workflows."""
    print("\n" + "="*60)
    print(f"PHASE: {phase_name}")
    print("="*60)
    passed = True
    for wf in matching_workflows:
        commands = extract_fn(wf['workflow'])
        if commands:
            print(f"\n[{wf['name']}]")
            if not run_commands(commands, wf['name']):
                passed = False
    return passed


def main():
    """Main entry point for the pre-git checks hook."""
    command = parse_command_from_stdin()
    # Match git commit with optional flags between git and commit (e.g., git -C <path> commit)
    if not command or not re.search(r'\bgit\s+(?:[\w-]+\s+\S+\s+)*commit\b', command):
        log_debug(f"pre_git_checks: skipping - not a git commit (command: {command[:50]}...)")
        sys.exit(0)

    log_debug("pre_git_checks: starting static analysis checks")
    print("Running static analysis before git commit...")
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '.')
    os.chdir(project_dir)

    changed_files = get_changed_files()
    if not changed_files:
        print("No changed files.")
        sys.exit(0)

    print(f"Staged files ({len(changed_files)}):")
    for f in changed_files:
        print(f"  - {f}")

    if not run_lint_disable_check(changed_files):
        sys.exit(2)

    if not run_single_assert_check(changed_files):
        sys.exit(2)

    if not run_workflow_yaml_lint(changed_files):
        sys.exit(2)

    workflows_dir = os.path.join(project_dir, '.github/workflows')
    matching_workflows = find_matching_workflows(changed_files, workflows_dir, project_dir)
    if not matching_workflows:
        print("\nNo matching workflows found for additional checks.")
        sys.exit(0)

    print(f"\nMatching workflows: {[w['name'] for w in matching_workflows]}")

    static_ok = run_phase(
        matching_workflows, "STATIC ANALYSIS", extract_static_analysis_commands)
    if not static_ok:
        print("\n" + "="*60)
        print("STATIC ANALYSIS FAILED - Fix issues before committing")
        print("="*60)
        print("STATIC ANALYSIS FAILED - Fix issues before committing", file=sys.stderr)
        sys.exit(2)

    print("\n" + "="*60)
    print("ALL CHECKS PASSED")
    print("="*60)
    sys.exit(0)


if __name__ == '__main__':
    main()
