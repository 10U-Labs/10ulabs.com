"""End-to-end tests for Docker functionality on EC2 runners."""
import pytest


def test_docker_can_run_containers_as_github_runner(ssm_client, e2e_test_instance, run_ssm_command):
    """Test that Docker can run containers as github-runner user."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    cmd = "sudo -u github-runner docker run --rm hello-world"
    output = run_ssm_command(ssm_client, e2e_test_instance, cmd, 10)

    assert output["Status"] == "Success"


def test_docker_buildx_can_build_image_as_github_runner(
    ssm_client, e2e_test_instance, run_ssm_command
):
    """Test that Docker buildx can build images as github-runner user."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    build_command = """
cd /tmp && \
echo 'FROM alpine:latest' > Dockerfile && \
echo 'RUN echo hello' >> Dockerfile && \
sudo -u github-runner docker buildx build -t test-build:latest . && \
rm Dockerfile
"""

    output = run_ssm_command(ssm_client, e2e_test_instance, build_command, 30)

    assert output["Status"] == "Success"
