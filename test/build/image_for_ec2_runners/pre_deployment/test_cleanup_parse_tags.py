class TestParseTagsEmptyInput:

    def test_returns_empty_dict_for_none(self, cleanup):
        result = cleanup.parse_tags(None)

        assert result == {}

    def test_returns_empty_dict_for_empty_list(self, cleanup):
        result = cleanup.parse_tags([])

        assert result == {}


class TestParseTagsSingleTag:

    def test_parses_single_tag(self, cleanup):
        result = cleanup.parse_tags(["Purpose=test"])

        assert result == {"Purpose": "test"}

    def test_parses_tag_with_spaces_in_value(self, cleanup):
        result = cleanup.parse_tags(["Purpose=GitHub self-hosted EC2 runner"])

        assert result == {"Purpose": "GitHub self-hosted EC2 runner"}


class TestParseTagsMultipleTags:

    def test_parses_multiple_tags(self, cleanup):
        result = cleanup.parse_tags(["Purpose=test", "Environment=dev"])

        assert result["Purpose"] == "test"

    def test_parses_multiple_tags_second_value(self, cleanup):
        result = cleanup.parse_tags(["Purpose=test", "Environment=dev"])

        assert result["Environment"] == "dev"


class TestParseTagsEdgeCases:

    def test_skips_items_without_equals_sign(self, cleanup):
        result = cleanup.parse_tags(["invalid"])

        assert result == {}

    def test_handles_value_with_equals_sign(self, cleanup):
        result = cleanup.parse_tags(["key=value=with=equals"])

        assert result["key"] == "value=with=equals"

    def test_handles_empty_value(self, cleanup):
        result = cleanup.parse_tags(["key="])

        assert result["key"] == ""
