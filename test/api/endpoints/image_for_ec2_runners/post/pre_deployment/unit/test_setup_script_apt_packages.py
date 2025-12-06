"""Unit tests for APT package installations in setup script."""
# pylint: disable=missing-function-docstring,missing-class-docstring


class TestSetupScriptDockerPackages:
    def test_script_installs_docker_ce(self, setup_script_content):
        has_package = "docker-ce" in setup_script_content
        assert has_package

    def test_script_installs_docker_ce_cli(self, setup_script_content):
        has_package = "docker-ce-cli" in setup_script_content
        assert has_package

    def test_script_installs_containerd(self, setup_script_content):
        has_package = "containerd.io" in setup_script_content
        assert has_package

    def test_script_installs_docker_buildx_plugin(self, setup_script_content):
        has_package = "docker-buildx-plugin" in setup_script_content
        assert has_package

    def test_script_installs_docker_compose_plugin(self, setup_script_content):
        has_package = "docker-compose-plugin" in setup_script_content
        assert has_package

    def test_script_enables_docker_service(self, setup_script_content):
        has_enable = "systemctl enable docker" in setup_script_content
        assert has_enable


class TestSetupScriptCorePackages:
    def test_script_installs_git(self, setup_script_content):
        has_package = "git" in setup_script_content
        assert has_package

    def test_script_installs_jq(self, setup_script_content):
        has_package = "jq" in setup_script_content
        assert has_package

    def test_script_installs_python3_pip(self, setup_script_content):
        has_package = "python3-pip" in setup_script_content
        assert has_package

    def test_script_installs_unzip(self, setup_script_content):
        has_package = "unzip" in setup_script_content
        assert has_package

    def test_script_installs_wget(self, setup_script_content):
        has_package = "wget" in setup_script_content
        assert has_package
