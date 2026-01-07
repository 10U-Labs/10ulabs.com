"""Unit tests for test_fixtures.terraform module."""
from pathlib import Path
from unittest.mock import patch, MagicMock

from test_fixtures.terraform import (
    terraform_init,
    terraform_output,
    terraform_output_json,
)


class TestTerraformInit:
    """Tests for terraform_init function."""

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_true_on_success(self, mock_run):
        """Test that terraform_init returns True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        result = terraform_init(Path('/test/dir'))
        assert result is True

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_false_on_failure(self, mock_run):
        """Test that terraform_init returns False on failure."""
        mock_run.return_value = MagicMock(returncode=1)
        result = terraform_init(Path('/test/dir'))
        assert result is False

    @patch('test_fixtures.terraform.subprocess.run')
    def test_calls_terraform_init_command(self, mock_run):
        """Test that terraform_init calls terraform init command."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/test/dir'))
        call_args = mock_run.call_args
        assert call_args[0][0][0] == 'terraform'
        assert call_args[0][0][1] == 'init'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_backend_true_flag(self, mock_run):
        """Test that terraform_init uses -backend=true flag."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/test/dir'))
        call_args = mock_run.call_args
        assert '-backend=true' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_input_false_flag(self, mock_run):
        """Test that terraform_init uses -input=false flag."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/test/dir'))
        call_args = mock_run.call_args
        assert '-input=false' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_correct_working_directory(self, mock_run):
        """Test that terraform_init uses correct cwd."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/custom/path'))
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == '/custom/path'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_captures_output(self, mock_run):
        """Test that terraform_init captures output."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/test/dir'))
        call_args = mock_run.call_args
        assert call_args[1]['capture_output'] is True

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_text_mode(self, mock_run):
        """Test that terraform_init uses text mode."""
        mock_run.return_value = MagicMock(returncode=0)
        terraform_init(Path('/test/dir'))
        call_args = mock_run.call_args
        assert call_args[1]['text'] is True


class TestTerraformOutput:
    """Tests for terraform_output function."""

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_output_value_on_success(self, mock_run):
        """Test that terraform_output returns output value on success."""
        mock_run.return_value = MagicMock(returncode=0, stdout='test-value\n')
        result = terraform_output(Path('/test/dir'), 'my_output')
        assert result == 'test-value'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_empty_string_on_failure(self, mock_run):
        """Test that terraform_output returns empty string on failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout='')
        result = terraform_output(Path('/test/dir'), 'my_output')
        assert result == ''

    @patch('test_fixtures.terraform.subprocess.run')
    def test_strips_whitespace_from_output(self, mock_run):
        """Test that terraform_output strips whitespace."""
        mock_run.return_value = MagicMock(returncode=0, stdout='  value  \n')
        result = terraform_output(Path('/test/dir'), 'my_output')
        assert result == 'value'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_calls_terraform_output_command(self, mock_run):
        """Test that terraform_output calls terraform output command."""
        mock_run.return_value = MagicMock(returncode=0, stdout='')
        terraform_output(Path('/test/dir'), 'my_output')
        call_args = mock_run.call_args
        assert call_args[0][0][0] == 'terraform'
        assert call_args[0][0][1] == 'output'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_raw_flag(self, mock_run):
        """Test that terraform_output uses -raw flag."""
        mock_run.return_value = MagicMock(returncode=0, stdout='')
        terraform_output(Path('/test/dir'), 'my_output')
        call_args = mock_run.call_args
        assert '-raw' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_passes_output_name(self, mock_run):
        """Test that terraform_output passes output name."""
        mock_run.return_value = MagicMock(returncode=0, stdout='')
        terraform_output(Path('/test/dir'), 'bucket_name')
        call_args = mock_run.call_args
        assert 'bucket_name' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_correct_working_directory(self, mock_run):
        """Test that terraform_output uses correct cwd."""
        mock_run.return_value = MagicMock(returncode=0, stdout='')
        terraform_output(Path('/custom/path'), 'my_output')
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == '/custom/path'


class TestTerraformOutputJson:
    """Tests for terraform_output_json function."""

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_json_output_on_success(self, mock_run):
        """Test that terraform_output_json returns JSON on success."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{"key": "value"}\n')
        result = terraform_output_json(Path('/test/dir'), 'my_output')
        assert result == '{"key": "value"}'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_returns_empty_string_on_failure(self, mock_run):
        """Test that terraform_output_json returns empty string on failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout='')
        result = terraform_output_json(Path('/test/dir'), 'my_output')
        assert result == ''

    @patch('test_fixtures.terraform.subprocess.run')
    def test_strips_whitespace_from_output(self, mock_run):
        """Test that terraform_output_json strips whitespace."""
        mock_run.return_value = MagicMock(returncode=0, stdout='  {"key": "value"}  \n')
        result = terraform_output_json(Path('/test/dir'), 'my_output')
        assert result == '{"key": "value"}'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_calls_terraform_output_command(self, mock_run):
        """Test that terraform_output_json calls terraform output command."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{}')
        terraform_output_json(Path('/test/dir'), 'my_output')
        call_args = mock_run.call_args
        assert call_args[0][0][0] == 'terraform'
        assert call_args[0][0][1] == 'output'

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_json_flag(self, mock_run):
        """Test that terraform_output_json uses -json flag."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{}')
        terraform_output_json(Path('/test/dir'), 'my_output')
        call_args = mock_run.call_args
        assert '-json' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_passes_output_name(self, mock_run):
        """Test that terraform_output_json passes output name."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{}')
        terraform_output_json(Path('/test/dir'), 'complex_output')
        call_args = mock_run.call_args
        assert 'complex_output' in call_args[0][0]

    @patch('test_fixtures.terraform.subprocess.run')
    def test_uses_correct_working_directory(self, mock_run):
        """Test that terraform_output_json uses correct cwd."""
        mock_run.return_value = MagicMock(returncode=0, stdout='{}')
        terraform_output_json(Path('/another/path'), 'my_output')
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == '/another/path'
