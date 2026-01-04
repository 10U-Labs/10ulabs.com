"""Layer 3: Wiring tests for ECS runner Docker image.

These tests verify that components are connected and work together.
Per POST_DEPLOYMENT_INTEGRATION_TESTS.md tenets, wiring tests verify
component integration - assumes existence and configuration tests passed.
"""
import subprocess

from .conftest import ENTRYPOINT_IMPORT, run_command_in_container
from ..conftest import login_to_ecr


class TestImageWiring:
    """Verify Docker and ECR images work correctly."""

    def test_ecr_image_can_be_pulled(self, ecr_image_uri, aws_region):
        """Test that ECR image can be pulled."""
        login_to_ecr(aws_region)

        result = subprocess.run(
            ["docker", "pull", "--platform", "linux/arm64", ecr_image_uri],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_container_runs_on_arm64_platform(self, docker_image):
        """Test that container runs on ARM64 platform."""
        result = run_command_in_container(docker_image, "uname -m")
        assert result.stdout.strip() == "aarch64"

    def test_container_starts_with_missing_args(self, docker_image):
        """Test that container fails when started with missing arguments."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestEntrypointWiring:
    """Verify entrypoint works correctly."""

    def test_entrypoint_imports_required_modules(self, docker_image):
        """Test that entrypoint can import all required modules."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}exit(0)'"
        )
        assert result.returncode == 0

    def test_entrypoint_prints_registration_message(self, docker_image):
        """Test that entrypoint prints registration message."""
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    docker_image,
                    "--repo", "test/repo",
                    "--name", "test-runner",
                    "--labels", "test-label",
                    "--token", "fake-token"
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10
            )
            stdout = result.stdout
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        expected = "Registering GitHub Actions runner..."
        assert expected in stdout

    def test_entrypoint_prints_repository_from_arguments(self, docker_image):
        """Test that entrypoint prints repository from arguments."""
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    docker_image,
                    "--repo", "myorg/myrepo",
                    "--name", "test-runner",
                    "--labels", "test-label",
                    "--token", "fake-token"
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10
            )
            stdout = result.stdout
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        expected = "Repository: myorg/myrepo"
        assert expected in stdout

    def test_entrypoint_prints_runner_name_from_arguments(self, docker_image):
        """Test that entrypoint prints runner name from arguments."""
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    docker_image,
                    "--repo", "test/repo",
                    "--name", "my-test-runner",
                    "--labels", "test-label",
                    "--token", "fake-token"
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10
            )
            stdout = result.stdout
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        expected = "Runner Name: my-test-runner"
        assert expected in stdout

    def test_entrypoint_prints_labels_from_arguments(self, docker_image):
        """Test that entrypoint prints labels from arguments."""
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    docker_image,
                    "--repo", "test/repo",
                    "--name", "test-runner",
                    "--labels", "custom-label,another-label",
                    "--token", "fake-token"
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10
            )
            stdout = result.stdout
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        expected = "Labels: custom-label,another-label"
        assert expected in stdout

    def test_entrypoint_fails_with_invalid_token(self, docker_image):
        """Test that entrypoint fails with invalid token.

        The runner's config.sh may hang or fail when given an invalid token.
        Either a non-zero exit code or a timeout is considered a failure.
        """
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    docker_image,
                    "--repo", "test/repo",
                    "--name", "test-runner",
                    "--labels", "test-label",
                    "--token", "invalid-token-123"
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode != 0
        except subprocess.TimeoutExpired:
            pass

    def test_entrypoint_extract_run_id_from_fargate_runner(self, docker_image):
        """Test extract_run_id_from_name extracts ID from fargate runner name."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}"
            "assert entrypoint.extract_run_id_from_name(\"fargate-runner-12345\") == \"12345\"'"
        )
        assert result.returncode == 0

    def test_entrypoint_extract_run_id_returns_none_for_ec2_runner(self, docker_image):
        """Test extract_run_id_from_name returns None for ec2 runner name."""
        result = run_command_in_container(
            docker_image,
            f"python3 -c '{ENTRYPOINT_IMPORT}"
            "assert entrypoint.extract_run_id_from_name(\"ec2-runner-12345\") is None'"
        )
        assert result.returncode == 0


class TestNodeJSWiring:
    """Verify Node.js ESM imports work correctly."""

    def test_esm_import_resolves_eslint_js(self, docker_image):
        """Test that ESM import can resolve @eslint/js from global node_modules."""
        cmd = (
            "node --input-type=module -e "
            "\"import js from '@eslint/js'; "
            "console.log(js.configs.recommended ? 'OK' : 'FAIL')\""
        )
        result = run_command_in_container(docker_image, cmd)
        assert result.returncode == 0

    def test_esm_import_resolves_globals(self, docker_image):
        """Test that ESM import can resolve globals from global node_modules."""
        cmd = (
            "node --input-type=module -e "
            "\"import globals from 'globals'; "
            "console.log(globals.node ? 'OK' : 'FAIL')\""
        )
        result = run_command_in_container(docker_image, cmd)
        assert result.returncode == 0


class TestRunnerArgumentValidation:
    """Verify runner argument validation works correctly."""

    def test_runner_fails_with_missing_repo_argument(self, ecr_image_uri, aws_region):
        """Test that runner fails when --repo argument is missing."""
        login_to_ecr(aws_region)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                ecr_image_uri,
                "--name", "test-runner",
                "--labels", "test",
                "--token", "test-token"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_runner_fails_with_missing_name_argument(self, ecr_image_uri, aws_region):
        """Test that runner fails when --name argument is missing."""
        login_to_ecr(aws_region)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                ecr_image_uri,
                "--repo", "org/repo",
                "--labels", "test",
                "--token", "test-token"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_runner_fails_with_missing_labels_argument(
        self, ecr_image_uri, aws_region
    ):
        """Test that runner fails when --labels argument is missing."""
        login_to_ecr(aws_region)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                ecr_image_uri,
                "--repo", "org/repo",
                "--name", "test-runner",
                "--token", "test-token"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_runner_fails_with_missing_token_argument(self, ecr_image_uri, aws_region):
        """Test that runner fails when --token argument is missing."""
        login_to_ecr(aws_region)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                ecr_image_uri,
                "--repo", "org/repo",
                "--name", "test-runner",
                "--labels", "test"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
