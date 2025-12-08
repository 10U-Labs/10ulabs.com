"""Unit tests for parse_tags functionality."""


class TestParseTagsEmptyInput:
    """Tests for parse_tags with empty input."""

    def test_returns_empty_dict_for_none(self, cleanup):
        """Test that parse_tags returns empty dict when input is None."""
        result = cleanup.parse_tags(None)

        assert result == {}

    def test_returns_empty_dict_for_empty_list(self, cleanup):
        """Test that parse_tags returns empty dict when input is empty list."""
        result = cleanup.parse_tags([])

        assert result == {}


class TestParseTagsSingleTag:
    """Tests for parse_tags with single tag."""

    def test_parses_single_tag(self, cleanup):
        """Test that parse_tags parses a single tag."""
        result = cleanup.parse_tags(["Purpose=test"])

        assert result == {"Purpose": "test"}

    def test_parses_tag_with_spaces_in_value(self, cleanup):
        """Test that parse_tags parses tag with spaces in value."""
        result = cleanup.parse_tags(["Purpose=GitHub self-hosted EC2 runner"])

        assert result == {"Purpose": "GitHub self-hosted EC2 runner"}


class TestParseTagsMultipleTags:
    """Tests for parse_tags with multiple tags."""

    def test_parses_multiple_tags(self, cleanup):
        """Test that parse_tags parses multiple tags."""
        result = cleanup.parse_tags(["Purpose=test", "Environment=dev"])

        assert result["Purpose"] == "test"

    def test_parses_multiple_tags_second_value(self, cleanup):
        """Test that parse_tags parses second value from multiple tags."""
        result = cleanup.parse_tags(["Purpose=test", "Environment=dev"])

        assert result["Environment"] == "dev"


class TestParseTagsEdgeCases:
    """Tests for parse_tags edge cases."""

    def test_skips_items_without_equals_sign(self, cleanup):
        """Test that parse_tags skips items without equals sign."""
        result = cleanup.parse_tags(["invalid"])

        assert result == {}

    def test_handles_value_with_equals_sign(self, cleanup):
        """Test that parse_tags handles value with equals sign."""
        result = cleanup.parse_tags(["key=value=with=equals"])

        assert result["key"] == "value=with=equals"

    def test_handles_empty_value(self, cleanup):
        """Test that parse_tags handles empty value."""
        result = cleanup.parse_tags(["key="])

        assert result["key"] == ""
