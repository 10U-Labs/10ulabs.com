from unittest.mock import Mock, patch
import entrypoint
import pytest


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', '', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_parser_accepts_empty_string_for_repo(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][2] == 'https://github.com/'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', '', '--labels', 'lbl', '--token', 'tok'])
def test_parser_accepts_empty_string_for_name(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][6] == ''


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', '', '--token', 'tok'])
def test_parser_accepts_empty_string_for_labels(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][8] == ''


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'my-org/my-repo-with-dashes_underscores', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_parser_accepts_special_characters_in_repo(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][2] == 'https://github.com/my-org/my-repo-with-dashes_underscores'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner-with-dashes_123', '--labels', 'lbl', '--token', 'tok'])
def test_parser_accepts_special_characters_in_name(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][6] == 'runner-with-dashes_123'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'label1,label2,label-3_test', '--token', 'tok'])
def test_parser_accepts_comma_separated_labels(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][8] == 'label1,label2,label-3_test'
