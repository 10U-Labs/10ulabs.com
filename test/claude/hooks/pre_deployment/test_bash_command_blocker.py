import re


def test_blocked_patterns_contains_cdk_deploy(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    cdk_deploy_pattern_exists = any('cdk' in p and 'deploy' in p for p in patterns)
    assert cdk_deploy_pattern_exists


def test_blocked_patterns_contains_cdk_destroy(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    cdk_destroy_pattern_exists = any('cdk' in p and 'destroy' in p for p in patterns)
    assert cdk_destroy_pattern_exists


def test_blocked_patterns_contains_terraform_apply(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    terraform_apply_pattern_exists = any('terraform' in p and 'apply' in p for p in patterns)
    assert terraform_apply_pattern_exists


def test_blocked_patterns_contains_terraform_destroy(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    terraform_destroy_pattern_exists = any('terraform' in p and 'destroy' in p for p in patterns)
    assert terraform_destroy_pattern_exists


def test_blocked_patterns_contains_gh_run_watch(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    gh_run_watch_pattern_exists = any('gh' in p and 'run' in p and 'watch' in p for p in patterns)
    assert gh_run_watch_pattern_exists


def test_blocked_patterns_contains_sleep(bash_command_blocker):
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    sleep_pattern_exists = any('sleep' in p for p in patterns)
    assert sleep_pattern_exists


def test_cdk_deploy_command_matches_pattern():
    command = 'cdk deploy --all'
    pattern = r'\bcdk\s+deploy\b'
    cdk_deploy_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert cdk_deploy_command_matches


def test_cdk_destroy_command_matches_pattern():
    command = 'cdk destroy MyStack'
    pattern = r'\bcdk\s+destroy\b'
    cdk_destroy_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert cdk_destroy_command_matches


def test_terraform_apply_command_matches_pattern():
    command = 'terraform apply -auto-approve'
    pattern = r'\bterraform\s+apply\b'
    terraform_apply_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert terraform_apply_command_matches


def test_terraform_destroy_command_matches_pattern():
    command = 'terraform destroy -auto-approve'
    pattern = r'\bterraform\s+destroy\b'
    terraform_destroy_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert terraform_destroy_command_matches


def test_gh_run_watch_command_matches_pattern():
    command = 'gh run watch 12345'
    pattern = r'\bgh\s+run\s+watch\b'
    gh_run_watch_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert gh_run_watch_command_matches


def test_sleep_command_matches_pattern():
    command = 'sleep 10'
    pattern = r'\bsleep\s+'
    sleep_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert sleep_command_matches


def test_safe_command_does_not_match_blocked_patterns(bash_command_blocker):
    command = 'git status'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    safe_command_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert safe_command_is_not_blocked


def test_git_push_command_is_not_blocked(bash_command_blocker):
    command = 'git push origin main'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    git_push_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert git_push_is_not_blocked


def test_cdk_synth_command_is_not_blocked(bash_command_blocker):
    command = 'cdk synth'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    cdk_synth_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert cdk_synth_is_not_blocked


def test_terraform_plan_command_is_not_blocked(bash_command_blocker):
    command = 'terraform plan'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    terraform_plan_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert terraform_plan_is_not_blocked


def test_gh_pr_create_command_is_not_blocked(bash_command_blocker):
    command = 'gh pr create --title "test"'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    gh_pr_create_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert gh_pr_create_is_not_blocked
