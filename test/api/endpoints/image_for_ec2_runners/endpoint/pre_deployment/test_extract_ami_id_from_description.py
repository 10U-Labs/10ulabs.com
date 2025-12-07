"""Unit tests for extract_ami_id_from_description functionality."""


class TestExtractAmiIdFromDescription:
    """Tests for extract_ami_id_from_description operations."""

    def test_extracts_ami_id_from_standard_description(self, cleanup):
        """Test that AMI ID is extracted from standard description."""
        description = "Created by CreateImage(i-0117e00a226195fac) for ami-0bb67a44482c9198e"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-0bb67a44482c9198e"

    def test_returns_none_for_empty_description(self, cleanup):
        """Test that None is returned for empty description."""
        result = cleanup.extract_ami_id_from_description("")

        assert result is None

    def test_returns_none_when_no_ami_id_found(self, cleanup):
        """Test that None is returned when no AMI ID found."""
        description = "Some random snapshot description"

        result = cleanup.extract_ami_id_from_description(description)

        assert result is None

    def test_extracts_ami_id_with_volume_suffix(self, cleanup):
        """Test that AMI ID is extracted with volume suffix."""
        description = "Created by CreateImage(i-abc123) for ami-def456 from vol-xyz789"

        result = cleanup.extract_ami_id_from_description(description)

        assert result == "ami-def456"

    def test_handles_description_with_only_for_keyword(self, cleanup):
        """Test that description with only 'for' keyword returns None."""
        description = "for something else"

        result = cleanup.extract_ami_id_from_description(description)

        assert result is None
