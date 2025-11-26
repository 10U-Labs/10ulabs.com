import pytest


RUNNER_DIR = "/home/github-runner/actions-runner"


class TestRunnerDirectoryStructure:

    def test_github_runner_user_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "id github-runner")

        assert output["Status"] == "Success"

    def test_runner_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -d {RUNNER_DIR} && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"

    def test_bin_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -d {RUNNER_DIR}/bin && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"

    def test_externals_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -d {RUNNER_DIR}/externals && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"


class TestRunnerScriptsExist:

    def test_config_script_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/config.sh && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_script_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/run.sh && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_env_script_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/env.sh && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_run_helper_template_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -f {RUNNER_DIR}/run-helper.sh.template && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"

    def test_safe_sleep_script_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/safe_sleep.sh && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_installdependencies_script_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/bin/installdependencies.sh && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"


class TestRunnerBinariesExist:

    def test_runner_listener_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/bin/Runner.Listener && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_worker_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/bin/Runner.Worker && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_runner_plugin_host_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/bin/Runner.PluginHost && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"


class TestRunnerBinariesExecute:

    def test_runner_listener_executes(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"{RUNNER_DIR}/bin/Runner.Listener --version")

        assert output["Status"] == "Success"

    def test_runner_worker_executes(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"{RUNNER_DIR}/bin/Runner.Worker --version")

        assert output["Status"] == "Success"


class TestDotNetSharedLibraryDependencies:

    def test_libcoreclr_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"ldd {RUNNER_DIR}/bin/libcoreclr.so | grep -c 'not found' || echo 0")

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcrypto_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"ldd {RUNNER_DIR}/bin/libSystem.Security.Cryptography.Native.OpenSsl.so | grep -c 'not found' || echo 0")

        assert output["StandardOutputContent"].strip() == "0"

    def test_libcompression_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"ldd {RUNNER_DIR}/bin/libSystem.IO.Compression.Native.so | grep -c 'not found' || echo 0")

        assert output["StandardOutputContent"].strip() == "0"

    def test_libglobalization_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"ldd {RUNNER_DIR}/bin/libSystem.Globalization.Native.so | grep -c 'not found' || echo 0")

        assert output["StandardOutputContent"].strip() == "0"

    def test_libnative_dependencies_resolved(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"ldd {RUNNER_DIR}/bin/libSystem.Native.so | grep -c 'not found' || echo 0")

        assert output["StandardOutputContent"].strip() == "0"


class TestSystemLibrariesInstalled:

    def test_libicu_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "ldconfig -p | grep -q libicu && echo found")

        assert output["StandardOutputContent"].strip() == "found"

    def test_libssl_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "ldconfig -p | grep -q libssl && echo found")

        assert output["StandardOutputContent"].strip() == "found"

    def test_libkrb5_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "ldconfig -p | grep -q libkrb5 && echo found")

        assert output["StandardOutputContent"].strip() == "found"

    def test_zlib_available_via_ldconfig(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "ldconfig -p | grep -q libz && echo found")

        assert output["StandardOutputContent"].strip() == "found"


class TestNodeJsExternals:

    def test_node20_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -d {RUNNER_DIR}/externals/node20 && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node20_binary_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/externals/node20/bin/node && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node20_binary_executes(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"{RUNNER_DIR}/externals/node20/bin/node --version")

        assert output["Status"] == "Success"

    def test_node24_directory_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -d {RUNNER_DIR}/externals/node24 && echo exists")

        assert output["StandardOutputContent"].strip() == "exists"

    def test_node24_binary_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"test -x {RUNNER_DIR}/externals/node24/bin/node && echo executable")

        assert output["StandardOutputContent"].strip() == "executable"

    def test_node24_binary_executes(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, f"{RUNNER_DIR}/externals/node24/bin/node --version")

        assert output["Status"] == "Success"


class TestRequiredSystemCommands:

    def test_ldd_command_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "command -v ldd && echo found")

        assert "found" in output["StandardOutputContent"]

    def test_ldconfig_command_exists(self, ssm_client, test_instance, run_ssm_command):
        if not test_instance:
            pytest.fail("Test instance not created")

        output = run_ssm_command(ssm_client, test_instance, "(command -v ldconfig || test -x /sbin/ldconfig) && echo found")

        assert "found" in output["StandardOutputContent"]
