"""Tests for bash_command_blocker hook."""

import re


def test_blocked_patterns_contains_gh_run_watch(bash_command_blocker):
    """Test that Blocked patterns contains gh run watch."""
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    gh_run_watch_pattern_exists = any('gh' in p and 'run' in p and 'watch' in p for p in patterns)
    assert gh_run_watch_pattern_exists


def test_blocked_patterns_contains_sleep(bash_command_blocker):
    """Test that Blocked patterns contains sleep."""
    patterns = [p[0] for p in bash_command_blocker.BLOCKED_PATTERNS]
    sleep_pattern_exists = any('sleep' in p for p in patterns)
    assert sleep_pattern_exists


def test_gh_run_watch_command_matches_pattern():
    """Test that Gh run watch command matches pattern."""
    command = 'gh run watch 12345'
    pattern = r'\bgh\s+run\s+watch\b'
    gh_run_watch_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert gh_run_watch_command_matches


def test_sleep_command_matches_pattern():
    """Test that Sleep command matches pattern."""
    command = 'sleep 10'
    pattern = r'\bsleep\s+'
    sleep_command_matches = re.search(pattern, command, re.IGNORECASE) is not None
    assert sleep_command_matches


def test_safe_command_does_not_match_blocked_patterns(bash_command_blocker):
    """Test that Safe command does not match blocked patterns."""
    command = 'git status'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    safe_command_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert safe_command_is_not_blocked


def test_git_push_command_is_not_blocked(bash_command_blocker):
    """Test that Git push command is not blocked."""
    command = 'git push origin main'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    git_push_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert git_push_is_not_blocked


def test_gh_pr_create_command_is_not_blocked(bash_command_blocker):
    """Test that Gh pr create command is not blocked."""
    command = 'gh pr create --title "test"'
    blocked_patterns = bash_command_blocker.BLOCKED_PATTERNS
    gh_pr_create_is_not_blocked = all(
        re.search(p[0], command, re.IGNORECASE) is None for p in blocked_patterns
    )
    assert gh_pr_create_is_not_blocked
