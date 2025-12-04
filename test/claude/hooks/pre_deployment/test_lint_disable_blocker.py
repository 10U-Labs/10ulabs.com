def test_check_content_detects_eslint_disable(lint_disable_blocker):
    content = '// eslint-disable-next-line no-console'
    violations = lint_disable_blocker.check_content(content)
    eslint_disable_is_detected = len(violations) > 0
    assert eslint_disable_is_detected


def test_check_content_detects_eslint_disable_block(lint_disable_blocker):
    content = '/* eslint-disable */'
    violations = lint_disable_blocker.check_content(content)
    eslint_disable_block_is_detected = len(violations) > 0
    assert eslint_disable_block_is_detected


def test_check_content_detects_ts_ignore(lint_disable_blocker):
    content = '// @ts-ignore'
    violations = lint_disable_blocker.check_content(content)
    ts_ignore_is_detected = len(violations) > 0
    assert ts_ignore_is_detected


def test_check_content_detects_ts_nocheck(lint_disable_blocker):
    content = '// @ts-nocheck'
    violations = lint_disable_blocker.check_content(content)
    ts_nocheck_is_detected = len(violations) > 0
    assert ts_nocheck_is_detected


def test_check_content_detects_ts_expect_error(lint_disable_blocker):
    content = '// @ts-expect-error'
    violations = lint_disable_blocker.check_content(content)
    ts_expect_error_is_detected = len(violations) > 0
    assert ts_expect_error_is_detected


def test_check_content_detects_noqa(lint_disable_blocker):
    content = 'import os  # noqa'
    violations = lint_disable_blocker.check_content(content)
    noqa_is_detected = len(violations) > 0
    assert noqa_is_detected


def test_check_content_detects_noqa_without_space(lint_disable_blocker):
    content = 'import os  #noqa'
    violations = lint_disable_blocker.check_content(content)
    noqa_without_space_is_detected = len(violations) > 0
    assert noqa_without_space_is_detected


def test_check_content_detects_type_ignore(lint_disable_blocker):
    content = 'result = func()  # type: ignore'
    violations = lint_disable_blocker.check_content(content)
    type_ignore_is_detected = len(violations) > 0
    assert type_ignore_is_detected


def test_check_content_detects_pylint_disable(lint_disable_blocker):
    content = '# pylint: disable=missing-docstring'
    violations = lint_disable_blocker.check_content(content)
    pylint_disable_is_detected = len(violations) > 0
    assert pylint_disable_is_detected


def test_check_content_detects_pragma_no_cover(lint_disable_blocker):
    content = 'if DEBUG:  # pragma: no cover'
    violations = lint_disable_blocker.check_content(content)
    pragma_no_cover_is_detected = len(violations) > 0
    assert pragma_no_cover_is_detected


def test_check_content_detects_nolint_go(lint_disable_blocker):
    content = '// nolint:errcheck'
    violations = lint_disable_blocker.check_content(content)
    nolint_go_is_detected = len(violations) > 0
    assert nolint_go_is_detected


def test_check_content_detects_rubocop_disable(lint_disable_blocker):
    content = '# rubocop:disable Style/StringLiterals'
    violations = lint_disable_blocker.check_content(content)
    rubocop_disable_is_detected = len(violations) > 0
    assert rubocop_disable_is_detected


def test_check_content_detects_nolint_cpp(lint_disable_blocker):
    content = '// NOLINT'
    violations = lint_disable_blocker.check_content(content)
    nolint_cpp_is_detected = len(violations) > 0
    assert nolint_cpp_is_detected


def test_check_content_detects_shellcheck_disable(lint_disable_blocker):
    content = '# shellcheck disable=SC2086'
    violations = lint_disable_blocker.check_content(content)
    shellcheck_disable_is_detected = len(violations) > 0
    assert shellcheck_disable_is_detected


def test_check_content_detects_markdownlint_disable(lint_disable_blocker):
    content = '<!-- markdownlint-disable MD013 -->'
    violations = lint_disable_blocker.check_content(content)
    markdownlint_disable_is_detected = len(violations) > 0
    assert markdownlint_disable_is_detected


def test_check_content_detects_stylelint_disable(lint_disable_blocker):
    content = '/* stylelint-disable property-no-unknown */'
    violations = lint_disable_blocker.check_content(content)
    stylelint_disable_is_detected = len(violations) > 0
    assert stylelint_disable_is_detected


def test_check_content_allows_regular_comment(lint_disable_blocker):
    content = '# This is a regular comment'
    violations = lint_disable_blocker.check_content(content)
    regular_comment_is_allowed = len(violations) == 0
    assert regular_comment_is_allowed


def test_check_content_allows_regular_code(lint_disable_blocker):
    content = 'def hello():\n    print("hello")'
    violations = lint_disable_blocker.check_content(content)
    regular_code_is_allowed = len(violations) == 0
    assert regular_code_is_allowed


def test_check_content_allows_todo_comment(lint_disable_blocker):
    content = '# TODO: fix this later'
    violations = lint_disable_blocker.check_content(content)
    todo_comment_is_allowed = len(violations) == 0
    assert todo_comment_is_allowed


def test_check_content_returns_empty_for_empty_content(lint_disable_blocker):
    content = ''
    violations = lint_disable_blocker.check_content(content)
    empty_content_returns_empty = len(violations) == 0
    assert empty_content_returns_empty
