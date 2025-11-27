class TestExtractAmiIdFromDescriptionSuccess:

    def test_extracts_ami_id_from_standard_format(self, cleanup):
        description = "Created by CreateImage(i-1234567890abcdef0) for ami-12345678901234567"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-12345678901234567"

    def test_extracts_short_ami_id(self, cleanup):
        description = "Created by CreateImage(i-abcdef12) for ami-abcd1234"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-abcd1234"


class TestExtractAmiIdFromDescriptionNoMatch:

    def test_returns_none_for_empty_description(self, cleanup):
        result = cleanup.extract_ami_id_from_description("")

        assert result is None

    def test_returns_none_when_no_ami_id_present(self, cleanup):
        result = cleanup.extract_ami_id_from_description("Some random description")

        assert result is None

    def test_returns_none_for_invalid_ami_format(self, cleanup):
        result = cleanup.extract_ami_id_from_description("for ami-INVALID")

        assert result is None


class TestExtractAmiIdFromDescriptionEdgeCases:

    def test_extracts_first_ami_id_when_multiple_present(self, cleanup):
        description = "Created for ami-aaaa1111 and also for ami-bbbb2222"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-aaaa1111"

    def test_handles_long_ami_id(self, cleanup):
        description = "Created for ami-0123456789abcdef0"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-0123456789abcdef0"
