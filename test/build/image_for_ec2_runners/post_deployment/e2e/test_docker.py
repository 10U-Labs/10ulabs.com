import pytest


def test_docker_can_run_containers_as_github_runner(ssm_client, e2e_test_instance, run_ssm_command):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, e2e_test_instance, "sudo -u github-runner docker run --rm hello-world", 10)

    assert output["Status"] == "Success"
