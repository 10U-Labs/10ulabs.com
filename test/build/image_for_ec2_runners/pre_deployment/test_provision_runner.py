class TestProvisionRunnerBaseDependencies:

    def test_installs_curl(self, provision_script_content):
        assert "curl" in provision_script_content

    def test_installs_git(self, provision_script_content):
        assert "git" in provision_script_content

    def test_installs_jq(self, provision_script_content):
        assert "jq" in provision_script_content

    def test_installs_python3_pip(self, provision_script_content):
        assert "python3-pip" in provision_script_content

    def test_installs_unzip(self, provision_script_content):
        assert "unzip" in provision_script_content

    def test_installs_wget(self, provision_script_content):
        assert "wget" in provision_script_content


class TestProvisionRunnerPython3Pip:

    def test_python3_pip_installed_via_apt(self, provision_script_content):
        apt_install_pos = provision_script_content.find("apt-get install")
        pip_module_pos = provision_script_content.find("python3 -m pip")
        assert apt_install_pos < pip_module_pos

    def test_python3_pip_installed_before_pip_module_used(self, provision_script_content):
        apt_install_pos = provision_script_content.find("python3-pip")
        pip_module_pos = provision_script_content.find("python3 -m pip")
        assert apt_install_pos < pip_module_pos


class TestProvisionRunnerPythonPackages:

    def test_installs_packages_via_pip(self, provision_script_content):
        assert "python3 -m pip install" in provision_script_content

    def test_pip_uses_break_system_packages_flag(self, provision_script_content):
        assert "--break-system-packages" in provision_script_content

    def test_installs_boto3(self, provision_script_content):
        assert "boto3" in provision_script_content

    def test_installs_boto3_stubs_with_ecr(self, provision_script_content):
        assert "boto3-stubs[ecr]" in provision_script_content

    def test_installs_botocore(self, provision_script_content):
        assert "botocore" in provision_script_content

    def test_installs_dnspython(self, provision_script_content):
        assert "dnspython" in provision_script_content

    def test_installs_dockerfile_parse(self, provision_script_content):
        assert "dockerfile-parse" in provision_script_content

    def test_installs_mypy(self, provision_script_content):
        assert "mypy" in provision_script_content

    def test_installs_pylint(self, provision_script_content):
        assert "pylint" in provision_script_content

    def test_installs_pytest(self, provision_script_content):
        assert "pytest" in provision_script_content

    def test_installs_python_hcl2(self, provision_script_content):
        assert "python-hcl2" in provision_script_content

    def test_installs_pyyaml(self, provision_script_content):
        assert "pyyaml" in provision_script_content

    def test_installs_requests(self, provision_script_content):
        assert "requests" in provision_script_content

    def test_installs_types_pyyaml(self, provision_script_content):
        assert "types-PyYAML" in provision_script_content

    def test_installs_types_dockerfile_parse(self, provision_script_content):
        assert "types-dockerfile-parse" in provision_script_content

    def test_installs_types_requests(self, provision_script_content):
        assert "types-requests" in provision_script_content

    def test_installs_yamllint(self, provision_script_content):
        assert "yamllint" in provision_script_content


class TestProvisionRunnerYq:

    def test_yq_downloads_from_github(self, provision_script_content):
        assert "github.com/mikefarah/yq" in provision_script_content

    def test_yq_installs(self, provision_script_content):
        assert "yq" in provision_script_content

    def test_yq_uses_architecture_variable(self, provision_script_content):
        assert "yq_linux_${OS_ARCHITECTURE}" in provision_script_content


class TestProvisionRunnerDocker:

    def test_installs_docker_ce(self, provision_script_content):
        assert "docker-ce" in provision_script_content

    def test_installs_docker_cli(self, provision_script_content):
        assert "docker-ce-cli" in provision_script_content

    def test_installs_containerd(self, provision_script_content):
        assert "containerd.io" in provision_script_content

    def test_installs_docker_buildx_plugin(self, provision_script_content):
        assert "docker-buildx-plugin" in provision_script_content

    def test_enables_docker_service(self, provision_script_content):
        assert "systemctl enable docker" in provision_script_content


class TestProvisionRunnerGitHubRunner:

    def test_creates_runner_user(self, provision_script_content):
        assert "useradd" in provision_script_content

    def test_runner_user_named_github_runner(self, provision_script_content):
        assert "github-runner" in provision_script_content

    def test_adds_runner_to_docker_group(self, provision_script_content):
        assert "usermod -aG docker github-runner" in provision_script_content

    def test_downloads_actions_runner(self, provision_script_content):
        assert "actions-runner" in provision_script_content

    def test_runs_installdependencies_script(self, provision_script_content):
        assert "installdependencies.sh" in provision_script_content

    def test_installdependencies_uses_absolute_path(self, provision_script_content):
        assert "/home/github-runner/actions-runner/bin/installdependencies.sh" in provision_script_content


class TestProvisionRunnerAgents:

    def test_installs_ssm_agent(self, provision_script_content):
        assert "amazon-ssm-agent" in provision_script_content

    def test_enables_ssm_agent_service(self, provision_script_content):
        assert "systemctl enable amazon-ssm-agent" in provision_script_content

    def test_installs_cloudwatch_agent(self, provision_script_content):
        assert "amazon-cloudwatch-agent" in provision_script_content
