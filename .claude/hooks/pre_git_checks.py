#!/usr/bin/env python3
"""Pre-git checks hook that runs static analysis before git commit/push operations."""
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

from hook_utils import LINT_DISABLE_PATTERNS


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
    """Load workflow dependencies from etc/workflow-dependencies.yml."""
    deps_file = os.path.join(project_dir, 'etc', 'workflow-dependencies.yml')
    if not os.path.exists(deps_file):
        return {}
    with open(deps_file, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def is_pre_push_check_step(step_name, run_cmd):
    """Determine if a workflow step is a pre-push check (linting, testing, etc.)."""
    step_lower = step_name.lower()
    # Skip setup/install steps - they're not actual checks
    skip_keywords = ['install', 'setup', 'checkout', 'configure', 'set up']
    if any(kw in step_lower for kw in skip_keywords):
        return False
    static_keywords = [
        'lint', 'pylint', 'mypy', 'type check', 'static',
        'format check', 'fmt', 'validate', 'hadolint', 'tflint',
        'yamllint', 'jsonlint'
    ]
    if any(kw in step_lower for kw in static_keywords):
        return True
    # Only run unit tests locally, skip integration tests (they require AWS resources)
    if 'pre_deployment/unit' in run_cmd or 'pre-deployment/unit' in run_cmd:
        return True
    if 'unit test' in step_lower:
        return True
    return False


def is_conditional_on_github_hosted(condition):
    """Check if a step condition depends on github-hosted runner."""
    if not condition:
        return False
    return 'github_hosted' in condition or 'github-hosted' in condition


def is_static_analysis_job(job_name):
    """Check if a job name indicates a static analysis job."""
    job_lower = job_name.lower().replace('-', '_').replace(' ', '_')
    return 'static' in job_lower or 'analysis' in job_lower or 'lint' in job_lower


def is_test_job(job_name):
    """Check if a job name indicates a test job."""
    job_lower = job_name.lower().replace('-', '_').replace(' ', '_')
    return 'test' in job_lower or 'unit' in job_lower or 'integration' in job_lower


def extract_commands_from_jobs(workflow, job_filter):
    """Extract run commands from workflow jobs that match the filter."""
    commands = []
    jobs = workflow.get('jobs', {})
    for job_name, job in jobs.items():
        if not job_filter(job_name):
            continue
        steps = job.get('steps', [])
        for step in steps:
            step_name = step.get('name', '')
            run_cmd = step.get('run', '')
            if not run_cmd:
                continue
            if not is_pre_push_check_step(step_name, run_cmd):
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
    return extract_commands_from_jobs(workflow, is_static_analysis_job)


def extract_pre_deployment_test_commands(workflow):
    """Extract pre-deployment test commands from a workflow."""
    return extract_commands_from_jobs(workflow, is_test_job)


def find_matching_workflows(changed_files, workflows_dir, project_dir):
    """Find workflows whose path patterns match any of the changed files.

    Uses etc/workflow-dependencies.yml for path mappings instead of
    on.push.paths in workflow files (since orchestrator handles push triggers).
    """
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

    seen = set()
    unique = []
    for m in matching:
        if m['name'] not in seen:
            seen.add(m['name'])
            unique.append(m)
    return unique


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
    try:
        data = json.loads(input_data)
        return data.get('tool_input', {}).get('command', '')
    except json.JSONDecodeError:
        return ''


def get_current_branch():
    """Get the current git branch name."""
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def get_default_branch():
    """Get the default branch (main or master)."""
    for branch in ['main', 'master']:
        result = subprocess.run(
            ['git', 'rev-parse', '--verify', f'refs/heads/{branch}'],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return branch
    return 'main'


def count_commits_ahead_of_base(base_branch):
    """Count how many commits current branch is ahead of base branch."""
    current = get_current_branch()
    if not current or current == base_branch:
        return 0

    result = subprocess.run(
        ['git', 'rev-list', '--count', f'{base_branch}..HEAD'],
        capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def check_squash_commit_required(command):
    """Check if push has multiple commits and require squash. Returns True if OK."""
    if not re.search(r'\bgit\s+push\b', command):
        return True

    current_branch = get_current_branch()
    base_branch = get_default_branch()

    if current_branch == base_branch:
        return True

    commits_ahead = count_commits_ahead_of_base(base_branch)

    if commits_ahead > 1:
        print("\n" + "="*60)
        print("BLOCKED: SQUASH COMMITS REQUIRED")
        print("="*60)
        print(f"\nBranch '{current_branch}' has {commits_ahead} commits ahead of '{base_branch}'.")
        print("You must squash to a single commit before pushing.")
        print("\nTo squash commits, run:")
        print(f"  git rebase -i {base_branch}")
        print("  # Mark all commits except the first as 'squash' or 's'")
        print(f"  # Or: git reset --soft $(git merge-base HEAD {base_branch}) && git commit")
        print("="*60)
        return False

    return True


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
    if not command or not re.search(r'\bgit\s+(commit|push)\b', command):
        sys.exit(0)

    if not check_squash_commit_required(command):
        sys.exit(2)

    print("Running static analysis before git operation...")
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

    tests_ok = run_phase(
        matching_workflows, "PRE-DEPLOYMENT TESTS", extract_pre_deployment_test_commands)
    if not tests_ok:
        print("\n" + "="*60)
        print("PRE-DEPLOYMENT TESTS FAILED - Fix issues before committing")
        print("="*60)
        print("PRE-DEPLOYMENT TESTS FAILED - Fix issues before committing", file=sys.stderr)
        sys.exit(2)

    print("\n" + "="*60)
    print("ALL CHECKS PASSED")
    print("="*60)
    sys.exit(0)


if __name__ == '__main__':
    main()
