#!/usr/bin/env python3
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def get_changed_files():
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True
    )
    files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    if not files:
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', '--name-only'],
            capture_output=True, text=True
        )
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return [f for f in files if f]


def path_matches_pattern(file_path, pattern):
    if pattern.endswith('/**'):
        prefix = pattern[:-3]
        return file_path.startswith(prefix)
    if '**' in pattern:
        regex = pattern.replace('.', r'\.').replace('**', '.*').replace('*', '[^/]*')
        return bool(re.match(f'^{regex}$', file_path))
    return fnmatch.fnmatch(file_path, pattern)


def file_matches_workflow_paths(file_path, paths):
    for pattern in paths:
        if path_matches_pattern(file_path, pattern):
            return True
    return False


def get_workflow_paths(workflow):
    paths = []
    on_section = workflow.get('on') or workflow.get(True) or {}
    if isinstance(on_section, dict):
        push_section = on_section.get('push', {})
        if isinstance(push_section, dict):
            paths = push_section.get('paths', [])
    return paths


def is_pre_push_check_step(step_name, run_cmd):
    step_lower = step_name.lower()
    static_keywords = [
        'lint', 'pylint', 'mypy', 'type check', 'static',
        'format check', 'fmt', 'validate', 'hadolint', 'tflint',
        'yamllint', 'jsonlint'
    ]
    if any(kw in step_lower for kw in static_keywords):
        return True
    if 'pre_deployment' in run_cmd or 'pre-deployment' in step_lower:
        return True
    if 'unit test' in step_lower:
        return True
    return False


def is_conditional_on_github_hosted(condition):
    if not condition:
        return False
    return 'github_hosted' in condition or 'github-hosted' in condition


def is_static_analysis_job(job_name):
    job_lower = job_name.lower().replace('-', '_').replace(' ', '_')
    return 'static' in job_lower or 'analysis' in job_lower or 'lint' in job_lower


def is_test_job(job_name):
    job_lower = job_name.lower().replace('-', '_').replace(' ', '_')
    return 'test' in job_lower or 'unit' in job_lower or 'integration' in job_lower


def extract_commands_from_jobs(workflow, job_filter):
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
            commands.append({
                'name': step_name or 'unnamed',
                'run': run_cmd,
                'conditional': is_conditional_on_github_hosted(condition),
                'job': job_name
            })
    return commands


def extract_static_analysis_commands(workflow):
    return extract_commands_from_jobs(workflow, is_static_analysis_job)


def extract_pre_deployment_test_commands(workflow):
    return extract_commands_from_jobs(workflow, is_test_job)


def find_matching_workflows(changed_files, workflows_dir):
    matching = []
    workflow_files = list(Path(workflows_dir).glob('*.yml'))
    for wf_path in workflow_files:
        with open(wf_path) as f:
            try:
                workflow = yaml.safe_load(f)
            except yaml.YAMLError:
                continue
        if not workflow:
            continue
        paths = get_workflow_paths(workflow)
        if not paths:
            continue
        for changed_file in changed_files:
            if file_matches_workflow_paths(changed_file, paths):
                matching.append({
                    'name': wf_path.stem,
                    'path': str(wf_path),
                    'workflow': workflow
                })
    seen = set()
    unique = []
    for m in matching:
        if m['name'] not in seen:
            seen.add(m['name'])
            unique.append(m)
    return unique


def clean_command(cmd):
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
    cleaned = re.sub(r'\$\{\{[^}]+\}\}', '', raw_cmd)
    lines = []
    for line in cleaned.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            lines.append(line)
    return '\n'.join(lines)


def run_command(cmd_info, workflow_name):
    if cmd_info.get('conditional'):
        print(f"  [SKIP] Conditional on github-hosted")
        return True

    name = cmd_info['name']
    raw_cmd = cmd_info['run']
    script = clean_script(raw_cmd)

    if not script.strip():
        return True

    print(f"\n[{workflow_name}] {name}")

    first_line = script.split('\n')[0].strip()
    print(f"  $ {first_line[:70]}{'...' if len(first_line) > 70 else ''}")

    result = subprocess.run(
        script,
        shell=True,
        cwd=os.environ.get('CLAUDE_PROJECT_DIR', '.'),
        capture_output=True,
        text=True,
        executable='/bin/bash'
    )

    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})")
        if result.stdout:
            for out_line in result.stdout.strip().split('\n')[-15:]:
                print(f"    {out_line}")
        if result.stderr:
            for err_line in result.stderr.strip().split('\n')[-10:]:
                print(f"    {err_line}")
        return False

    print(f"  PASSED")
    return True


def run_commands(commands, workflow_name):
    all_passed = True
    for cmd_info in commands:
        if not run_command(cmd_info, workflow_name):
            all_passed = False
    return all_passed


def main():
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        command = data.get('tool_input', {}).get('command', '')
    except json.JSONDecodeError:
        command = ''

    if not command:
        sys.exit(0)

    if not re.match(r'^git\s+(commit|push)', command):
        sys.exit(0)

    print("Running static analysis before git operation...")

    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '.')
    os.chdir(project_dir)

    changed_files = get_changed_files()
    if not changed_files:
        print("No changed files.")
        sys.exit(0)

    print(f"Changed files: {changed_files}")

    workflows_dir = os.path.join(project_dir, '.github/workflows')
    matching_workflows = find_matching_workflows(changed_files, workflows_dir)

    if not matching_workflows:
        print("No matching workflows found.")
        sys.exit(0)

    print(f"Matching workflows: {[w['name'] for w in matching_workflows]}")

    print("\n" + "="*60)
    print("PHASE 1: STATIC ANALYSIS")
    print("="*60)

    static_passed = True
    for wf in matching_workflows:
        commands = extract_static_analysis_commands(wf['workflow'])
        if commands:
            print(f"\n[{wf['name']}]")
            if not run_commands(commands, wf['name']):
                static_passed = False

    if not static_passed:
        print("\n" + "="*60)
        print("STATIC ANALYSIS FAILED - Fix issues before committing")
        print("="*60)
        print("STATIC ANALYSIS FAILED - Fix issues before committing", file=sys.stderr)
        sys.exit(2)

    print("\n" + "="*60)
    print("PHASE 2: PRE-DEPLOYMENT TESTS")
    print("="*60)

    tests_passed = True
    for wf in matching_workflows:
        commands = extract_pre_deployment_test_commands(wf['workflow'])
        if commands:
            print(f"\n[{wf['name']}]")
            if not run_commands(commands, wf['name']):
                tests_passed = False

    if not tests_passed:
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
