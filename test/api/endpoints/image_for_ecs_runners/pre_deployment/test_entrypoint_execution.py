from unittest.mock import Mock, patch
import entrypoint
import pytest


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_main_exits_with_code_1_when_config_fails(mock_run):
    mock_run.return_value = Mock(returncode=1)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 1


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_run_sh_called_after_successful_configuration(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    run_sh_calls = [c for c in mock_run.call_args_list if c[0][0] == ['./run.sh']]
    assert len(run_sh_calls) == 1


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_main_exits_with_run_sh_return_code(mock_run):
    mock_run.side_effect = [Mock(returncode=0), Mock(returncode=0), Mock(returncode=42), Mock(returncode=0)]
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 42


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_run_sh_uses_check_false_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[1][1]['check'] is False


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_returns_non_zero_exit_code(mock_run):
    mock_run.return_value = Mock(returncode=127)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 1


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_run_sh_not_called_when_config_fails(mock_run):
    mock_run.return_value = Mock(returncode=1)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_count == 1
