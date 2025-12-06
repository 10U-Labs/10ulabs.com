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


def test_get_workflow_paths_from_push_section(pre_git_checks, sample_workflow):
    """Test that Get workflow paths from push section."""
    result = pre_git_checks.get_workflow_paths(sample_workflow)
    assert 'src/**/*.py' in result


def test_get_workflow_paths_returns_empty_for_no_paths(pre_git_checks, sample_workflow_no_paths):
    """Test that Get workflow paths returns empty for no paths."""
    result = pre_git_checks.get_workflow_paths(sample_workflow_no_paths)
    assert result == []


def test_get_workflow_paths_handles_missing_on_section(pre_git_checks):
    """Test that Get workflow paths handles missing on section."""
    workflow = {}
    result = pre_git_checks.get_workflow_paths(workflow)
    assert result == []


def test_is_pre_push_check_step_detects_lint(pre_git_checks):
    """Test that Is pre push check step detects lint."""
    result = pre_git_checks.is_pre_push_check_step('Run pylint', 'pylint src/')
    assert result is True


def test_is_pre_push_check_step_detects_mypy(pre_git_checks):
    """Test that Is pre push check step detects mypy."""
    result = pre_git_checks.is_pre_push_check_step('Type check with mypy', 'mypy src/')
    assert result is True


def test_is_pre_push_check_step_detects_pre_deployment_unit(pre_git_checks):
    """Test that Is pre push check step detects pre deployment unit tests."""
    result = pre_git_checks.is_pre_push_check_step('Test', 'pytest test/pre_deployment/unit/')
    assert result is True


def test_is_pre_push_check_step_skips_pre_deployment_integration(pre_git_checks):
    """Test that Is pre push check step skips pre deployment integration tests."""
    cmd = 'pytest test/pre_deployment/integration/'
    result = pre_git_checks.is_pre_push_check_step('Test', cmd)
    assert result is False


def test_is_pre_push_check_step_detects_unit_test(pre_git_checks):
    """Test that Is pre push check step detects unit test."""
    result = pre_git_checks.is_pre_push_check_step('Run unit tests', 'pytest')
    assert result is True


def test_is_pre_push_check_step_ignores_deploy(pre_git_checks):
    """Test that Is pre push check step ignores deploy."""
    result = pre_git_checks.is_pre_push_check_step('Deploy', 'deploy.sh')
    assert result is False


def test_is_pre_push_check_step_detects_validate(pre_git_checks):
    """Test that Is pre push check step detects validate."""
    result = pre_git_checks.is_pre_push_check_step('Validate config', 'validate.sh')
    assert result is True


def test_is_pre_push_check_step_detects_tflint(pre_git_checks):
    """Test that Is pre push check step detects tflint."""
    result = pre_git_checks.is_pre_push_check_step('Run tflint', 'tflint')
    assert result is True


def test_is_pre_push_check_step_detects_hadolint(pre_git_checks):
    """Test that Is pre push check step detects hadolint."""
    result = pre_git_checks.is_pre_push_check_step('Hadolint check', 'hadolint Dockerfile')
    assert result is True


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


def test_is_static_analysis_job_detects_static(pre_git_checks):
    """Test that Is static analysis job detects static."""
    result = pre_git_checks.is_static_analysis_job('static-analysis')
    assert result is True


def test_is_static_analysis_job_detects_lint(pre_git_checks):
    """Test that Is static analysis job detects lint."""
    result = pre_git_checks.is_static_analysis_job('lint-python')
    assert result is True


def test_is_static_analysis_job_returns_false_for_test(pre_git_checks):
    """Test that Is static analysis job returns false for test."""
    result = pre_git_checks.is_static_analysis_job('unit-tests')
    assert result is False


def test_is_static_analysis_job_handles_underscores(pre_git_checks):
    """Test that Is static analysis job handles underscores."""
    result = pre_git_checks.is_static_analysis_job('static_analysis')
    assert result is True


def test_is_test_job_detects_test(pre_git_checks):
    """Test that Is job detects test."""
    result = pre_git_checks.is_test_job('unit-tests')
    assert result is True


def test_is_test_job_detects_integration(pre_git_checks):
    """Test that Is job detects integration."""
    result = pre_git_checks.is_test_job('integration-tests')
    assert result is True


def test_is_test_job_returns_false_for_deploy(pre_git_checks):
    """Test that Is job returns false for deploy."""
    result = pre_git_checks.is_test_job('deploy')
    assert result is False


def test_extract_static_analysis_commands_returns_list(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands returns list."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    assert isinstance(result, list)


def test_extract_static_analysis_commands_finds_pylint(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands finds pylint."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Run pylint' in names


def test_extract_static_analysis_commands_finds_mypy(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands finds mypy."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Run mypy' in names


def test_extract_static_analysis_commands_excludes_deploy(pre_git_checks, sample_workflow):
    """Test that Extract static analysis commands excludes deploy."""
    result = pre_git_checks.extract_static_analysis_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Deploy' not in names


def test_extract_pre_deployment_test_commands_returns_list(pre_git_checks, sample_workflow):
    """Test that Extract pre deployment commands returns list."""
    result = pre_git_checks.extract_pre_deployment_test_commands(sample_workflow)
    assert isinstance(result, list)


def test_extract_pre_deployment_test_commands_finds_unit_tests(pre_git_checks, sample_workflow):
    """Test that Extract pre deployment commands finds unit tests."""
    result = pre_git_checks.extract_pre_deployment_test_commands(sample_workflow)
    names = [cmd['name'] for cmd in result]
    assert 'Run unit tests' in names


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
    """Test that Extract commands from jobs with filter."""
    job_filter = pre_git_checks.is_static_analysis_job
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, job_filter)
    assert len(result) > 0


def test_extract_commands_from_jobs_includes_job_name(pre_git_checks, sample_workflow):
    """Test that Extract commands from jobs includes job name."""
    job_filter = pre_git_checks.is_static_analysis_job
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, job_filter)
    assert all('job' in cmd for cmd in result)


def test_extract_commands_from_jobs_includes_conditional_field(
    pre_git_checks, sample_workflow
):
    """Test that Extract commands from jobs includes conditional field."""
    job_filter = pre_git_checks.is_static_analysis_job
    result = pre_git_checks.extract_commands_from_jobs(sample_workflow, job_filter)
    assert all('conditional' in cmd for cmd in result)


def test_extract_commands_from_jobs_empty_workflow(pre_git_checks):
    """Test that Extract commands from jobs empty workflow."""
    workflow = {'jobs': {}}
    job_filter = pre_git_checks.is_static_analysis_job
    result = pre_git_checks.extract_commands_from_jobs(workflow, job_filter)
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
