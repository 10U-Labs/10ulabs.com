class TestSetupScriptYq:
    def test_script_downloads_yq(self, setup_script_content):
        has_download = "github.com/mikefarah/yq/releases" in setup_script_content
        assert has_download

    def test_script_installs_yq_to_usr_local_bin(self, setup_script_content):
        has_install = "/usr/local/bin/yq" in setup_script_content
        assert has_install

    def test_script_makes_yq_executable(self, setup_script_content):
        has_chmod = "chmod +x /usr/local/bin/yq" in setup_script_content
        assert has_chmod


class TestSetupScriptGitHubRunner:
    def test_script_downloads_actions_runner(self, setup_script_content):
        has_download = "github.com/actions/runner/releases" in setup_script_content
        assert has_download

    def test_script_creates_runner_user(self, setup_script_content):
        has_useradd = "useradd -m -s /bin/bash" in setup_script_content
        assert has_useradd

    def test_script_adds_runner_user_to_docker_group(self, setup_script_content):
        has_usermod = "usermod -aG docker" in setup_script_content
        assert has_usermod

    def test_script_creates_actions_runner_directory(self, setup_script_content):
        has_mkdir = "actions-runner" in setup_script_content
        assert has_mkdir

    def test_script_runs_install_dependencies(self, setup_script_content):
        has_install = "installdependencies.sh" in setup_script_content
        assert has_install


class TestSetupScriptSsmAgent:
    def test_script_downloads_ssm_agent(self, setup_script_content):
        has_download = "amazon-ssm-agent.deb" in setup_script_content
        assert has_download

    def test_script_installs_ssm_agent(self, setup_script_content):
        has_dpkg = "dpkg -i /tmp/amazon-ssm-agent.deb" in setup_script_content
        assert has_dpkg

    def test_script_enables_ssm_agent(self, setup_script_content):
        has_enable = "systemctl enable amazon-ssm-agent" in setup_script_content
        assert has_enable


class TestSetupScriptCloudWatchAgent:
    def test_script_downloads_cloudwatch_agent(self, setup_script_content):
        has_download = "amazon-cloudwatch-agent.deb" in setup_script_content
        assert has_download

    def test_script_installs_cloudwatch_agent(self, setup_script_content):
        has_dpkg = "dpkg -i /tmp/amazon-cloudwatch-agent.deb" in setup_script_content
        assert has_dpkg
