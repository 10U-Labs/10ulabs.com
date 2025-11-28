import os
import subprocess
import boto3
import pytest


TFVARS_PATH = os.path.join(os.path.dirname(__file__), "../../../../src/api/terraform.tfvars")


def _get_tfvar_value(var_name):
    with open(TFVARS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    idx = content.find(f'{var_name}')
    if idx == -1:
        return None
    line = content[idx:content.find('\n', idx)]
    start = line.find('"') + 1
    end = line.find('"', start)
    if 0 < start < end:
        return line[start:end]
    return None


def get_dockerfile_path():
    return os.path.join(os.path.dirname(__file__), "../../../../src/build/image_for_docker_runners/Dockerfile")


def get_docker_image_tag():
    try:
        tag = os.environ["TEST_DOCKER_IMAGE_TAG"]
    except KeyError:
        container_name = _get_tfvar_value("container_name")
        tag = f"{container_name}:test"
    return tag


@pytest.fixture(scope="module")
def dockerfile_path():
    return get_dockerfile_path()


@pytest.fixture(scope="module")
def docker_image_tag():
    return get_docker_image_tag()


@pytest.fixture(scope="module")
def docker_image():
    path = get_dockerfile_path()
    tag = get_docker_image_tag()
    build_context = os.path.dirname(path)

    build_args = [
        "--build-arg", f"NODE_VERSION={os.environ['NODE_VERSION']}",
        "--build-arg", f"RUNNER_ARCH={os.environ['RUNNER_ARCH']}",
        "--build-arg", f"RUNNER_VERSION={os.environ['RUNNER_VERSION']}",
        "--build-arg", f"TERRAFORM_VERSION={os.environ['TERRAFORM_VERSION']}",
        "--build-arg", f"YQ_VERSION={os.environ['YQ_VERSION']}",
    ]

    result = subprocess.run(
        ["docker", "build", "--platform", "linux/arm64"] + build_args + ["-t", tag, "-f", path, build_context],
        check=False,
        capture_output=True,
        text=True,
        errors='replace'
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed: {result.stderr}")

    yield tag

    subprocess.run(["docker", "rmi", "-f", tag], check=False, capture_output=True)


def get_available_ecr_tag(region, repository):
    client = boto3.client("ecr", region_name=region)
    response = client.describe_images(
        repositoryName=repository,
        imageIds=[{"imageTag": "available"}]
    )
    try:
        tags = response["imageDetails"][0]["imageTags"]
    except KeyError:
        tags = []
    tag = None
    index = 0
    while index < len(tags):
        if tags[index] == "available":
            tag = tags[index]
            break
        index = index + 1
    if not tag:
        pytest.fail("Image with tag 'available' not found in ECR")
    return tag


@pytest.fixture(scope="module")
def image_tag(aws_region, ecr_repository):
    return get_available_ecr_tag(aws_region, ecr_repository)


@pytest.fixture(scope="module")
def ecr_image_uri(aws_region, aws_account_id, ecr_repository):
    tag = get_available_ecr_tag(aws_region, ecr_repository)
    return f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/{ecr_repository}:{tag}"


def login_to_ecr(region):
    password_result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", region],
        check=True,
        capture_output=True,
        text=True
    )
    account_result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=True,
        capture_output=True,
        text=True
    )
    account_id = account_result.stdout.strip()
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin",
         f"{account_id}.dkr.ecr.{region}.amazonaws.com"],
        input=password_result.stdout,
        check=True,
        text=True
    )
