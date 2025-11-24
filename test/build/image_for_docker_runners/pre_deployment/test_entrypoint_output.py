from unittest.mock import Mock, patch
import entrypoint
import pytest


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'my-org/my-repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_registration_prints_repository_name(mock_run, mock_print):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[1][0][0] == 'Repository: my-org/my-repo'


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'test-runner-name', '--labels', 'lbl', '--token', 'tok'])
def test_registration_prints_runner_name(mock_run, mock_print):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[2][0][0] == 'Runner Name: test-runner-name'


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'test-labels', '--token', 'tok'])
def test_registration_prints_labels(mock_run, mock_print):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[3][0][0] == 'Labels: test-labels'


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_error_message_prints_when_config_fails(mock_run, mock_print):
    mock_run.return_value = Mock(returncode=5)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[4][0][0] == 'Error: config.sh failed with exit code 5'


@patch('builtins.print')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_runner_exit_code_is_printed(mock_run, mock_print):
    mock_run.side_effect = [Mock(returncode=0), Mock(returncode=3)]
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_print.call_args_list[5][0][0] == 'Runner exited with code 3'
