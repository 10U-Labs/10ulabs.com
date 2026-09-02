from typing import Any, Dict

import pytest
from botocore.exceptions import ClientError


class TestCloudFrontConfiguration:
    def test_cloudfront_distribution_is_deployed(
        self, cloudfront_distribution: Any, www_common_outputs: Dict[str, str]
    ) -> None:
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        if cloudfront_distribution is None:
            pytest.skip("Distribution does not exist")
        status = cloudfront_distribution["Status"]
        is_deployed = status == "Deployed"
        assert is_deployed, (
            f"CloudFront distribution '{distribution_id}' is not deployed "
            f"(status: {status}). Wait for distribution to finish deploying."
        )

    def test_cloudfront_distribution_is_enabled(
        self, cloudfront_distribution: Any, www_common_outputs: Dict[str, str]
    ) -> None:
        distribution_id = www_common_outputs.get("cloudfront_distribution_id")
        if not distribution_id:
            pytest.skip("cloudfront_distribution_id output not available")
        if cloudfront_distribution is None:
            pytest.skip("Distribution does not exist")
        is_enabled = (
            cloudfront_distribution["DistributionConfig"]["Enabled"] is True
        )
        assert is_enabled, (
            f"CloudFront distribution '{distribution_id}' is disabled. "
            "Enable the distribution in AWS Console or via Terraform."
        )


class TestS3BucketConfiguration:
    def test_s3_bucket_location_is_retrievable(
        self,
        s3_client: Any,
        www_common_outputs: Dict[str, str]
    ) -> None:
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            response = s3_client.get_bucket_location(Bucket=bucket_name)
            location_retrieved = "LocationConstraint" in response
            assert location_retrieved, "Should be able to retrieve bucket location"
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                pytest.skip("Bucket does not exist")
            raise

    def test_s3_bucket_accepts_list_operations(
        self,
        s3_client: Any,
        www_common_outputs: Dict[str, str]
    ) -> None:
        bucket_name = www_common_outputs.get("bucket_name")
        if not bucket_name:
            pytest.skip("bucket_name output not available")
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            can_list = "KeyCount" in response
            assert can_list, "Should be able to list bucket objects"
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                pytest.skip("Bucket does not exist")
            raise
