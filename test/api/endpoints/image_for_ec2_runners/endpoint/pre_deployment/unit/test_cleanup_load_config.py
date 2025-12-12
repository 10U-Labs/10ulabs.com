"""Unit tests for load_config functionality."""


class TestLoadConfigBasic:
    """Tests for load_config basic operations."""

    def test_loads_json_file(self, cleanup, tmp_path):
        """Test that load_config loads a JSON file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        result = cleanup.load_config(config_file)

        assert result == {"key": "value"}

    def test_loads_nested_json(self, cleanup, tmp_path):
        """Test that load_config loads nested JSON structures."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"parent": {"child": "value"}}')

        result = cleanup.load_config(config_file)

        assert result == {"parent": {"child": "value"}}

    def test_loads_json_list(self, cleanup, tmp_path):
        """Test that load_config loads JSON lists."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"items": ["one", "two"]}')

        result = cleanup.load_config(config_file)

        assert result == {"items": ["one", "two"]}

    def test_loads_empty_object(self, cleanup, tmp_path):
        """Test that load_config returns empty dict for empty object."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        result = cleanup.load_config(config_file)

        assert result == {}


class TestLoadConfigTags:
    """Tests for load_config tag loading."""

    def test_loads_tags_dict(self, cleanup, tmp_path):
        """Test that load_config loads tags dictionary."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"tags": {"Purpose": "test"}}')

        result = cleanup.load_config(config_file)

        assert result["tags"] == {"Purpose": "test"}

    def test_loads_multiple_tags(self, cleanup, tmp_path):
        """Test that load_config loads multiple tags."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"tags": {"Purpose": "test", "Environment": "dev"}}')

        result = cleanup.load_config(config_file)

        assert result["tags"]["Purpose"] == "test"

    def test_loads_tag_value_from_multiple_tags(self, cleanup, tmp_path):
        """Test that load_config loads individual tag values from multiple tags."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"tags": {"Purpose": "test", "Environment": "dev"}}')

        result = cleanup.load_config(config_file)

        assert result["tags"]["Environment"] == "dev"
