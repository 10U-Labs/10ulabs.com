"""Unit tests for build_ami module functionality."""

from unittest.mock import MagicMock, patch


class TestParseTagsBasic:
    """Tests for parse_tags with basic inputs."""

    def test_returns_empty_dict_for_none(self, build_ami_module):
        """Test that empty dict is returned for None input."""
        result = build_ami_module.parse_tags(None)
        assert result == {}

    def test_returns_empty_dict_for_empty_list(self, build_ami_module):
        """Test that empty dict is returned for empty list."""
        result = build_ami_module.parse_tags([])
        assert result == {}

    def test_parses_single_tag(self, build_ami_module):
        """Test that single tag is parsed correctly."""
        result = build_ami_module.parse_tags(["Name=my-ami"])
        assert result == {"Name": "my-ami"}

    def test_parses_multiple_tags(self, build_ami_module):
        """Test that multiple tags are parsed correctly."""
        result = build_ami_module.parse_tags(["Name=my-ami", "Env=prod"])
        assert result == {"Name": "my-ami", "Env": "prod"}


class TestParseTagsEdgeCases:
    """Tests for parse_tags with edge cases."""

    def test_handles_value_with_equals_sign(self, build_ami_module):
        """Test that values containing equals signs are handled correctly."""
        result = build_ami_module.parse_tags(["key=value=with=equals"])
        assert result == {"key": "value=with=equals"}

    def test_skips_items_without_equals_sign(self, build_ami_module):
        """Test that items without equals sign are skipped."""
        result = build_ami_module.parse_tags(["invalid", "valid=value"])
        assert result == {"valid": "value"}

    def test_handles_empty_value(self, build_ami_module):
        """Test that empty values are handled correctly."""
        result = build_ami_module.parse_tags(["key="])
        assert result == {"key": ""}


class TestLookupSourceAmi:
    """Tests for lookup_source_ami functionality."""

    def test_returns_ami_id_when_found(self, build_ami_module):
        """Test that AMI ID is returned when image is found."""
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": [{"ImageId": "ami-12345678"}]}
        result = build_ami_module.lookup_source_ami(mock_ec2, "debian-13-arm64-20251117-2299")
        assert result == "ami-12345678"

    def test_raises_error_when_not_found(self, build_ami_module, raise_runtime_error):
        """Test that error is raised when AMI not found."""
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": []}
        with raise_runtime_error:
            build_ami_module.lookup_source_ami(mock_ec2, "nonexistent-ami")
        assert True  # Explicit pass


class TestRunSshCommandSuccess:
    """Tests for run_ssh_command when command succeeds."""

    def test_does_not_raise_when_exit_code_zero(self, build_ami_module, mock_ssh_client_success):
        """Test that no error is raised when exit code is zero."""
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert True  # Explicit pass

    def test_calls_exec_command_with_command(self, build_ami_module, mock_ssh_client_success):
        """Test that exec_command is called with correct command."""
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[0][0] == "echo hello"

    def test_calls_exec_command_with_timeout(self, build_ami_module, mock_ssh_client_success):
        """Test that exec_command is called with timeout."""
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[1]["timeout"] == 600

    def test_calls_exec_command_with_pty(self, build_ami_module, mock_ssh_client_success):
        """Test that exec_command is called with pty enabled."""
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[1]["get_pty"] is True


class TestRunSshCommandFailure:
    """Tests for run_ssh_command when command fails."""

    def test_raises_runtime_error_when_exit_code_nonzero(
        self, build_ami_module, mock_ssh_client_failure, raise_runtime_error
    ):
        """Test that RuntimeError is raised when exit code is non-zero."""
        with raise_runtime_error:
            build_ami_module.run_ssh_command(mock_ssh_client_failure, "exit 1")
        assert True  # Explicit pass

    def test_raises_runtime_error_when_exit_code_127(
        self, build_ami_module, mock_ssh_client_exit_127, raise_runtime_error
    ):
        """Test that RuntimeError is raised when exit code is 127."""
        with raise_runtime_error:
            build_ami_module.run_ssh_command(
                mock_ssh_client_exit_127, "command_not_found"
            )
        assert True  # Explicit pass


class TestRunSshCommandOutput:
    """Tests for run_ssh_command output handling."""

    def test_writes_output_to_sys_stdout(
        self, build_ami_module, mock_ssh_client_with_output, capsys
    ):
        """Test that command output is written to stdout."""
        build_ami_module.run_ssh_command(
            mock_ssh_client_with_output, "echo hello"
        )
        captured = capsys.readouterr()
        assert captured.out == "hello world"

    def test_streams_output_from_multiline_script(
        self, build_ami_module, mock_ssh_client_with_multiline_output, capsys
    ):
        """Test that multiline output is streamed correctly."""
        script = "echo line1\necho line2\necho line3"
        build_ami_module.run_ssh_command(
            mock_ssh_client_with_multiline_output, script
        )
        captured = capsys.readouterr()
        assert captured.out == "line1\nline2\nline3\n"


class TestGetInstancePublicIp:
    """Tests for get_instance_public_ip functionality."""

    def test_returns_public_ip(self, build_ami_module):
        """Test that public IP address is returned."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"PublicIpAddress": "1.2.3.4"}]}]
        }
        result = build_ami_module.get_instance_public_ip(mock_ec2, "i-12345")
        assert result == "1.2.3.4"

    def test_queries_correct_instance_id(self, build_ami_module):
        """Test that correct instance ID is queried."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"PublicIpAddress": "5.6.7.8"}]}]
        }
        build_ami_module.get_instance_public_ip(mock_ec2, "i-test123")
        assert mock_ec2.describe_instances.call_args[1]["InstanceIds"] == ["i-test123"]


class TestWaitForInstanceIntegration:
    """Tests for wait_for_instance integration."""

    def test_calls_wait_for_instance_running(self, build_ami_module):
        """Test that wait_for_instance_running is called."""
        mock_ec2 = MagicMock()
        with patch.object(
            build_ami_module, 'wait_for_instance_running'
        ) as mock_running:
            with patch.object(build_ami_module, 'wait_for_status_checks'):
                with patch.object(
                    build_ami_module,
                    'get_instance_public_ip',
                    return_value="1.2.3.4",
                ):
                    build_ami_module.wait_for_instance(mock_ec2, "i-12345")
        assert mock_running.call_args[0][1] == "i-12345"

    def test_calls_wait_for_status_checks(self, build_ami_module):
        """Test that wait_for_status_checks is called."""
        mock_ec2 = MagicMock()
        with patch.object(build_ami_module, 'wait_for_instance_running'):
            with patch.object(
                build_ami_module, 'wait_for_status_checks'
            ) as mock_status:
                with patch.object(
                    build_ami_module,
                    'get_instance_public_ip',
                    return_value="1.2.3.4",
                ):
                    build_ami_module.wait_for_instance(mock_ec2, "i-12345")
        assert mock_status.call_args[0][1] == "i-12345"

    def test_returns_public_ip(self, build_ami_module):
        """Test that public IP is returned."""
        mock_ec2 = MagicMock()
        with patch.object(build_ami_module, 'wait_for_instance_running'):
            with patch.object(build_ami_module, 'wait_for_status_checks'):
                with patch.object(
                    build_ami_module,
                    'get_instance_public_ip',
                    return_value="9.8.7.6",
                ):
                    result = build_ami_module.wait_for_instance(
                        mock_ec2, "i-12345"
                    )
        assert result == "9.8.7.6"


class TestRunScriptConnection:
    """Tests for run_script SSH connection handling."""

    def test_connects_to_correct_ip(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that SSH connects to correct IP address."""
        mock_client, _ = mock_ssh_context
        params = make_script_params(ip_addr="192.168.1.100")
        build_ami_module.run_script(params)
        assert mock_client.connect.call_args[0][0] == "192.168.1.100"

    def test_connects_with_admin_username(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that SSH connects with admin username."""
        mock_client, _ = mock_ssh_context
        params = make_script_params()
        build_ami_module.run_script(params)
        assert mock_client.connect.call_args[1]["username"] == "admin"

    def test_closes_client_after_completion(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that SSH client is closed after completion."""
        mock_client, _ = mock_ssh_context
        params = make_script_params()
        build_ami_module.run_script(params)
        assert mock_client.close.called


class TestRunScriptSftp:
    """Tests for run_script SFTP file handling."""

    def test_uploads_script_via_sftp(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that script is uploaded via SFTP."""
        _, mock_sftp = mock_ssh_context
        params = make_script_params()
        build_ami_module.run_script(params)
        assert mock_sftp.put.called

    def test_makes_script_executable(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that script is made executable after upload."""
        _, mock_sftp = mock_ssh_context
        params = make_script_params()
        build_ami_module.run_script(params)
        mock_sftp.chmod.assert_called_with("/tmp/setup.sh", 0o755)
        assert True  # Explicit pass

    def test_closes_sftp_after_upload(
        self, build_ami_module, mock_ssh_context, make_script_params
    ):
        """Test that SFTP connection is closed after upload."""
        _, mock_sftp = mock_ssh_context
        params = make_script_params()
        build_ami_module.run_script(params)
        assert mock_sftp.close.called


class TestRunScriptCloudwatchConfig:
    """Tests for run_script CloudWatch config transfer."""

    def test_transfers_cloudwatch_config_if_exists(
        self, build_ami_module, mock_ssh_context, tmp_path
    ):
        """Test that CloudWatch config file is transferred if it exists."""
        _, mock_sftp = mock_ssh_context
        # Create script and config file in same directory
        script = tmp_path / "setup.py"
        script.write_text("print('hello')")
        config = tmp_path / "cloudwatch-agent-config.json"
        config.write_text('{"test": true}')
        params = build_ami_module.ScriptParams(
            "1.2.3.4", "key", script, "1.0", "1.0", "1.0", "test"
        )
        build_ami_module.run_script(params)
        # Check that config file was transferred
        put_calls = [str(c) for c in mock_sftp.put.call_args_list]
        assert any("cloudwatch-agent-config.json" in c for c in put_calls)

    def test_skips_cloudwatch_config_if_not_exists(
        self, build_ami_module, mock_ssh_context, tmp_path
    ):
        """Test that missing CloudWatch config file is handled gracefully."""
        _, mock_sftp = mock_ssh_context
        # Create script but no config file
        script = tmp_path / "setup.py"
        script.write_text("print('hello')")
        params = build_ami_module.ScriptParams(
            "1.2.3.4", "key", script, "1.0", "1.0", "1.0", "test"
        )
        build_ami_module.run_script(params)
        # Should only transfer the script, not config
        put_calls = [str(c) for c in mock_sftp.put.call_args_list]
        assert not any("cloudwatch-agent-config.json" in c for c in put_calls)


class TestScriptParamsDataclass:
    """Tests for ScriptParams dataclass."""

    def test_stores_ip_addr(self, make_script_params):
        """Test that ip_addr is stored correctly."""
        params = make_script_params(ip_addr="1.2.3.4")
        assert params.ip_addr == "1.2.3.4"

    def test_stores_key_material(self, make_script_params):
        """Test that key_material is stored correctly."""
        params = make_script_params(key_material="my-key")
        assert params.key_material == "my-key"

    def test_stores_setup_script(self, make_script_params, script_file):
        """Test that setup_script is stored correctly."""
        params = make_script_params(setup_script=script_file)
        assert params.setup_script == script_file

    def test_stores_runner_version(self, make_script_params):
        """Test that runner_version is stored correctly."""
        params = make_script_params(runner_version="2.330.0")
        assert params.runner_version == "2.330.0"

    def test_stores_yq_version(self, make_script_params):
        """Test that yq_version is stored correctly."""
        params = make_script_params(yq_version="4.44.1")
        assert params.yq_version == "4.44.1"

    def test_stores_runner_user(self, make_script_params):
        """Test that runner_user is stored correctly."""
        params = make_script_params(runner_user="github-runner")
        assert params.runner_user == "github-runner"
