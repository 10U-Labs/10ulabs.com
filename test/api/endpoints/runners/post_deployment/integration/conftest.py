"""Pytest fixtures for runners post-deployment integration tests."""
import zipfile
from io import BytesIO
from urllib.request import urlopen

import boto3
import pytest


@pytest.fixture(name="sqs_client", scope="session")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="layer_contents", scope="module")
def layer_contents_fixture(config):
    """Download and extract layer contents for inspection."""
    lambda_client = boto3.client("lambda", region_name=config["aws_region"])

    # Get latest layer version
    response = lambda_client.list_layer_versions(
        LayerName="TenULabsRunnersLayer",
        MaxItems=1
    )
    layer_arn = response["LayerVersions"][0]["LayerVersionArn"]

    # Get layer download URL
    layer_response = lambda_client.get_layer_version_by_arn(Arn=layer_arn)
    download_url = layer_response["Content"]["Location"]

    # Download and extract file list
    with urlopen(download_url) as response:
        zip_bytes = BytesIO(response.read())
        with zipfile.ZipFile(zip_bytes, 'r') as zip_file:
            return zip_file.namelist()
