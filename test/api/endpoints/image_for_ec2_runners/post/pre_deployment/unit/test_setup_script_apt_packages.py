"""Unit tests for APT package installations in setup script."""


class TestSetupScriptDockerPackages:
    """Tests for setup script docker packages."""

    def test_script_installs_docker_ce(self, setup_script_content):
        """Script installs docker ce."""
        has_package = "docker-ce" in setup_script_content
        assert has_package

    def test_script_installs_docker_ce_cli(self, setup_script_content):
        """Script installs docker ce cli."""
        has_package = "docker-ce-cli" in setup_script_content
        assert has_package

    def test_script_installs_containerd(self, setup_script_content):
        """Script installs containerd."""
        has_package = "containerd.io" in setup_script_content
        assert has_package

    def test_script_installs_docker_buildx_plugin(self, setup_script_content):
        """Script installs docker buildx plugin."""
        has_package = "docker-buildx-plugin" in setup_script_content
        assert has_package

    def test_script_installs_docker_compose_plugin(self, setup_script_content):
        """Script installs docker compose plugin."""
        has_package = "docker-compose-plugin" in setup_script_content
        assert has_package

    def test_script_enables_docker_service(self, setup_script_content):
        """Script enables docker service."""
        has_enable = "systemctl enable docker" in setup_script_content
        assert has_enable


class TestSetupScriptCorePackages:
    """Tests for setup script core packages."""

    def test_script_installs_git(self, setup_script_content):
        """Script installs git."""
        has_package = "git" in setup_script_content
        assert has_package

    def test_script_installs_jq(self, setup_script_content):
        """Script installs jq."""
        has_package = "jq" in setup_script_content
        assert has_package

    def test_script_installs_python3_pip(self, setup_script_content):
        """Script installs python3 pip."""
        has_package = "python3-pip" in setup_script_content
        assert has_package

    def test_script_installs_unzip(self, setup_script_content):
        """Script installs unzip."""
        has_package = "unzip" in setup_script_content
        assert has_package

    def test_script_installs_wget(self, setup_script_content):
        """Script installs wget."""
        has_package = "wget" in setup_script_content
        assert has_package
