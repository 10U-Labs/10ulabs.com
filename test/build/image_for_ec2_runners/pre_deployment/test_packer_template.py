class TestPackerTemplateBaseDependencies:

    def test_installs_curl(self, packer_template_content):
        assert "curl \\" in packer_template_content

    def test_installs_git(self, packer_template_content):
        assert "git \\" in packer_template_content

    def test_installs_jq(self, packer_template_content):
        assert "jq \\" in packer_template_content

    def test_installs_unzip(self, packer_template_content):
        assert "unzip \\" in packer_template_content

    def test_installs_wget(self, packer_template_content):
        assert "wget" in packer_template_content


class TestPackerTemplatePythonPackages:

    def test_installs_pytest_via_pip(self, packer_template_content):
        assert "python3 -m pip install" in packer_template_content

    def test_pip_uses_break_system_packages_flag(self, packer_template_content):
        assert "--break-system-packages" in packer_template_content

    def test_pytest_installed(self, packer_template_content):
        assert "pytest" in packer_template_content


class TestPackerTemplateYq:

    def test_yq_downloads_from_github(self, packer_template_content):
        assert "github.com/mikefarah/yq" in packer_template_content

    def test_yq_installs(self, packer_template_content):
        assert "yq" in packer_template_content

    def test_yq_uses_architecture_variable(self, packer_template_content):
        assert "yq_linux_${var.os_architecture}" in packer_template_content


class TestPackerTemplateDocker:

    def test_installs_docker_ce(self, packer_template_content):
        assert "docker-ce" in packer_template_content

    def test_installs_docker_cli(self, packer_template_content):
        assert "docker-ce-cli" in packer_template_content

    def test_installs_containerd(self, packer_template_content):
        assert "containerd.io" in packer_template_content

    def test_installs_docker_buildx_plugin(self, packer_template_content):
        assert "docker-buildx-plugin" in packer_template_content

    def test_enables_docker_service(self, packer_template_content):
        assert "systemctl enable docker" in packer_template_content


class TestPackerTemplateGitHubRunner:

    def test_creates_runner_user(self, packer_template_content):
        assert "useradd" in packer_template_content

    def test_runner_user_named_github_runner(self, packer_template_content):
        assert "github-runner" in packer_template_content

    def test_adds_runner_to_docker_group(self, packer_template_content):
        assert "usermod -aG docker github-runner" in packer_template_content

    def test_downloads_actions_runner(self, packer_template_content):
        assert "actions-runner" in packer_template_content

    def test_runs_installdependencies_script(self, packer_template_content):
        assert "installdependencies.sh" in packer_template_content

    def test_installdependencies_uses_absolute_path(self, packer_template_content):
        assert "sudo /home/github-runner/actions-runner/bin/installdependencies.sh" in packer_template_content


class TestPackerTemplateAgents:

    def test_installs_ssm_agent(self, packer_template_content):
        assert "amazon-ssm-agent" in packer_template_content

    def test_enables_ssm_agent_service(self, packer_template_content):
        assert "systemctl enable amazon-ssm-agent" in packer_template_content

    def test_installs_cloudwatch_agent(self, packer_template_content):
        assert "amazon-cloudwatch-agent" in packer_template_content
