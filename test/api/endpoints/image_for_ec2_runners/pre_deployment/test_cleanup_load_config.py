class TestLoadConfigBasic:

    def test_loads_yaml_file(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("key: value")

        result = cleanup.load_config(config_file)

        assert result == {"key": "value"}

    def test_loads_nested_yaml(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("parent:\n  child: value")

        result = cleanup.load_config(config_file)

        assert result == {"parent": {"child": "value"}}

    def test_loads_yaml_list(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("items:\n  - one\n  - two")

        result = cleanup.load_config(config_file)

        assert result == {"items": ["one", "two"]}

    def test_loads_empty_file_as_none(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("")

        result = cleanup.load_config(config_file)

        assert result is None


class TestLoadConfigTags:

    def test_loads_tags_dict(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("tags:\n  Purpose: test")

        result = cleanup.load_config(config_file)

        assert result["tags"] == {"Purpose": "test"}

    def test_loads_multiple_tags(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("tags:\n  Purpose: test\n  Environment: dev")

        result = cleanup.load_config(config_file)

        assert result["tags"]["Purpose"] == "test"

    def test_loads_tag_value_from_multiple_tags(self, cleanup, tmp_path):
        config_file = tmp_path / "config.yml"
        config_file.write_text("tags:\n  Purpose: test\n  Environment: dev")

        result = cleanup.load_config(config_file)

        assert result["tags"]["Environment"] == "dev"
