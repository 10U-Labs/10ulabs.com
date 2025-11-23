import argparse
import os
import sys
from unittest.mock import MagicMock, Mock, call, patch
import pytest
from dockerfile_parse import DockerfileParser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src/api/docker_runner'))
import entrypoint


@pytest.fixture
def dockerfile_parser(dockerfile_path):
    dfp = DockerfileParser()
    with open(dockerfile_path, 'r') as f:
        dfp.content = f.read()
    return dfp


def test_parser_accepts_all_required_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--labels', required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args(['--repo', 'org/repo', '--name', 'test-runner', '--labels', 'label1', '--token', 'test-token'])
    assert args.repo == 'org/repo'


def test_parser_raises_error_when_repo_argument_missing():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--labels', required=True)
    parser.add_argument('--token', required=True)
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(['--name', 'test-runner', '--labels', 'label1', '--token', 'test-token'])
    assert exc_info.value.code == 2


def test_parsed_arguments_assigned_to_repo_variable():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--labels', required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args(['--repo', 'test/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
    assert args.repo == 'test/repo'


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_subprocess_run_with_config_sh(mock_run):
    entrypoint.cleanup_runner('test-token')
    assert mock_run.called


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_uses_registration_token_parameter(mock_run):
    entrypoint.cleanup_runner('my-token')
    assert mock_run.call_args[0][0][3] == 'my-token'


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_uses_check_false_parameter(mock_run):
    entrypoint.cleanup_runner('token')
    assert mock_run.call_args[1]['check'] == False


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_sigterm_signal_registered(mock_run, mock_signal):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[0][0][0] == entrypoint.signal.SIGTERM


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_sigint_signal_registered(mock_run, mock_signal):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_signal.call_args_list[1][0][0] == entrypoint.signal.SIGINT


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_signal_handler_exits_with_code_zero(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 0


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'test/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_called_with_correct_url_format(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][2] == 'https://github.com/test/repo'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'my-token'])
def test_config_sh_called_with_correct_token_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][4] == 'my-token'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'my-runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_called_with_correct_name_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][6] == 'my-runner'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'my-labels', '--token', 'tok'])
def test_config_sh_called_with_correct_labels_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][8] == 'my-labels'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_called_with_work_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][10] == '_work'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_called_with_unattended_flag(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][11] == '--unattended'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_config_sh_called_with_ephemeral_flag(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[0][0][0][12] == '--ephemeral'


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
    assert mock_run.call_args_list[1][0][0][0] == './run.sh'


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_main_exits_with_run_sh_return_code(mock_run):
    mock_run.side_effect = [Mock(returncode=0), Mock(returncode=42)]
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()
    assert exc_info.value.code == 42


@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_run_sh_uses_check_false_parameter(mock_run):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert mock_run.call_args_list[1][1]['check'] == False


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


def test_dockerfile_base_image_is_debian_stable_slim(dockerfile_parser):
    assert dockerfile_parser.baseimage == 'debian:stable-slim'


def test_dockerfile_shell_set_to_bash(dockerfile_parser):
    content = dockerfile_parser.content
    assert 'SHELL ["/bin/bash", "-o", "pipefail", "-c"]' == content.split('\n')[1]


def test_dockerfile_pip3_uses_break_system_packages(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('--break-system-packages') != -1


def test_dockerfile_creates_runner_user(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('useradd -m -s /bin/bash runner') != -1


def test_dockerfile_runner_has_sudo_nopasswd(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('runner ALL=(ALL) NOPASSWD:ALL') != -1


def test_dockerfile_copies_entrypoint_to_home_runner(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('COPY entrypoint.py /home/runner/entrypoint.py') != -1


def test_dockerfile_entrypoint_chmod_executable(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('chmod +x /home/runner/entrypoint.py') != -1


def test_dockerfile_entrypoint_chown_runner(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('chown runner:runner /home/runner/entrypoint.py') != -1


def test_dockerfile_entrypoint_directive_set(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('ENTRYPOINT ["/home/runner/entrypoint.py"]') != -1


def test_dockerfile_cmd_includes_repo_argument(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('--repo') != -1


def test_dockerfile_cmd_includes_name_argument(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('--name') != -1


def test_dockerfile_cmd_includes_labels_argument(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('--labels') != -1


def test_dockerfile_cmd_includes_token_argument(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('--token') != -1


def test_dockerfile_user_directive_sets_runner(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('USER runner') != -1


def test_dockerfile_workdir_set_to_home_runner(dockerfile_parser):
    content = dockerfile_parser.content
    assert content.find('WORKDIR /home/runner') != -1


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_continues_when_removal_fails(mock_run):
    mock_run.return_value = Mock(returncode=1)
    entrypoint.cleanup_runner('token')
    assert mock_run.called


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


@patch('entrypoint.signal.signal')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', ['entrypoint.py', '--repo', 'org/repo', '--name', 'runner', '--labels', 'lbl', '--token', 'tok'])
def test_signal_handler_function_registered(mock_run, mock_signal):
    mock_run.return_value = Mock(returncode=0)
    with pytest.raises(SystemExit):
        entrypoint.main()
    assert callable(mock_signal.call_args_list[0][0][1])


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


@patch('entrypoint.subprocess.run')
def test_cleanup_runner_calls_config_sh_remove(mock_run):
    entrypoint.cleanup_runner('test-token')
    assert mock_run.call_args[0][0][1] == 'remove'
