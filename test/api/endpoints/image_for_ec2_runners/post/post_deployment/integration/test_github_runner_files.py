"""Integration tests for GitHub runner files on EC2 AMI."""
import pytest


RUNNER_DIR = "/home/github-runner/actions-runner"


class TestRunnerDirectoryStructure:
    """Tests for GitHub runner directory structure on EC2 AMI."""

    def test_github_runner_user_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that github-runner user exists on the instance."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "id github-runner")

        assert output["Status"] == "Success"

    def test_runner_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that runner directory exists on the instance."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR} && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_bin_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that bin directory exists in runner directory."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/bin && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_externals_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that externals directory exists in runner directory."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/externals && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"


class TestRunnerScriptsExist:
    """Tests for GitHub runner scripts existence."""

    def test_config_script_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that config.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/config.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_script_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that run.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/run.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_env_script_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that env.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/env.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_helper_template_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that run-helper.sh.template exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -f {RUNNER_DIR}/run-helper.sh.template && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_safe_sleep_script_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that safe_sleep.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/safe_sleep.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_installdependencies_script_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that installdependencies.sh script exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/installdependencies.sh && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"


class TestRunnerBinariesExist:
    """Tests for GitHub runner binaries existence."""

    def test_runner_listener_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that Runner.Listener binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.Listener && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_worker_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that Runner.Worker binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.Worker && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_plugin_host_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that Runner.PluginHost binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/bin/Runner.PluginHost && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_listener_executes(self, ssm_client, test_instance, run_ssm_command):
        """Test that Runner.Listener binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/bin/Runner.Listener --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"


class TestDotNetSharedLibraryDependencies:
    """Tests for .NET shared library dependencies."""

    def test_libcoreclr_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        """Test that libcoreclr.so has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"ldd {RUNNER_DIR}/bin/libcoreclr.so | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcrypto_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        """Test that OpenSSL crypto library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Security.Cryptography.Native.OpenSsl.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcompression_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        """Test that compression library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.IO.Compression.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libglobalization_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Test that globalization library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Globalization.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libnative_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        """Test that native library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"


class TestSystemLibrariesInstalled:
    """Tests for system libraries availability."""

    def test_libicu_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        """Test that libicu is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libicu && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_libssl_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        """Test that libssl is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libssl && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_libkrb5_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        """Test that libkrb5 is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libkrb5 && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_zlib_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        """Test that zlib is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libz && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"


class TestNodeJsExternals:
    """Tests for Node.js externals in runner directory."""

    def test_node20_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that node20 directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/externals/node20 && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node20_binary_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that node20 binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/externals/node20/bin/node && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node20_binary_executes(self, ssm_client, test_instance, run_ssm_command):
        """Test that node20 binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/externals/node20/bin/node --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"

    def test_node24_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that node24 directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/externals/node24 && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node24_binary_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that node24 binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/externals/node24/bin/node && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node24_binary_executes(self, ssm_client, test_instance, run_ssm_command):
        """Test that node24 binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/externals/node24/bin/node --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"


class TestRequiredSystemCommands:
    """Tests for required system commands on the runner."""

    def test_ldd_command_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that ldd command exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "command -v ldd && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert "found" in output["StandardOutputContent"]

    def test_ldconfig_command_exists(self, ssm_client, test_instance, run_ssm_command):
        """Test that ldconfig command exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "(command -v ldconfig || test -x /sbin/ldconfig) && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert "found" in output["StandardOutputContent"]
