"""Layer 3: Wiring tests.

These tests verify that all components are connected properly.
Assumes existence (Layer 1) and configuration (Layer 2) have passed.
"""
import pytest


RUNNER_DIR = "/home/github-runner/actions-runner"


class TestDockerWiring:
    """Tests for Docker wiring."""

    def test_docker_daemon_is_running(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify Docker daemon is running."""
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "docker info")

        assert output["Status"] == "Success"

    def test_github_runner_user_in_docker_group(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify github-runner user is in docker group."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "groups github-runner | grep -q docker && echo in_group"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "in_group"


class TestSsmAgentWiring:
    """Tests for SSM agent wiring."""

    def test_ssm_agent_service_is_running(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify SSM agent service is running."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "systemctl is-active amazon-ssm-agent"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "active"


class TestDotNetDependenciesResolved:
    """Tests for .NET shared library dependencies."""

    def test_libcoreclr_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify libcoreclr.so has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"ldd {RUNNER_DIR}/bin/libcoreclr.so | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcrypto_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify OpenSSL crypto library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Security.Cryptography.Native.OpenSsl.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcompression_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify compression library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.IO.Compression.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libglobalization_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify globalization library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Globalization.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"

    def test_libnative_dependencies_resolved(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify native library has all dependencies resolved."""
        if not test_instance:
            pytest.fail("Test instance not created")

        lib = "libSystem.Native.so"
        cmd = f"ldd {RUNNER_DIR}/bin/{lib} | grep 'not found' | wc -l"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "0"


class TestSystemLibrariesAvailable:
    """Tests for system libraries availability."""

    def test_libicu_available_via_ldconfig(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify libicu is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libicu && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_libssl_available_via_ldconfig(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify libssl is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libssl && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_libkrb5_available_via_ldconfig(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify libkrb5 is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libkrb5 && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"

    def test_zlib_available_via_ldconfig(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify zlib is available via ldconfig."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "ldconfig -p | grep -q libz && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "found"


class TestNodeJsExternals:
    """Tests for Node.js externals wiring in runner directory."""

    def test_node20_directory_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node20 directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/externals/node20 && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node20_binary_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node20 binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/externals/node20/bin/node && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node20_binary_executes(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node20 binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/externals/node20/bin/node --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"

    def test_node24_directory_exists(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node24 directory exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -d {RUNNER_DIR}/externals/node24 && echo exists"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node24_binary_exists_and_executable(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node24 binary exists and is executable."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"test -x {RUNNER_DIR}/externals/node24/bin/node && echo executable"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node24_binary_executes(
        self, ssm_client, test_instance, run_ssm_command
    ):
        """Verify node24 binary can execute."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = f"{RUNNER_DIR}/externals/node24/bin/node --version"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert output["Status"] == "Success"


class TestRequiredSystemCommands:
    """Tests for required system commands on the runner."""

    def test_ldd_command_exists(self, ssm_client, test_instance, run_ssm_command):
        """Verify ldd command exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "command -v ldd && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert "found" in output["StandardOutputContent"]

    def test_ldconfig_command_exists(self, ssm_client, test_instance, run_ssm_command):
        """Verify ldconfig command exists."""
        if not test_instance:
            pytest.fail("Test instance not created")

        cmd = "(command -v ldconfig || test -x /sbin/ldconfig) && echo found"
        output = run_ssm_command(ssm_client, test_instance, cmd)

        assert "found" in output["StandardOutputContent"]
