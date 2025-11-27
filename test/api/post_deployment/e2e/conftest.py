import pytest
from botocore.exceptions import ClientError


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(ecr_client):
    try:
        response = ecr_client.describe_images(
            repositoryName='10ulabs',
            filter={'tagStatus': 'TAGGED'}
        )
        stable_images = [
            img for img in response.get('imageDetails', [])
            if 'stable' in img.get('imageTags', [])
        ]
        return len(stable_images)
    except ClientError:
        return 0
