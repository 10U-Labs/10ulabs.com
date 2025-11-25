import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'scripts' / 'cleanup_packer_artifacts'))

from cleanup_packer_artifacts import extract_ami_id_from_description


class TestExtractAmiIdFromDescription:

    def test_extracts_ami_id_from_standard_description(self):
        description = "Created by CreateImage(i-0117e00a226195fac) for ami-0bb67a44482c9198e"

        result = extract_ami_id_from_description(description)

        assert result == "ami-0bb67a44482c9198e"

    def test_returns_none_for_empty_description(self):
        result = extract_ami_id_from_description("")

        assert result is None

    def test_returns_none_when_no_ami_id_found(self):
        description = "Some random snapshot description"

        result = extract_ami_id_from_description(description)

        assert result is None

    def test_extracts_ami_id_with_volume_suffix(self):
        description = "Created by CreateImage(i-abc123) for ami-def456 from vol-xyz789"

        result = extract_ami_id_from_description(description)

        assert result == "ami-def456"

    def test_handles_description_with_only_for_keyword(self):
        description = "for something else"

        result = extract_ami_id_from_description(description)

        assert result is None
