import subprocess
import pytest
import boto3


@pytest.fixture(scope="module")
def image_tag(aws_region, ecr_repository):
    client = boto3.client("ecr", region_name=aws_region)
    response = client.describe_images(
        repositoryName=ecr_repository,
        imageIds=[{"imageTag": "available"}]
    )
    tags = response["imageDetails"][0].get("imageTags", [])
    available_tag = next((tag for tag in tags if tag == "available"), None)
    if not available_tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return available_tag


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository, image_tag):
    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:{image_tag}"


def run_command_in_container(tag, command):
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/bash", tag, "-c", command],
        check=False,
        capture_output=True,
        text=True
    )
    return result


def login_to_ecr(region):
    password_result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True,
        capture_output=True,
        text=True
    )
    ecr_url = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=True,
        capture_output=True,
        text=True
    )
    account_id = ecr_url.stdout.strip()
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin",
         f"{account_id}.dkr.ecr.{region}.amazonaws.com"],
        input=password_result.stdout,
        check=True,
        text=True
    )
