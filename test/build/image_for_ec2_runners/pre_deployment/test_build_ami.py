from unittest.mock import MagicMock, patch
import pytest


class TestParseValueStrings:

    def test_returns_string_unchanged(self, build_ami_module):
        assert build_ami_module.parse_value("hello") == "hello"

    def test_returns_string_with_spaces_unchanged(self, build_ami_module):
        assert build_ami_module.parse_value("hello world") == "hello world"

    def test_returns_empty_string_unchanged(self, build_ami_module):
        assert build_ami_module.parse_value("") == ""


class TestParseValueJsonArrays:

    def test_parses_json_array_of_strings(self, build_ami_module):
        assert build_ami_module.parse_value('["a", "b", "c"]') == ["a", "b", "c"]

    def test_parses_empty_json_array(self, build_ami_module):
        assert build_ami_module.parse_value('[]') == []

    def test_parses_single_element_json_array(self, build_ami_module):
        assert build_ami_module.parse_value('["subnet-123"]') == ["subnet-123"]


class TestParseValueJsonObjects:

    def test_parses_json_object(self, build_ami_module):
        assert build_ami_module.parse_value('{"key": "value"}') == {"key": "value"}

    def test_parses_empty_json_object(self, build_ami_module):
        assert build_ami_module.parse_value('{}') == {}


class TestParseValueJsonPrimitives:

    def test_parses_json_integer(self, build_ami_module):
        assert build_ami_module.parse_value('42') == 42

    def test_parses_json_boolean_true(self, build_ami_module):
        assert build_ami_module.parse_value('true') is True

    def test_parses_json_boolean_false(self, build_ami_module):
        assert build_ami_module.parse_value('false') is False

    def test_parses_json_null(self, build_ami_module):
        assert build_ami_module.parse_value('null') is None


class TestApplyVarsSimpleKeys:

    def test_sets_simple_string_value(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ["key=value"])
        assert config["key"] == "value"

    def test_overwrites_existing_value(self, build_ami_module):
        config = {"key": "old"}
        build_ami_module.apply_vars(config, ["key=new"])
        assert config["key"] == "new"

    def test_sets_csv_value_as_list(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ["subnet_ids=subnet-a,subnet-b"])
        assert config["subnet_ids"] == ["subnet-a", "subnet-b"]


class TestApplyVarsNestedKeys:

    def test_creates_nested_dict_for_dot_notation(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ["tags.Name=my-ami"])
        assert config["tags"]["Name"] == "my-ami"

    def test_adds_to_existing_nested_dict(self, build_ami_module):
        config = {"tags": {"existing": "value"}}
        build_ami_module.apply_vars(config, ["tags.new=added"])
        assert config["tags"]["new"] == "added"

    def test_preserves_existing_nested_values(self, build_ami_module):
        config = {"tags": {"existing": "value"}}
        build_ami_module.apply_vars(config, ["tags.new=added"])
        assert config["tags"]["existing"] == "value"


class TestApplyVarsEdgeCases:

    def test_handles_none_var_list(self, build_ami_module):
        config = {"key": "value"}
        build_ami_module.apply_vars(config, None)
        assert config["key"] == "value"

    def test_handles_empty_var_list(self, build_ami_module):
        config = {"key": "value"}
        build_ami_module.apply_vars(config, [])
        assert config["key"] == "value"

    def test_skips_items_without_equals_sign(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ["invalid"])
        assert not config

    def test_handles_value_with_equals_sign(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ["key=value=with=equals"])
        assert config["key"] == "value=with=equals"


class TestValidateCommandsMissing:

    def test_returns_empty_list_when_commands_key_missing(self, build_ami_module):
        result = build_ami_module.validate_commands({})
        assert result == []

    def test_returns_empty_list_when_commands_is_none(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": None})
        assert result == []


class TestValidateCommandsValidInput:

    def test_returns_empty_list_for_valid_string(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": "echo hello"})
        assert result == []

    def test_returns_empty_list_for_multiline_string(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": "echo hello\necho world"})
        assert result == []


class TestValidateCommandsInvalidInput:

    def test_returns_error_when_commands_is_list(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": ["echo hello"]})
        assert result == ["commands must be a string (use YAML block scalar |)"]

    def test_returns_error_when_commands_is_int(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": 123})
        assert result == ["commands must be a string (use YAML block scalar |)"]

    def test_returns_error_when_commands_is_dict(self, build_ami_module):
        result = build_ami_module.validate_commands({"commands": {"cmd": "echo"}})
        assert result == ["commands must be a string (use YAML block scalar |)"]


class TestValidateConfigValidInput:

    def test_returns_empty_list_for_valid_config(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == []

    def test_accepts_valid_tags_dict(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "tags": {"Name": "test"},
        }
        result = build_ami_module.validate_config(config)
        assert result == []

    def test_accepts_valid_commands_string(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "commands": "echo hello",
        }
        result = build_ami_module.validate_config(config)
        assert result == []


class TestValidateConfigMissingRequiredFields:

    def test_returns_error_for_missing_ami_name(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["Missing required field: ami_name"]

    def test_returns_error_for_missing_region(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["Missing required field: region"]

    def test_returns_error_for_missing_subnet_ids(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["Missing required field: subnet_ids"]

    def test_returns_error_for_missing_instance_types(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["Missing required field: instance_types"]


class TestValidateConfigSourceAmiLookup:

    def test_valid_with_source_ami(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == []

    def test_returns_error_for_missing_source_ami(self, build_ami_module):
        config = {
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["Missing required field: source_ami"]


class TestValidateConfigInstanceTypes:

    def test_returns_error_when_instance_types_is_string(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": "t3.micro",
        }
        result = build_ami_module.validate_config(config)
        assert result == ["instance_types must be a list"]

    def test_returns_error_when_instance_types_is_empty(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": [],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["instance_types cannot be empty"]


class TestValidateConfigSubnetIds:

    def test_returns_error_when_subnet_ids_is_string(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": "subnet-123",
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["subnet_ids must be a list"]

    def test_returns_error_when_subnet_ids_is_empty(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": [],
            "instance_types": ["t3.micro"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["subnet_ids cannot be empty"]


class TestValidateConfigTags:

    def test_returns_error_when_tags_is_list(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "tags": ["tag1", "tag2"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["tags must be a dict"]

    def test_returns_error_when_tags_is_string(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "tags": "Name=test",
        }
        result = build_ami_module.validate_config(config)
        assert result == ["tags must be a dict"]


class TestValidateConfigCommands:

    def test_returns_error_when_commands_is_list(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "commands": ["echo hello"],
        }
        result = build_ami_module.validate_config(config)
        assert result == ["commands must be a string (use YAML block scalar |)"]

    def test_returns_error_when_commands_is_int(self, build_ami_module):
        config = {
            "source_ami": "ami-123",
            "ami_name": "my-ami",
            "region": "us-east-1",
            "subnet_ids": ["subnet-123"],
            "instance_types": ["t3.micro"],
            "commands": 123,
        }
        result = build_ami_module.validate_config(config)
        assert result == ["commands must be a string (use YAML block scalar |)"]


class TestLoadConfigBasic:

    def test_loads_yaml_file(self, build_ami_module, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("key: value")
        result = build_ami_module.load_config(config_file)
        assert result == {"key": "value"}

    def test_loads_nested_yaml(self, build_ami_module, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("parent:\n  child: value")
        result = build_ami_module.load_config(config_file)
        assert result == {"parent": {"child": "value"}}

    def test_loads_yaml_list(self, build_ami_module, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("items:\n  - one\n  - two")
        result = build_ami_module.load_config(config_file)
        assert result == {"items": ["one", "two"]}

    def test_loads_empty_file_as_none(self, build_ami_module, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("")
        result = build_ami_module.load_config(config_file)
        assert result is None

    def test_loads_multiline_string(self, build_ami_module, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("commands: |\n  echo hello\n  echo world")
        result = build_ami_module.load_config(config_file)
        assert result["commands"] == "echo hello\necho world"


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

    def test_writes_stdout_to_sys_stdout(self, build_ami_module, mock_ssh_client_with_output, capsys):
        build_ami_module.run_ssh_command(mock_ssh_client_with_output, "echo hello")
        captured = capsys.readouterr()
        assert captured.out == "hello world"

    def test_streams_output_from_multiline_script(self, build_ami_module, mock_ssh_client_with_multiline_output, capsys):
        script = "echo line1\necho line2\necho line3"
        build_ami_module.run_ssh_command(mock_ssh_client_with_multiline_output, script)
        captured = capsys.readouterr()
        assert captured.out == "line1\nline2\nline3\n"


class TestWaitForInstanceRunningSuccess:

    def test_returns_when_state_is_running(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")
        assert mock_ec2.describe_instances.call_count == 1

    def test_polls_until_running(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = [
            {"Reservations": [{"Instances": [{"State": {"Name": "pending"}}]}]},
            {"Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]},
        ]
        with patch.object(build_ami_module.time, 'sleep'):
            build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")
        assert mock_ec2.describe_instances.call_count == 2

    def test_queries_correct_instance_id(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]
        }
        build_ami_module.wait_for_instance_running(mock_ec2, "i-test456")
        assert mock_ec2.describe_instances.call_args[1]["InstanceIds"] == ["i-test456"]


class TestWaitForInstanceRunningFailure:

    def test_raises_after_max_attempts(self, build_ami_module, raise_runtime_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "pending"}}]}]
        }
        with patch.object(build_ami_module.time, 'sleep'):
            with raise_runtime_error:
                build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")

    def test_raises_when_stuck_in_stopped_state(self, build_ami_module, raise_runtime_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "stopped"}}]}]
        }
        with patch.object(build_ami_module.time, 'sleep'):
            with raise_runtime_error:
                build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")


class TestWaitForInstanceRunningEventualConsistency:

    def test_retries_when_instance_not_found(self, build_ami_module, instance_not_found_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = [
            instance_not_found_error,
            {"Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]},
        ]
        with patch.object(build_ami_module.time, 'sleep'):
            build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")
        assert mock_ec2.describe_instances.call_count == 2

    def test_succeeds_after_multiple_not_found_errors(self, build_ami_module, instance_not_found_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = [
            instance_not_found_error,
            instance_not_found_error,
            instance_not_found_error,
            {"Reservations": [{"Instances": [{"State": {"Name": "running"}}]}]},
        ]
        with patch.object(build_ami_module.time, 'sleep'):
            build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")
        assert mock_ec2.describe_instances.call_count == 4

    def test_reraises_other_client_errors(self, build_ami_module, access_denied_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = access_denied_error
        with patch.object(build_ami_module.time, 'sleep'):
            with pytest.raises(build_ami_module.ClientError):
                build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")

    def test_raises_after_max_not_found_attempts(self, build_ami_module, instance_not_found_error, raise_runtime_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = instance_not_found_error
        with patch.object(build_ami_module.time, 'sleep'):
            with raise_runtime_error:
                build_ami_module.wait_for_instance_running(mock_ec2, "i-12345")


class TestWaitForStatusChecksSuccess:

    def test_returns_when_both_statuses_ok(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [{
                "InstanceStatus": {"Status": "ok"},
                "SystemStatus": {"Status": "ok"}
            }]
        }
        build_ami_module.wait_for_status_checks(mock_ec2, "i-12345")
        assert mock_ec2.describe_instance_status.call_count == 1

    def test_polls_until_status_ok(self, build_ami_module):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_status.side_effect = [
            {"InstanceStatuses": [{"InstanceStatus": {"Status": "initializing"}, "SystemStatus": {"Status": "initializing"}}]},
            {"InstanceStatuses": [{"InstanceStatus": {"Status": "ok"}, "SystemStatus": {"Status": "ok"}}]},
        ]
        with patch.object(build_ami_module.time, 'sleep'):
            build_ami_module.wait_for_status_checks(mock_ec2, "i-12345")
        assert mock_ec2.describe_instance_status.call_count == 2


class TestWaitForStatusChecksFailure:

    def test_raises_after_max_attempts(self, build_ami_module, raise_runtime_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [{
                "InstanceStatus": {"Status": "initializing"},
                "SystemStatus": {"Status": "initializing"}
            }]
        }
        with patch.object(build_ami_module.time, 'sleep'):
            with raise_runtime_error:
                build_ami_module.wait_for_status_checks(mock_ec2, "i-12345")

    def test_raises_when_instance_status_impaired(self, build_ami_module, raise_runtime_error):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [{
                "InstanceStatus": {"Status": "impaired"},
                "SystemStatus": {"Status": "ok"}
            }]
        }
        with patch.object(build_ami_module.time, 'sleep'):
            with raise_runtime_error:
                build_ami_module.wait_for_status_checks(mock_ec2, "i-12345")


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


class TestRunCommandsHeredoc:

    def test_creates_heredoc_with_sudo_bash(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command') as mock_run:
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "echo hello")
                    build_ami_module.run_commands(params)
                    call_args = mock_run.call_args[0][1]
                    assert call_args.startswith("sudo bash -ex << 'EOFSCRIPT'\nPS4=''\nexport DEBIAN_FRONTEND=noninteractive")

    def test_heredoc_ends_with_eofscript(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command') as mock_run:
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "echo hello")
                    build_ami_module.run_commands(params)
                    call_args = mock_run.call_args[0][1]
                    assert call_args.endswith("EOFSCRIPT")

    def test_heredoc_contains_command(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command') as mock_run:
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "apt-get update")
                    build_ami_module.run_commands(params)
                    call_args = mock_run.call_args[0][1]
                    assert "apt-get update" in call_args

    def test_heredoc_contains_variable_definitions(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command') as mock_run:
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "MY_VAR=hello\necho $MY_VAR")
                    build_ami_module.run_commands(params)
                    call_args = mock_run.call_args[0][1]
                    assert "MY_VAR=hello" in call_args


class TestRunCommandsConnection:

    def test_connects_to_correct_ip(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.CommandParams("192.168.1.100", "key", "echo hi")
                    build_ami_module.run_commands(params)
                    assert mock_client.connect.call_args[0][0] == "192.168.1.100"

    def test_connects_with_admin_username(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "echo hi")
                    build_ami_module.run_commands(params)
                    assert mock_client.connect.call_args[1]["username"] == "admin"

    def test_closes_client_after_completion(self, build_ami_module):
        with patch.object(build_ami_module.paramiko.Ed25519Key, 'from_private_key'):
            mock_client = MagicMock()
            with patch.object(build_ami_module.paramiko, 'SSHClient', return_value=mock_client):
                with patch.object(build_ami_module, 'run_ssh_command'):
                    params = build_ami_module.CommandParams("1.2.3.4", "key", "echo hi")
                    build_ami_module.run_commands(params)
                    assert mock_client.close.called
