from unittest.mock import MagicMock, patch
import pytest


class TestParseTagsBasic:

    def test_returns_empty_dict_for_none(self, build_ami_module):
        result = build_ami_module.parse_tags(None)
        assert result == {}

    def test_returns_empty_dict_for_empty_list(self, build_ami_module):
        result = build_ami_module.parse_tags([])
        assert result == {}

    def test_parses_single_tag(self, build_ami_module):
        result = build_ami_module.parse_tags(["Name=my-ami"])
        assert result == {"Name": "my-ami"}

    def test_parses_multiple_tags(self, build_ami_module):
        result = build_ami_module.parse_tags(["Name=my-ami", "Env=prod"])
        assert result == {"Name": "my-ami", "Env": "prod"}


class TestParseTagsEdgeCases:

    def test_handles_value_with_equals_sign(self, build_ami_module):
        result = build_ami_module.parse_tags(["key=value=with=equals"])
        assert result == {"key": "value=with=equals"}

    def test_skips_items_without_equals_sign(self, build_ami_module):
        result = build_ami_module.parse_tags(["invalid", "valid=value"])
        assert result == {"valid": "value"}

    def test_handles_empty_value(self, build_ami_module):
        result = build_ami_module.parse_tags(["key="])
        assert result == {"key": ""}


class TestLookupSourceAmi:

    def test_returns_ami_id_when_found(self, build_ami_module):
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": [{"ImageId": "ami-12345678"}]}
        result = build_ami_module.lookup_source_ami(mock_ec2, "debian-13-arm64-20251117-2299")
        assert result == "ami-12345678"

    def test_raises_error_when_not_found(self, build_ami_module, raise_runtime_error):
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": []}
        with raise_runtime_error:
            build_ami_module.lookup_source_ami(mock_ec2, "nonexistent-ami")


class TestRunSshCommandSuccess:

    def test_does_not_raise_when_exit_code_zero(self, build_ami_module, mock_ssh_client_success):
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")

    def test_calls_exec_command_with_command(self, build_ami_module, mock_ssh_client_success):
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[0][0] == "echo hello"

    def test_calls_exec_command_with_timeout(self, build_ami_module, mock_ssh_client_success):
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[1]["timeout"] == 600

    def test_calls_exec_command_with_pty(self, build_ami_module, mock_ssh_client_success):
        build_ami_module.run_ssh_command(mock_ssh_client_success, "echo hello")
        assert mock_ssh_client_success.exec_command.call_args[1]["get_pty"] is True


class TestRunSshCommandFailure:

    def test_raises_runtime_error_when_exit_code_nonzero(self, build_ami_module, mock_ssh_client_failure, raise_runtime_error):
        with raise_runtime_error:
            build_ami_module.run_ssh_command(mock_ssh_client_failure, "exit 1")

    def test_raises_runtime_error_when_exit_code_127(self, build_ami_module, mock_ssh_client_exit_127, raise_runtime_error):
        with raise_runtime_error:
            build_ami_module.run_ssh_command(mock_ssh_client_exit_127, "command_not_found")


class TestRunSshCommandOutput:

    def test_writes_output_to_sys_stdout(self, build_ami_module, mock_ssh_client_with_output, capsys):
        build_ami_module.run_ssh_command(mock_ssh_client_with_output, "echo hello")
        captured = capsys.readouterr()
        assert captured.out == "hello world"

    def test_streams_output_from_multiline_script(self, build_ami_module, mock_ssh_client_with_multiline_output, capsys):
        script = "echo line1\necho line2\necho line3"
        build_ami_module.run_ssh_command(mock_ssh_client_with_multiline_output, script)
        captured = capsys.readouterr()
        assert captured.out == "line1\nline2\nline3\n"


class TestGetInstancePublicIp:

    def test_returns_public_ip(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"PublicIpAddress": "1.2.3.4"}]}]
        }
        result = build_ami_module.get_instance_public_ip(mock_ec2, "i-12345")
        assert result == "1.2.3.4"

    def test_queries_correct_instance_id(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"PublicIpAddress": "5.6.7.8"}]}]
        }
        build_ami_module.get_instance_public_ip(mock_ec2, "i-test123")
        assert mock_ec2.describe_instances.call_args[1]["InstanceIds"] == ["i-test123"]


class TestWaitForInstanceIntegration:

    def test_calls_wait_for_instance_running(self, build_ami_module):
        mock_ec2 = MagicMock()
        with patch.object(build_ami_module, 'wait_for_instance_running') as mock_running:
            with patch.object(build_ami_module, 'wait_for_status_checks'):
                with patch.object(build_ami_module, 'get_instance_public_ip', return_value="1.2.3.4"):
                    build_ami_module.wait_for_instance(mock_ec2, "i-12345")
        assert mock_running.call_args[0][1] == "i-12345"

    def test_calls_wait_for_status_checks(self, build_ami_module):
        mock_ec2 = MagicMock()
        with patch.object(build_ami_module, 'wait_for_instance_running'):
            with patch.object(build_ami_module, 'wait_for_status_checks') as mock_status:
                with patch.object(build_ami_module, 'get_instance_public_ip', return_value="1.2.3.4"):
                    build_ami_module.wait_for_instance(mock_ec2, "i-12345")
        assert mock_status.call_args[0][1] == "i-12345"

    def test_returns_public_ip(self, build_ami_module):
        mock_ec2 = MagicMock()
        with patch.object(build_ami_module, 'wait_for_instance_running'):
            with patch.object(build_ami_module, 'wait_for_status_checks'):
                with patch.object(build_ami_module, 'get_instance_public_ip', return_value="9.8.7.6"):
                    result = build_ami_module.wait_for_instance(mock_ec2, "i-12345")
        assert result == "9.8.7.6"


class TestRunScriptConnection:

    def test_connects_to_correct_ip(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("192.168.1.100", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    assert mock_client.connect.call_args[0][0] == "192.168.1.100"

    def test_connects_with_admin_username(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("1.2.3.4", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    assert mock_client.connect.call_args[1]["username"] == "admin"

    def test_closes_client_after_completion(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("1.2.3.4", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    assert mock_client.close.called


class TestRunScriptSftp:

    def test_uploads_script_via_sftp(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("1.2.3.4", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    assert mock_sftp.put.called

    def test_makes_script_executable(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("1.2.3.4", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    mock_sftp.chmod.assert_called_with("/tmp/setup.sh", 0o755)

    def test_closes_sftp_after_upload(self, build_ami_module, tmp_path):
        script_file = tmp_path / "setup.sh"
        script_file.write_text("#!/bin/bash\necho hello")
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.ScriptParams("1.2.3.4", "key", str(script_file), "1.0", "1.0", "test")
                    build_ami_module.run_script(params)
                    assert mock_sftp.close.called


class TestScriptParamsDataclass:

    def test_stores_ip_addr(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "key", "/path/script.sh", "2.0", "4.0", "runner")
        assert params.ip_addr == "1.2.3.4"

    def test_stores_key_material(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "my-key", "/path/script.sh", "2.0", "4.0", "runner")
        assert params.key_material == "my-key"

    def test_stores_script_path(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "key", "/path/to/setup.sh", "2.0", "4.0", "runner")
        assert params.script_path == "/path/to/setup.sh"

    def test_stores_runner_version(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "key", "/path/script.sh", "2.330.0", "4.0", "runner")
        assert params.runner_version == "2.330.0"

    def test_stores_yq_version(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "key", "/path/script.sh", "2.0", "4.44.1", "runner")
        assert params.yq_version == "4.44.1"

    def test_stores_runner_user(self, build_ami_module):
        params = build_ami_module.ScriptParams("1.2.3.4", "key", "/path/script.sh", "2.0", "4.0", "github-runner")
        assert params.runner_user == "github-runner"
