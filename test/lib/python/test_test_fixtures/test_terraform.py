from pathlib import Path
from unittest.mock import patch, MagicMock

from test_fixtures.terraform import (
    terraform_init,
    terraform_output,
)


@patch('test_fixtures.terraform.subprocess.run')
def test_returns_true_on_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    result = terraform_init(Path('/test/dir'))
    assert result is True


@patch('test_fixtures.terraform.subprocess.run')
def test_returns_false_on_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1)
    result = terraform_init(Path('/test/dir'))
    assert result is False


@patch('test_fixtures.terraform.subprocess.run')
def test_terraform_init_calls_terraform_command(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert call_args[0][0][0] == 'terraform'


@patch('test_fixtures.terraform.subprocess.run')
def test_calls_init_subcommand(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert call_args[0][0][1] == 'init'


@patch('test_fixtures.terraform.subprocess.run')
def test_uses_backend_true_flag(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert '-backend=true' in call_args[0][0]


@patch('test_fixtures.terraform.subprocess.run')
def test_uses_input_false_flag(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert '-input=false' in call_args[0][0]


@patch('test_fixtures.terraform.subprocess.run')
def test_terraform_init_uses_correct_working_directory(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/custom/path'))
    call_args = mock_run.call_args
    assert call_args[1]['cwd'] == '/custom/path'


@patch('test_fixtures.terraform.subprocess.run')
def test_captures_output(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert call_args[1]['capture_output'] is True


@patch('test_fixtures.terraform.subprocess.run')
def test_uses_text_mode(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0)
    terraform_init(Path('/test/dir'))
    call_args = mock_run.call_args
    assert call_args[1]['text'] is True


@patch('test_fixtures.terraform.subprocess.run')
def test_returns_output_value_on_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='test-value\n')
    result = terraform_output(Path('/test/dir'), 'my_output')
    assert result == 'test-value'


@patch('test_fixtures.terraform.subprocess.run')
def test_returns_empty_string_on_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout='')
    result = terraform_output(Path('/test/dir'), 'my_output')
    assert result == ''


@patch('test_fixtures.terraform.subprocess.run')
def test_strips_whitespace_from_output(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='  value  \n')
    result = terraform_output(Path('/test/dir'), 'my_output')
    assert result == 'value'


@patch('test_fixtures.terraform.subprocess.run')
def test_terraform_output_calls_terraform_command(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='')
    terraform_output(Path('/test/dir'), 'my_output')
    call_args = mock_run.call_args
    assert call_args[0][0][0] == 'terraform'


@patch('test_fixtures.terraform.subprocess.run')
def test_calls_output_subcommand(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='')
    terraform_output(Path('/test/dir'), 'my_output')
    call_args = mock_run.call_args
    assert call_args[0][0][1] == 'output'


@patch('test_fixtures.terraform.subprocess.run')
def test_uses_raw_flag(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='')
    terraform_output(Path('/test/dir'), 'my_output')
    call_args = mock_run.call_args
    assert '-raw' in call_args[0][0]


@patch('test_fixtures.terraform.subprocess.run')
def test_passes_output_name(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='')
    terraform_output(Path('/test/dir'), 'bucket_name')
    call_args = mock_run.call_args
    assert 'bucket_name' in call_args[0][0]


@patch('test_fixtures.terraform.subprocess.run')
def test_terraform_output_uses_correct_working_directory(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout='')
    terraform_output(Path('/custom/path'), 'my_output')
    call_args = mock_run.call_args
    assert call_args[1]['cwd'] == '/custom/path'
