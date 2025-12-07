"""Unit tests for setup script syntax validation."""
import subprocess


class TestSetupScriptSyntaxAndStructure:
    """Tests for setup script syntax and structure."""

    def test_script_has_bash_shebang(self, setup_script_content):
        """Script has bash shebang."""
        first_line = setup_script_content.split("\n")[0]
        assert first_line == "#!/bin/bash"

    def test_script_has_valid_bash_syntax(self, setup_script_path):
        """Script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(setup_script_path)],
            capture_output=True,
            check=False,
            text=True
        )
        assert result.returncode == 0

    def test_script_uses_set_euo_pipefail(self, setup_script_content):
        """Script uses set euo pipefail."""
        has_strict_mode = "set -euo pipefail" in setup_script_content
        assert has_strict_mode
