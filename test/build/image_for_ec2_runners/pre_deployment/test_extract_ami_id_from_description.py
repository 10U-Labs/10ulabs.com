class TestExtractAmiIdFromDescription:

    def test_extracts_ami_id_from_standard_description(self, cleanup_packer_artifacts):
        description = "Created by CreateImage(i-0117e00a226195fac) for ami-0bb67a44482c9198e"

        result = cleanup_packer_artifacts.extract_ami_id_from_description(description)

        assert result == "ami-0bb67a44482c9198e"

    def test_returns_none_for_empty_description(self, cleanup_packer_artifacts):
        result = cleanup_packer_artifacts.extract_ami_id_from_description("")

        assert result is None

    def test_returns_none_when_no_ami_id_found(self, cleanup_packer_artifacts):
        description = "Some random snapshot description"

        result = cleanup_packer_artifacts.extract_ami_id_from_description(description)

        assert result is None

    def test_extracts_ami_id_with_volume_suffix(self, cleanup_packer_artifacts):
        description = "Created by CreateImage(i-abc123) for ami-def456 from vol-xyz789"

        result = cleanup_packer_artifacts.extract_ami_id_from_description(description)

        assert result == "ami-def456"

    def test_handles_description_with_only_for_keyword(self, cleanup_packer_artifacts):
        description = "for something else"

        result = cleanup_packer_artifacts.extract_ami_id_from_description(description)

        assert result is None
