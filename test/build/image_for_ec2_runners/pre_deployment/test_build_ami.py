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

    def test_sets_json_array_value(self, build_ami_module):
        config = {}
        build_ami_module.apply_vars(config, ['subnet_ids=["subnet-a", "subnet-b"]'])
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


class TestParseCommandsBasic:

    def test_parses_single_command(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello")
        assert result == ["echo hello"]

    def test_parses_multiple_commands(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello\necho world")
        assert result == ["echo hello", "echo world"]

    def test_returns_empty_list_for_empty_string(self, build_ami_module):
        result = build_ami_module.parse_commands("")
        assert result == []


class TestParseCommandsWhitespace:

    def test_strips_leading_whitespace(self, build_ami_module):
        result = build_ami_module.parse_commands("  echo hello")
        assert result == ["echo hello"]

    def test_strips_trailing_whitespace(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello  ")
        assert result == ["echo hello"]

    def test_strips_whitespace_from_all_lines(self, build_ami_module):
        result = build_ami_module.parse_commands("  echo hello  \n  echo world  ")
        assert result == ["echo hello", "echo world"]

    def test_skips_empty_lines(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello\n\necho world")
        assert result == ["echo hello", "echo world"]

    def test_skips_whitespace_only_lines(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello\n   \necho world")
        assert result == ["echo hello", "echo world"]


class TestParseCommandsComments:

    def test_skips_comment_lines(self, build_ami_module):
        result = build_ami_module.parse_commands("# this is a comment\necho hello")
        assert result == ["echo hello"]

    def test_skips_multiple_comment_lines(self, build_ami_module):
        result = build_ami_module.parse_commands("# comment 1\n# comment 2\necho hello")
        assert result == ["echo hello"]

    def test_skips_comment_with_leading_whitespace(self, build_ami_module):
        result = build_ami_module.parse_commands("  # indented comment\necho hello")
        assert result == ["echo hello"]

    def test_keeps_commands_with_hash_in_middle(self, build_ami_module):
        result = build_ami_module.parse_commands("echo hello # not a comment")
        assert result == ["echo hello # not a comment"]


class TestLookupSourceAmiFound:

    def test_returns_ami_id_when_found(self, build_ami_module):
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": [{"ImageId": "ami-12345678"}]}
        result = build_ami_module.lookup_source_ami(mock_ec2, "debian-13-arm64-20251117-2299")
        assert result == "ami-12345678"


class TestLookupSourceAmiNotFound:

    def test_raises_error_when_not_found(self, build_ami_module):
        import pytest
        mock_ec2 = type("MockEC2", (), {})()
        mock_ec2.describe_images = lambda **kwargs: {"Images": []}
        with pytest.raises(RuntimeError):
            build_ami_module.lookup_source_ami(mock_ec2, "nonexistent-ami")
