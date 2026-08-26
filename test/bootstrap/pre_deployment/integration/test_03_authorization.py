import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import create_layer2_s3_authorization_tests


TestS3Authorization = create_layer2_s3_authorization_tests()


def test_can_call_s3_get_object(s3_client, state_bucket_name):
    try:
        s3_client.get_object(Bucket=state_bucket_name, Key="bootstrap/terraform.tfstate")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:GetObject on '{state_bucket_name}'")
        if error_code not in ("NoSuchKey", "NoSuchBucket", "404"):
            raise
    assert True
