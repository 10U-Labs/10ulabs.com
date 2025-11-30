import pytest


def test_docker_can_run_containers_as_github_runner(ssm_client, e2e_test_instance, run_ssm_command):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, e2e_test_instance, "sudo -u github-runner docker run --rm hello-world", 10)

    assert output["Status"] == "Success"


def test_docker_buildx_can_build_image_as_github_runner(ssm_client, e2e_test_instance, run_ssm_command):
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
