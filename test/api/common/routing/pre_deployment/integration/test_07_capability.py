import uuid
from typing import Any

import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    Layer6S3WriteCapabilityTests,
    check_state_file_readable,
)


class TestIAMCapabilities(Layer6IAMCapabilityTests):
    pass
class TestS3StateCapabilities(Layer6S3CapabilityTests, Layer6S3WriteCapabilityTests):
    def test_can_read_state_file(self, s3_client: Any, state_bucket_name: str) -> None:
        check_state_file_readable(s3_client, state_bucket_name, "api/terraform.tfstate")
        assert True


class TestCentralLogsBucketCapabilities:
    def test_can_write_to_central_logs_bucket(
        self,
        s3_client: Any,
        central_logs_bucket_name: str
    ) -> None:
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        test_key = f"pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=central_logs_bucket_name,
                Key=test_key,
                Body=b"test-write"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to write to '{central_logs_bucket_name}'. "
                    "Firehose delivery will fail without write access. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
            except ClientError:
                pass
        assert True

    def test_can_delete_from_central_logs_bucket(
        self, s3_client: Any, central_logs_bucket_name: str
    ) -> None:
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        test_key = f"pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=central_logs_bucket_name,
                Key=test_key,
                Body=b"test-delete"
            )
            s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to delete from '{central_logs_bucket_name}'. "
                    "Check IAM permissions for s3:DeleteObject."
                )
            raise
        finally:
            s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
        assert True
