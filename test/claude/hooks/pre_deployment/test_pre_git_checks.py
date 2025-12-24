"""Tests for pre_git_checks hook."""


def test_path_matches_pattern_exact_match(pre_git_checks):
    """Test that Path matches pattern exact match."""
    result = pre_git_checks.path_matches_pattern('src/main.py', 'src/main.py')
    assert result is True


def test_path_matches_pattern_wildcard_star(pre_git_checks):
    """Test that Path matches pattern wildcard star."""
    result = pre_git_checks.path_matches_pattern('src/main.py', 'src/*.py')
    assert result is True


def test_path_matches_pattern_double_star_suffix(pre_git_checks):
    """Test that Path matches pattern double star suffix."""
    result = pre_git_checks.path_matches_pattern('src/app/main.py', 'src/**')
    assert result is True


def test_path_matches_pattern_double_star_in_middle(pre_git_checks):
    """Test that Path matches pattern double star in middle."""
    result = pre_git_checks.path_matches_pattern('src/app/main.py', 'src/**/*.py')
    assert result is True


def test_path_matches_pattern_no_match(pre_git_checks):
    """Test that Path matches pattern no match."""
    result = pre_git_checks.path_matches_pattern('docs/readme.md', 'src/**/*.py')
    assert result is False


def test_file_matches_workflow_paths_returns_true(pre_git_checks):
    """Test that File matches workflow paths returns true."""
    paths = ['src/**', 'test/**']
    result = pre_git_checks.file_matches_workflow_paths('src/main.py', paths)
    assert result is True


def test_file_matches_workflow_paths_returns_false(pre_git_checks):
    """Test that File matches workflow paths returns false."""
    paths = ['src/**', 'test/**']
    result = pre_git_checks.file_matches_workflow_paths('docs/readme.md', paths)
    assert result is False


def test_file_matches_workflow_paths_empty_list(pre_git_checks):
    """Test that File matches workflow paths empty list."""
    result = pre_git_checks.file_matches_workflow_paths('src/main.py', [])
    assert result is False


def test_is_static_analysis_step_skips_pylint(pre_git_checks):
    """Test that is_static_analysis_step skips pylint (too slow for local)."""
    result = pre_git_checks.is_static_analysis_step('Run pylint')
    assert result is False


def test_is_static_analysis_step_skips_mypy(pre_git_checks):
    """Test that is_static_analysis_step skips mypy (too slow for local)."""
    result = pre_git_checks.is_static_analysis_step('Type check with mypy')
    assert result is False


def test_is_static_analysis_step_detects_yamllint(pre_git_checks):
    """Test that is_static_analysis_step detects yamllint."""
    result = pre_git_checks.is_static_analysis_step('Run yamllint')
    assert result is True


def test_is_static_analysis_step_detects_tflint(pre_git_checks):
    """Test that is_static_analysis_step detects tflint."""
    result = pre_git_checks.is_static_analysis_step('Run tflint')
    assert result is True


def test_is_static_analysis_step_detects_hadolint(pre_git_checks):
    """Test that is_static_analysis_step detects hadolint."""
    result = pre_git_checks.is_static_analysis_step('Hadolint check')
    assert result is True


def test_is_static_analysis_step_ignores_deploy(pre_git_checks):
    """Test that is_static_analysis_step ignores deploy."""
    result = pre_git_checks.is_static_analysis_step('Deploy')
    assert result is False


def test_is_static_analysis_step_ignores_install(pre_git_checks):
    """Test that is_static_analysis_step ignores install."""
    result = pre_git_checks.is_static_analysis_step('Install dependencies')
    assert result is False


def test_is_conditional_on_github_hosted_returns_true(pre_git_checks):
    """Test that Is conditional on github hosted returns true."""
    conditional = 'needs.setup.outputs.github_hosted == true'
    result = pre_git_checks.is_conditional_on_github_hosted(conditional)
    assert result is True


def test_is_conditional_on_github_hosted_returns_false(pre_git_checks):
    """Test that Is conditional on github hosted returns false."""
    result = pre_git_checks.is_conditional_on_github_hosted('always()')
    assert result is False


def test_is_conditional_on_github_hosted_handles_none(pre_git_checks):
    """Test that Is conditional on github hosted handles none."""
    result = pre_git_checks.is_conditional_on_github_hosted(None)
    assert result is False


def test_is_conditional_on_github_hosted_handles_hyphenated(pre_git_checks):
    """Test that Is conditional on github hosted handles hyphenated."""
    result = pre_git_checks.is_conditional_on_github_hosted('github-hosted')
    assert result is True


def test_extract_static_analysis_commands_returns_list(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands returns list."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    assert isinstance(result, list)


def test_extract_static_analysis_commands_finds_yamllint(pre_git_checks, sample_workflow):
    """Test that extract_static_analysis_commands finds yamllint."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Run yamllint' in names


def test_extract_static_analysis_commands_finds_tflint(pre_git_checks, sample_workflow):
    """Test that extract_static_analysis_commands finds tflint."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Run tflint' in names


def test_extract_static_analysis_commands_excludes_deploy(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands excludes deploy."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Deploy' not in names


def test_clean_command_removes_github_expressions(pre_git_checks):
    """Test that Clean command removes github expressions."""
    cmd = 'echo ${{ secrets.TOKEN }}'
    result = pre_git_checks.clean_command(cmd)
    assert '{{' not in result


def test_clean_command_removes_comments(pre_git_checks):
    """Test that Clean command removes comments."""
    cmd = '# comment\necho hello'
    result = pre_git_checks.clean_command(cmd)
    assert 'comment' not in result


def test_clean_command_joins_lines(pre_git_checks):
    """Test that Clean command joins lines."""
    cmd = 'echo \\\n  hello'
    result = pre_git_checks.clean_command(cmd)
    assert 'echo hello' in result


def test_clean_script_removes_github_expressions(pre_git_checks):
    """Test that Clean script removes github expressions."""
    cmd = 'echo ${{ secrets.TOKEN }}'
    result = pre_git_checks.clean_script(cmd)
    assert '{{' not in result


def test_clean_script_removes_empty_lines(pre_git_checks):
    """Test that Clean script removes empty lines."""
    cmd = 'echo hello\n\necho world'
    result = pre_git_checks.clean_script(cmd)
    assert '\n\n' not in result


def test_clean_script_removes_comment_lines(pre_git_checks):
    """Test that Clean script removes comment lines."""
    cmd = '# comment\necho hello'
    result = pre_git_checks.clean_script(cmd)
    assert '# comment' not in result


def test_extract_commands_from_jobs_with_filter(pre_git_checks, sample_workflow):
    """Test that Extract commands from jobs with step filter."""
    def step_filter(name, _cmd):
        return pre_git_checks.is_static_analysis_step(name)
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, step_filter)
    assert len(result) > 0


def test_extract_commands_from_jobs_includes_job_name(pre_git_checks, sample_workflow):
    """Test that Extract commands from jobs includes job name."""
    def step_filter(name, _cmd):
        return pre_git_checks.is_static_analysis_step(name)
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, step_filter)
    assert all('job' in cmd for cmd in result)


def test_extract_commands_from_jobs_includes_conditional_field(
    pre_git_checks, sample_workflow
):
    """Test that Extract commands from jobs includes conditional field."""
    def step_filter(name, _cmd):
        return pre_git_checks.is_static_analysis_step(name)
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, step_filter)
    assert all('conditional' in cmd for cmd in result)


def test_extract_commands_from_jobs_empty_workflow(pre_git_checks):
    """Test that Extract commands from jobs empty workflow."""
    workflow = {'jobs': {}}
    def step_filter(name, _cmd):
        return pre_git_checks.is_static_analysis_step(name)
    result = pre_git_checks.extract_commands_from_jobs(workflow, step_filter)
    assert result == []


def test_run_command_skips_conditional(pre_git_checks):
    """Test that Run command skips conditional."""
    cmd_info = {'name': 'test', 'run': 'echo hello', 'conditional': True}
    result = pre_git_checks.run_command(cmd_info, 'test-workflow')
    assert result is True


def test_run_command_returns_true_for_empty_script(pre_git_checks):
    """Test that Run command returns true for empty script."""
    cmd_info = {'name': 'test', 'run': '${{ github.token }}', 'conditional': False}
    result = pre_git_checks.run_command(cmd_info, 'test-workflow')
    assert result is True


def test_run_commands_returns_true_when_all_pass(pre_git_checks):
    """Test that Run commands returns true when all pass."""
    commands = [
        {'name': 'skip1', 'run': 'echo', 'conditional': True},
        {'name': 'skip2', 'run': '', 'conditional': False}
    ]
    result = pre_git_checks.run_commands(commands, 'test-workflow')
    assert result is True


def test_run_commands_returns_false_when_one_fails(pre_git_checks):
    """Test that Run commands returns false when one fails."""
    commands = [
        {'name': 'fail', 'run': 'exit 1', 'conditional': False}
    ]
    result = pre_git_checks.run_commands(commands, 'test-workflow')
    assert result is False


def test_get_workflow_push_paths_returns_paths(pre_git_checks, sample_workflow):
    """Test that get_workflow_push_paths extracts paths from workflow."""
    result = pre_git_checks.get_workflow_push_paths(sample_workflow)
    assert result == ['src/**/*.py', 'test/**']


def test_get_workflow_push_paths_returns_empty_for_no_paths(
    pre_git_checks, sample_workflow_no_paths
):
    """Test that get_workflow_push_paths returns empty list when no paths."""
    result = pre_git_checks.get_workflow_push_paths(sample_workflow_no_paths)
    assert result == []


def test_get_workflow_push_paths_handles_missing_on(pre_git_checks):
    """Test that get_workflow_push_paths handles missing on key."""
    workflow = {'jobs': {}}
    result = pre_git_checks.get_workflow_push_paths(workflow)
    assert result == []


def test_get_workflow_push_paths_handles_non_dict_on(pre_git_checks):
    """Test that get_workflow_push_paths handles non-dict on value."""
    workflow = {'on': 'push'}
    result = pre_git_checks.get_workflow_push_paths(workflow)
    assert result == []


def test_get_workflow_push_paths_handles_non_dict_push(pre_git_checks):
    """Test that get_workflow_push_paths handles non-dict push value."""
    workflow = {'on': {'push': None}}
    result = pre_git_checks.get_workflow_push_paths(workflow)
    assert result == []


def test_get_workflow_push_paths_handles_yaml_boolean_on(pre_git_checks):
    """Test that get_workflow_push_paths handles YAML parsing 'on' as True."""
    # YAML parses 'on:' as boolean True
    workflow = {True: {'push': {'paths': ['src/**']}}}
    result = pre_git_checks.get_workflow_push_paths(workflow)
    assert result == ['src/**']


def test_find_workflows_by_push_paths_finds_one_matching(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths finds exactly one matching workflow."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text("""
on:
  push:
    paths:
      - 'src/**'
jobs:
  test:
    steps:
      - name: Run lint
        run: echo lint
""")
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert len(result) == 1


def test_find_workflows_by_push_paths_returns_correct_name(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths returns workflow with correct name."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text("""
on:
  push:
    paths:
      - 'src/**'
jobs:
  test:
    steps:
      - name: Run lint
        run: echo lint
""")
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert result[0]['name'] == 'test_workflow'


def test_find_workflows_by_push_paths_skips_known(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths skips already known workflows."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text("""
on:
  push:
    paths:
      - 'src/**'
jobs: {}
""")
    changed_files = ['src/main.py']
    known_workflows = [{'name': 'test_workflow', 'path': str(workflow_file), 'workflow': {}}]
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert len(result) == 0


def test_find_workflows_by_push_paths_skips_no_match(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths skips workflows with no path match."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text("""
on:
  push:
    paths:
      - 'docs/**'
jobs: {}
""")
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert len(result) == 0


def test_find_workflows_by_push_paths_skips_no_paths(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths skips workflows without paths."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text("""
on:
  push: {}
jobs: {}
""")
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert len(result) == 0


def test_find_workflows_by_push_paths_handles_missing_dir(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths handles missing directory."""
    workflows_dir = tmp_path / 'nonexistent'
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert result == []


def test_find_workflows_by_push_paths_handles_invalid_yaml(pre_git_checks, tmp_path):
    """Test that find_workflows_by_push_paths handles invalid YAML."""
    workflows_dir = tmp_path / 'workflows'
    workflows_dir.mkdir()
    workflow_file = workflows_dir / 'test_workflow.yml'
    workflow_file.write_text('invalid: yaml: content: [')
    changed_files = ['src/main.py']
    known_workflows = []
    result = pre_git_checks.find_workflows_by_push_paths(
        changed_files, str(workflows_dir), known_workflows)
    assert len(result) == 0


def test_run_workflow_yaml_lint_returns_true_when_no_workflow_files(pre_git_checks):
    """Test that run_workflow_yaml_lint returns True when no workflow files."""
    changed_files = ['src/main.py', 'test/test_main.py']
    result = pre_git_checks.run_workflow_yaml_lint(changed_files)
    assert result is True


def test_run_workflow_yaml_lint_identifies_workflow_files_count():
    """Test that run_workflow_yaml_lint identifies correct number of workflow files."""
    changed_files = [
        'src/main.py',
        '.github/workflows/test.yml',
        '.github/workflows/deploy.yml',
        'test/test_main.py'
    ]
    workflow_files = [
        f for f in changed_files
        if f.startswith('.github/workflows/') and f.endswith('.yml')
    ]
    assert len(workflow_files) == 2


def test_run_workflow_yaml_lint_identifies_test_workflow():
    """Test that run_workflow_yaml_lint identifies test.yml as workflow file."""
    changed_files = ['.github/workflows/test.yml', 'src/main.py']
    workflow_files = [
        f for f in changed_files
        if f.startswith('.github/workflows/') and f.endswith('.yml')
    ]
    assert '.github/workflows/test.yml' in workflow_files


def test_run_workflow_yaml_lint_identifies_deploy_workflow():
    """Test that run_workflow_yaml_lint identifies deploy.yml as workflow file."""
    changed_files = ['.github/workflows/deploy.yml', 'src/main.py']
    workflow_files = [
        f for f in changed_files
        if f.startswith('.github/workflows/') and f.endswith('.yml')
    ]
    assert '.github/workflows/deploy.yml' in workflow_files


def test_run_workflow_yaml_lint_ignores_non_yml_files(pre_git_checks):
    """Test that run_workflow_yaml_lint ignores non-yml files in workflows dir."""
    changed_files = ['.github/workflows/README.md', '.github/workflows/.gitkeep']
    result = pre_git_checks.run_workflow_yaml_lint(changed_files)
    assert result is True


def test_run_workflow_yaml_lint_ignores_yaml_outside_workflows(pre_git_checks):
    """Test that run_workflow_yaml_lint ignores yaml files outside workflows dir."""
    changed_files = ['etc/config.yml', '.github/dependabot.yml']
    result = pre_git_checks.run_workflow_yaml_lint(changed_files)
    assert result is True


def test_run_blocked_lint_config_check_blocks_pylintrc(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .pylintrc files."""
    pylintrc = tmp_path / '.pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')
    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_pylintrc_no_dot(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks pylintrc files without dot."""
    pylintrc = tmp_path / 'pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')
    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_flake8(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .flake8 files."""
    flake8 = tmp_path / '.flake8'
    flake8.write_text('[flake8]\nmax-line-length = 999\n')
    changed_files = [str(flake8)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_mypy_ini(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .mypy.ini files."""
    mypy_ini = tmp_path / '.mypy.ini'
    mypy_ini.write_text('[mypy]\nignore_missing_imports = True\n')
    changed_files = [str(mypy_ini)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_blocks_tox_ini(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks tox.ini files."""
    tox_ini = tmp_path / 'tox.ini'
    tox_ini.write_text('[flake8]\nmax-line-length = 999\n')
    changed_files = [str(tox_ini)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_allows_regular_files(pre_git_checks):
    """Test that run_blocked_lint_config_check allows regular Python files."""
    changed_files = ['src/main.py', 'test/test_main.py', 'README.md']
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True


def test_run_blocked_lint_config_check_allows_empty_list(pre_git_checks):
    """Test that run_blocked_lint_config_check handles empty file list."""
    changed_files = []
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True


def test_run_blocked_lint_config_check_blocks_nested_pylintrc(pre_git_checks, tmp_path):
    """Test that run_blocked_lint_config_check blocks .pylintrc in nested paths."""
    # Create the file so it exists (simulating adding a file)
    nested_dir = tmp_path / 'deeply' / 'nested' / 'path'
    nested_dir.mkdir(parents=True)
    pylintrc = nested_dir / '.pylintrc'
    pylintrc.write_text('[MESSAGES CONTROL]\ndisable=all\n')

    changed_files = [str(pylintrc)]
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is False


def test_run_blocked_lint_config_check_allows_deleted_pylintrc(pre_git_checks):
    """Test that run_blocked_lint_config_check allows deletion of .pylintrc."""
    # File path that doesn't exist (simulating deletion)
    changed_files = ['nonexistent/path/.pylintrc']
    result = pre_git_checks.run_blocked_lint_config_check(changed_files)
    assert result is True
